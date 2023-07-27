final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [(
    python-final: python-prev: {
      esbonio = python-prev.buildPythonPackage {
        pname = "esbonio";
        version = "0.16.1";

        src = ./..;

        propagatedBuildInputs = with python-prev; [
          docutils
          platformdirs
          pygls
          websockets
        ];

        doCheck = true;

        nativeCheckInputs = with python-prev; [
          mock
          pytest-lsp
          pytest-timeout
          pytestCheckHook
        ];

        pythonImportsCheck = [ "esbonio.server" ];
      };
    }
  )];
}
