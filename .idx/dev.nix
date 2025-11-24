{ pkgs, ... }:

let
  pythonEnv = pkgs.python311.withPackages (ps: with ps; [
    flask
    werkzeug
    sqlalchemy
    pandas
    openpyxl
    xlrd
    paramiko
    cryptography
    python-dotenv
    python-dateutil
    numpy
    pyxlsb
  ]);
in
{
  channel = "stable-24.05";

  packages = [
    pythonEnv
    pkgs.python311Packages.pip
  ];

  idx = {
    extensions = [
      "ms-python.python"
    ];

    workspace = {
      onCreate = {
        install-extra-deps = ''
          echo "Instalando dependencias adicionales..."
          python3 -m pip install --break-system-packages pyxlsb==1.0.10
          python3 -m pip install --break-system-packages odfpy==1.4.1
          echo "Dependencias adicionales instaladas"
        '';
        
        create-folders = ''
          echo "Creando estructura de carpetas..."
          cd positiva-automatizacion
          mkdir -p data/maestra
          mkdir -p output/consolidador_t25
          mkdir -p temp/consolidador_t25
          mkdir -p templates/modules/consolidador_t25
          echo "Carpetas creadas"
        '';
      };
      
      onStart = {
        verify-installation = ''
          echo "Verificando instalación del Consolidador T25..."
          cd positiva-automatizacion
          python3 -c "
import sys
try:
    import flask
    import pandas
    import openpyxl
    import pyxlsb
    import paramiko
    import xlrd
    import odfpy
    print('Todas las dependencias están instaladas')
except ImportError as e:
    print('Falta dependencia:', e)
    print('Ejecuta: pip install --break-system-packages -r requirements.txt')
" || true
        '';
      };
    };

    previews = {
      enable = true;
      previews = {
        web = {
          command = ["python3" "app.py"];
          cwd = "positiva-automatizacion";
          manager = "web";
          env = {
            FLASK_ENV = "development";
            FLASK_DEBUG = "1";
          };
        };
      };
    };
  };
}