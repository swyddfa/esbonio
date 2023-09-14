{
  description = "The Esbonio language server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    utils.url = "github:numtide/flake-utils";

    lsp-devtools.url = "github:swyddfa/lsp-devtools";
    lsp-devtools.inputs.nixpkgs.follows = "nixpkgs";
    lsp-devtools.inputs.utils.follows = "utils";
  };

  outputs = { self, nixpkgs, lsp-devtools, utils }:

    utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system ; overlays = [ self.overlays.default ];};

        nvim-lspconfig = pkgs.callPackage ./docs/lsp/editors/nvim-lspconfig {};

      in {
         apps.nvim-lspconfig = {
           type = "app";
           program = "${nvim-lspconfig}/bin/nvim";
         };

      }) // {
        overlays.default = self: super:
          nixpkgs.lib.composeManyExtensions [
            lsp-devtools.overlays.default
            (import ./lib/esbonio/nix/esbonio-overlay.nix)
          ] self super;
      };
}
