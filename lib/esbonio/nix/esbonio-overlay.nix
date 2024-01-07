final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [(
    python-final: python-prev: {
      esbonio = python-prev.buildPythonPackage {
        pname = "esbonio";
        version = "0.16.1";
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
