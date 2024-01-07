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
          aiosqlite
          docutils
          platformdirs
          pygls
          websockets
        ] ++ prev.lib.optional (pythonOlder "3.11") tomli;

        doCheck = true;
        pythonImportsCheck = [ "esbonio.server" ];
        nativeCheckInputs = with python-prev; [
          pytest-lsp
          pytestCheckHook
        ];
      };
    }
  )];
}
