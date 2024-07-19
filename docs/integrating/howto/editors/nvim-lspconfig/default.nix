{
  lib,
  neovim,
  ripgrep,
  stdenv,
  python3Packages,
  vimPlugins,
  writeShellScriptBin,
  writeText,
}:

let
  # Executables that should be on $PATH
  paths = lib.makeBinPath [
    neovim
    ripgrep
    python3Packages.lsp-devtools
    (python3Packages.esbonio.overridePythonAttrs (_: { doCheck = false ;}))
  ];

  # Plugins that should be avaiable to nvim.
  pluginList = with vimPlugins; [
    everforest         # colortheme
    fidget-nvim        # UI for '$/progress'
    lualine-nvim       # statusline
    neoscroll-nvim     # smooth scrolling
    nvim-lspconfig
    nvim-web-devicons
    plenary-nvim       # Required for telescope
    telescope-nvim     # The helm/vertico/etc. of the nvim world
    toggleterm-nvim    # popup terminal windows
  ];

  plugins = stdenv.mkDerivation {
    name = "esbonio-nvim-plugins";
    buildCommand = ''
      mkdir -p $out/nvim/site/pack/plugins/start/
      ${lib.concatMapStringsSep "\n" (path: "ln -s ${path} $out/nvim/site/pack/plugins/start/") pluginList}
    '';
  };

  initVim = builtins.readFile ./init.vim;
in

writeShellScriptBin "nvim" ''
  export PATH=${paths}:$PATH
  export XDG_CONFIG_DIRS=
  export XDG_DATA_DIRS=${plugins.outPath}
  nvim --clean --cmd 'source ${writeText "init.vim" initVim}' "$@"
''
