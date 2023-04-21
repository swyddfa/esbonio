set expandtab
set tabstop=3
set softtabstop=3
set shiftwidth=3

let mapleader='<space>'

lua << EOF
local lspconfig = require('lspconfig')

local keymap_opts = { noremap = true, silent = true}
vim.keymap.set('n', '<space>e', vim.diagnostic.open_float, keymap_opts)
vim.keymap.set('n', '[d', vim.diagnostic.goto_prev, keymap_opts)
vim.keymap.set('n', ']d', vim.diagnostic.goto_next, keymap_opts)
vim.keymap.set('n', '<space>q', vim.diagnostic.setloclist, keymap_opts)

local on_attach = function(client, bufnr)
end

lspconfig.esbonio.setup {
  cmd = { 'esbonio' },
  init_options = {
    server = {
      completion = {
        preferredInsertBehavior = 'insert'
      }
    }
  },
  on_attach = function(client, bufnr)
    vim.api.nvim_buf_set_option(bufnr, 'omnifunc', 'v:lua.vim.lsp.omnifunc')

    local bufopts = { noremap=true, silent=true, buffer=bufnr }
    vim.keymap.set('n', 'gd', vim.lsp.buf.definition, bufopts)
    vim.keymap.set('n', 'gi', vim.lsp.buf.implementation, bufopts)
    vim.keymap.set('n', 'gh', vim.lsp.buf.hover, bufopts)
    vim.keymap.set('n', '<leader>ca', vim.lsp.buf.code_action, bufopts)

  end
}
EOF
