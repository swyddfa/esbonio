"  --------------- First time setup ------------------
"  There are a few steps you need to perform when setting this up for the
"  first time.
"
"  1. Ensure you have vim-plug's `plug.vim` file installed in your autoload
"     directory. See https://github.com/junegunn/vim-plug#installation for
"     details.
"
"  2. Open a terminal in the directory containing this file and run the
"     following command to load this config isolated from your existing
"     configuration.
"
"        nvim -u init.vim
"
"  3. Install the required plugins.
"
"     :PlugInstall
"
"  --------------- Subsequent use --------------------
"
"  1. Open a terminal in the directory containing this file and run the
"     following command to load it.
"
"     nvim -u init.vim

set expandtab
set tabstop=3
set softtabstop=3
set shiftwidth=3

let mapleader='<space>'

call plug#begin('./plugged')

Plug 'neovim/nvim-lspconfig'

call plug#end()

lua << EOF
local lspconfig = require('lspconfig')

lspconfig.esbonio.setup {
  -- The following is based on the example `on_attach` function found in nvim-lspconfig's README
  -- https://github.com/neovim/nvim-lspconfig/#keybindings-and-completion
  --
  -- Only the methods currently supported by the language server are bound.
  on_attach = function(client, bufnr)
    local function buf_set_keymap(...) vim.api.nvim_buf_set_keymap(bufnr, ...) end
    local function buf_set_option(...) vim.api.nvim_buf_set_option(bufnr, ...) end

    -- Enable completion triggered by <c-x><c-o>
    buf_set_option('omnifunc', 'v:lua.vim.lsp.omnifunc')

    -- Mappings.
    local opts = { noremap=true, silent=true }

    -- See `:help vim.lsp.*` for documentation on any of the below functions
    buf_set_keymap('n', 'gd', '<cmd>lua vim.lsp.buf.definition()<CR>', opts)
    buf_set_keymap('n', '<space>e', '<cmd>lua vim.lsp.diagnostic.show_line_diagnostics()<CR>', opts)
    buf_set_keymap('n', '[d', '<cmd>lua vim.lsp.diagnostic.goto_prev()<CR>', opts)
    buf_set_keymap('n', ']d', '<cmd>lua vim.lsp.diagnostic.goto_next()<CR>', opts)
    buf_set_keymap('n', '<space>q', '<cmd>lua vim.lsp.diagnostic.set_loclist()<CR>', opts)

  end
}
EOF
