{
  description = "flake for pywayfire Python bindings";
 
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
 
  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };
    python = pkgs.python311;
  in {
    packages.${system}.pywayfire = python.pkgs.buildPythonPackage rec {
      pname = "pywayfire";
      version = "master";
 
      format = "pyproject";
 
      src = pkgs.fetchFromGitHub {
        owner = "WayfireWM";
        repo = "pywayfire";
        rev = "master";
        sha256 = "8NnKeNsuGOc2/iKgxEBGGPS0kFepXCvnLFt+5oVOcSQ=";
      };
 
      nativeBuildInputs = with python.pkgs; [ setuptools wheel ];
 
      propagatedBuildInputs = with python.pkgs; [];
 
      doCheck = false;
 
      meta = with pkgs.lib; {
        description = "Python bindings for Wayfire IPC";
        homepage = "https://github.com/WayfireWM/pywayfire";
        license = licenses.mit;
        maintainers = [ ];
        platforms = platforms.linux;
      };
    };
  };
}
