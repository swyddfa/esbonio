" vim: et ts=2 sw=2
set expandtab
set tabstop=3
set softtabstop=3
set shiftwidth=3

let mapleader='<space>'

lua << EOF
local lspconfig = require('lspconfig')
local util = require('lspconfig.util')

local keymap_opts = { noremap = true, silent = true}
vim.keymap.set('n', '<space>e', vim.diagnostic.open_float, keymap_opts)
vim.keymap.set('n', '[d', vim.diagnostic.goto_prev, keymap_opts)
vim.keymap.set('n', ']d', vim.diagnostic.goto_next, keymap_opts)
vim.keymap.set('n', '<space>q', vim.diagnostic.setloclist, keymap_opts)

vim.lsp.set_log_level("info")

local function scroll_view(ev)
  local esbonio = vim.lsp.get_active_clients({bufnr = 0, name = "esbonio"})[1]
  local view = vim.fn.winsaveview()

  local params = { line = view.topline }
  esbonio.notify("view/scroll", params)
end

local function preview_file()
  local params = {
    command = "esbonio.server.previewFile",
    arguments = {
      { uri = vim.uri_from_bufnr(0), show = false },
    }
  }
  local result = vim.lsp.buf.execute_command(params)
  print(vim.inspect(result))

  -- Setup sync scrolling
  local augroup = vim.api.nvim_create_augroup("EsbonioSyncScroll", { clear = true })
  vim.api.nvim_create_autocmd({"WinScrolled"}, {
    callback = scroll_view,
    group = augroup,
    buffer = 0,
  })
end

-- Attempt to find a virtualenv that the server can use to build the docs.

local function find_venv()
  
  -- If there is an active virtual env, use that
  if vim.env.VIRTUAL_ENV then
    return { vim.env.VIRTUAL_ENV .. "/bin/python" }
  end

  -- Search within the current git repo to see if we can find a virtual env to use.
  local repo = util.find_git_ancestor(vim.fn.getcwd())
  if not repo then
    return nil
  end

  local candidates = vim.fs.find("pyvenv.cfg", { path = repo })
  if #candidates == 0 then
    return nil
  end

  return { vim.fn.resolve(candidates[1] .. "./../bin/python") }
end

lspconfig.esbonio.setup {
  cmd = { 'esbonio' },
  init_options = {
    server = {
      logLevel = 'debug',
      completion = {
        preferredInsertBehavior = 'insert'
      }
    }
  },
  settings = {
    esbonio = {
      sphinx = {
        pythonCommand = find_venv(),
      }
    }
  },
  handlers = {
    ["editor/scroll"] = function(err, result, ctx, config)
      vim.cmd('normal '.. result.line .. 'Gzt')
    end
  },
  on_attach = function(client, bufnr)
    vim.api.nvim_buf_set_option(bufnr, 'omnifunc', 'v:lua.vim.lsp.omnifunc')

    local bufopts = { noremap=true, silent=true, buffer=bufnr }
    vim.keymap.set('n', 'gd', vim.lsp.buf.definition, bufopts)
    vim.keymap.set('n', 'gi', vim.lsp.buf.implementation, bufopts)
    vim.keymap.set('n', 'gh', vim.lsp.buf.hover, bufopts)
    vim.keymap.set('n', '<leader>ca', vim.lsp.buf.code_action, bufopts)

    vim.api.nvim_create_user_command("EsbonioPreviewFile", preview_file, { desc = "Preview file" })
  end
}
EOF
