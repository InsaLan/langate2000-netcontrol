{ pkgs ? import <nixpkgs> {} }:
let
  py-pkgs = pkgs.python3.withPackages (p: with p; [
    xmltodict
    marshmallow
    marshmallow-oneofschema
    pyroute2
    pytest
    virtualenv
  ]);
in
  pkgs.mkShell {
    packages = (with pkgs; [
      py-pkgs
      ipset
    ]);
  }
