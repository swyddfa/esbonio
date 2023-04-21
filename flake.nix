{
  description = "The Esbonio language server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    esbonio.url = "path:lib/esbonio";
    esbonio.inputs.nixpkgs.follows = "nixpkgs";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, esbonio, utils }:

    utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system ; overlays = [ esbonio.overlays.default ];};

        esbonio-lsp = pkgs.python3Packages.esbonio.overridePythonAttrs (_: { doCheck = false ; });
        paths = pkgs.lib.makeBinPath [
          pkgs.neovim
          esbonio-lsp
        ];

        pluginList = with pkgs.vimPlugins; [
          nvim-lspconfig
        ];
        plugins = pkgs.stdenv.mkDerivation {
          name = "esbonio-nvim-plugins";
          buildCommand = ''
            mkdir -p $out/nvim/site/pack/plugins/start/
            ${pkgs.lib.concatMapStringsSep "\n" (path: "ln -s ${path} $out/nvim/site/pack/plugins/start/")  pluginList }
          '';
        };

        initVim = builtins.readFile ./docs/lsp/editors/nvim-lspconfig/init.vim;
        neovim = pkgs.writeShellScriptBin "nvim" ''
          export PATH=${paths}:$PATH
          export XDG_CONFIG_DIRS=
          export XDG_DATA_DIRS=${plugins.outPath}
          nvim --clean --cmd 'source ${pkgs.writeText "init.vim" initVim}' "$@"
        '';
      in {
         apps.default = {
           type = "app";
           program = "${neovim}/bin/nvim";
         };
       }
    );
}
