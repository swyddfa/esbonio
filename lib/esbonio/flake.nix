{
  description = "The Esbonio language server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils }:

    let
      eachPythonVersion = versions: f: builtins.listToAttrs (builtins.map (version: {name = "py${version}"; value = f version; }) versions);
    in {

    devShells = utils.lib.eachDefaultSystemMap (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
        eachPythonVersion [ "37" "38" "39" "310" "311" ] (pyVersion:
          let
            pytest-lsp = pkgs.callPackage ./nix/pytest-lsp.nix { pythonPackages = pkgs."python${pyVersion}Packages"; };
            esbonio = pkgs.callPackage ./nix/esbonio.nix { pythonPackages = pkgs."python${pyVersion}Packages"; };
          in

          with pkgs; mkShell {
            name = "py${pyVersion}";

            packages = [
              pkgs."python${pyVersion}"

              esbonio

              # test suite dependencies
              pkgs."python${pyVersion}Packages".mock
              pkgs."python${pyVersion}Packages".pytest
              pytest-lsp
              pkgs."python${pyVersion}Packages".pytest-timeout
            ];
          }
      )
    );
  };
}
