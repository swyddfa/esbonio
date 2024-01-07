" vim: et ts=2 sw=2
set expandtab
set tabstop=3
set softtabstop=3
set shiftwidth=3

let mapleader=' '

colorscheme everforest
lua << EOF
local lspconfig = require('lspconfig')
local util = require('lspconfig.util')

local LSP_DEVTOOLS_PORT = '91234'

-- The helm/vertico/etc of the nvim world
local telescope = require('telescope.builtin')
local keymap_opts = { noremap = true, silent = true}
vim.keymap.set('n', '<leader>ff', telescope.find_files, {})
vim.keymap.set('n', '<leader>fg', telescope.live_grep, {})
vim.keymap.set('n', '<leader>fb', telescope.buffers, {})
vim.keymap.set('n', '<leader>fh', telescope.help_tags, {})

vim.keymap.set('n', '<leader>ds', telescope.lsp_document_symbols, keymap_opts)
vim.keymap.set('n', '<leader>ws', telescope.lsp_workspace_symbols, keymap_opts)
vim.keymap.set('n', '<leader>e', vim.diagnostic.open_float, keymap_opts)
vim.keymap.set('n', '[d', vim.diagnostic.goto_prev, keymap_opts)
vim.keymap.set('n', ']d', vim.diagnostic.goto_next, keymap_opts)
vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist, keymap_opts)

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
  -- Wrap server with the lsp-devtools agent so that we can create out own
  -- VSCode style output window.
  cmd = { 'lsp-devtools', 'agent', '--port', LSP_DEVTOOLS_PORT, '--', 'esbonio' },
  init_options = {
    server = {
      logLevel = 'debug',
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

-- UI for $/progress and other notifications
require('fidget').setup {
  notification = {
    override_vim_notify = true,
  }
}

-- smooth scrolling
require('neoscroll').setup {}

-- statusline
require('lualine').setup { theme = "everforest" }

-- VSCode-style output window
local Terminal  = require('toggleterm.terminal').Terminal
local log_output = Terminal:new({
  cmd = "lsp-devtools record --port " .. LSP_DEVTOOLS_PORT .. " -f '{.params.message}'",
  hidden = false,
  direction = 'horizontal',
  auto_scroll = true,
})
-- Ensure that the terminal is launched, so that it can connect to the server.
log_output:spawn()

function _log_output_toggle()
  log_output:toggle()
end

vim.api.nvim_set_keymap("n", "<leader>wl", "<cmd>lua _log_output_toggle()<CR>", keymap_opts)

EOF
