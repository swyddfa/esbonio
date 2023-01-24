{
  description = "The Esbonio language server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    pytest-lsp.url = "github:swyddfa/lsp-devtools?dir=lib/pytest-lsp";
    pytest-lsp.inputs.nixpkgs.follows = "nixpkgs";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, pytest-lsp, utils }:

    let
      esbonio-overlay = import ./nix/esbonio-overlay.nix;
      pytest-lsp-overlay = pytest-lsp.overlays.default;

      eachPythonVersion = versions: f:
        builtins.listToAttrs (builtins.map (version: {name = "py${version}"; value = f version; }) versions);
    in {

    overlays.default = esbonio-overlay;

    devShells = utils.lib.eachDefaultSystemMap (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ pytest-lsp-overlay esbonio-overlay ];
        };
      in
        eachPythonVersion [ "38" "39" "310" "311" ] (pyVersion:

          let
            esbonio = pkgs."python${pyVersion}Packages".esbonio.overridePythonAttrs (_: { doCheck = false; });
          in

          pkgs.mkShell {
            name = "py${pyVersion}";

            packages = with pkgs."python${pyVersion}Packages"; [
              esbonio

              mock
              pkgs."python${pyVersion}Packages".pytest-lsp
              pytest-timeout
            ];
          }
      )
    );
  };
}
