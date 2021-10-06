{ lib, nixpkgs ? import <nixpkgs> {}, pythonPkgs ? nixpkgs.pkgs.python38Packages }:
pythonPkgs.buildPythonPackage rec {
  name   = "phonemes2ids-${version}";
  pname = "phonemes2ids";
  version = "1.1.0";

  src = ./.;

  meta = with lib; {
    homepage    = "https://github.com/rhasspy/phonemes2ids";
    description = "Convert phonemes to integer ids";
    license     = licenses.mit;
  };

  doCheck = false;
}
