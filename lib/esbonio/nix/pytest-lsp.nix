{ pythonPackages }:

pythonPackages.buildPythonPackage rec {
  pname = "pytest-lsp";
  version = "0.1.3";

  src = pythonPackages.fetchPypi {
    inherit pname version;
    sha256 = "sha256-WxTh9G3tWyGzYx1uHufkwg3hN6jTbRjlGLKJR1eUNtY=";
  };

  buildInputs = [
    pythonPackages.appdirs
    pythonPackages.pytest
  ];

  propagatedBuildInputs = [
    pythonPackages.pygls
    pythonPackages.pytest-asyncio
  ];

  # Disable tests
  doCheck = false;
}
