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

Plug 'prabirshrestha/vim-lsp'
Plug 'mattn/vim-lsp-settings'

call plug#end()

" The following is based on the example setup found in vim-lsp's README
" https://github.com/prabirshrestha/vim-lsp
"
" Only the methods currently supported by the language server are bound.
function! s:on_lsp_buffer_enabled() abort
    setlocal omnifunc=lsp#complete
    setlocal signcolumn=yes
    if exists('+tagfunc') | setlocal tagfunc=lsp#tagfunc | endif
    nmap <buffer> gd <plug>(lsp-definition)
    nmap <buffer> gs <plug>(lsp-document-symbol-search)
    nmap <buffer> [g <plug>(lsp-previous-diagnostic)
    nmap <buffer> ]g <plug>(lsp-next-diagnostic)
endfunction

augroup lsp_install
    au!
    " call s:on_lsp_buffer_enabled only for languages that has the server registered.
    autocmd User lsp_buffer_enabled call s:on_lsp_buffer_enabled()
augroup END
