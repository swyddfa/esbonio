{ pythonPackages }:

pythonPackages.buildPythonPackage rec {
  pname = "esbonio";
  version = "0.14.3";

  src = ./..;

  buildInputs = [
    pythonPackages.pyspellchecker
    pythonPackages.typing-extensions
  ];

  propagatedBuildInputs = [
    pythonPackages.appdirs
    pythonPackages.pygls
    pythonPackages.sphinx
  ];

  # Disable tests
  doCheck = false;
}
