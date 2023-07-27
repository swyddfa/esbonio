final: prev: {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [(
    python-final: python-prev: {
      esbonio = python-prev.buildPythonPackage {
        pname = "esbonio";
        version = "0.16.1";

        src = ./..;

        propagatedBuildInputs = with python-prev; [
          platformdirs
          pygls
          pyspellchecker
          sphinx
          # typing-extensions; only required for Python 3.7
        ];

        doCheck = true;

        nativeCheckInputs = with python-prev; [
          mock
          pytest-lsp
          pytest-timeout
          pytestCheckHook
        ];

        pythonImportsCheck = [ "esbonio.lsp" ];
      };
    }
  )];
}
