final: prev:

let
  # Read the package's version from file
  lines = prev.lib.splitString "\n" (builtins.readFile ../esbonio/server/server.py);
  matches = builtins.map (builtins.match ''__version__ = "(.+)"'') lines;
  versionStr = prev.lib.concatStrings (prev.lib.flatten (builtins.filter builtins.isList matches));
in {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [(
    python-final: python-prev: {
      esbonio = python-prev.buildPythonPackage {
        pname = "esbonio";
        version = versionStr;
        format = "pyproject";

        src = ./..;

        nativeBuildInputs = with python-final; [
          hatchling
        ];

        propagatedBuildInputs = with python-final; [
          docutils
          platformdirs
          pygls
          websockets
        ];

        doCheck = true;
        pythonImportsCheck = [ "esbonio.server" ];
        nativeCheckInputs = with python-prev; [
          mock
          pytest-lsp
          pytest-timeout
          pytestCheckHook
        ];
      };
    }
  )];
}
