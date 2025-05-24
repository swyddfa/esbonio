-- Basic options
vim.opt.number = true
vim.opt.shiftwidth = 3

-- Diagnostics
vim.diagnostic.config({
  virtual_lines = { current_line = true },
})

-- LSP Config
vim.lsp.config('esbonio', {
  cmd = { 'esbonio' },
  filetypes = { 'rst' },
  root_markers = { '.git' },
  settings = {
    esbonio = {
      -- sphinx = {
      --   buildCommand = { 'sphinx-build', '-M', 'dirhtml', '.', './_build' },
      --
      --   See: https://docs.esbon.io/en/latest/lsp/howto/use-esbonio-with.html
      --   pythonCommand = { 'hatch', '-e', 'docs', 'run', 'python' },
      -- },
      -- logging = {
      --   level = 'debug',
      --   filepath = 'esbonio.log'
      -- },
    },
  },
})
vim.lsp.enable('esbonio')
-- vim.lsp.set_log_level('DEBUG')
