{
  lib,
  neovim,
  stdenv,
  python3Packages,
  vimPlugins,
  writeShellScriptBin,
  writeText,
}:

let
  paths = lib.makeBinPath [
    neovim
    (python3Packages.esbonio.overridePythonAttrs (_: { doCheck = false ;}))
  ];

  pluginList = with vimPlugins; [
    nvim-lspconfig
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
