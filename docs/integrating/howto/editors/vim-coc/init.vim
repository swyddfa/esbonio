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
"        (n)vim -u init.vim
"
"  3. Install the required plugins.
"
"     :PlugInstall
"
"  4. Install the coc-esbonio extension.
"
"     :CocInstall coc-esbonio
"
"  --------------- Subsequent use --------------------
"
"  1. Open a terminal in the directory containing this file and run the
"     following command to load it.
"
"     (n)vim -u init.vim

set expandtab
set tabstop=3
set softtabstop=3
set shiftwidth=3

call plug#begin('./plugins')

Plug 'neoclide/coc.nvim', {'branch': 'release'}

call plug#end()

" The following is based on snippets found in coc.nvim's README
" https://github.com/neoclide/coc.nvim
"
" Only methods currently supported by the language server are bound.
nmap <silent> [g <Plug>(coc-diagnostic-prev)
nmap <silent> ]g <Plug>(coc-diagnostic-next)

nmap <silent> gd <Plug>(coc-definition)
nnoremap <silent><nowait> <space>o  :<C-u>CocList outline<cr>
