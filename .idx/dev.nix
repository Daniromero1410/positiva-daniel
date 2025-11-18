{ pkgs, ... }:

let
  # Define a Python environment with all the required packages from requirements.txt.
  # This makes the environment reproducible as Nix handles all Python dependencies,
  # avoiding conflicts and ensuring consistency.
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    flask
    pandas
    openpyxl
    python-dotenv
    pyxlsb
  ]);
in
{
  # The channel determines which package versions are available.
  # Using "stable-24.05" for consistency.
  channel = "stable-24.05";

  # A list of packages to install from the specified channel.
  packages = [
    # Our custom Python environment with all the project's dependencies.
    pythonEnv
  ];

  idx = {
    # A list of VS Code extensions to install from the Open VSX Registry.
    extensions = [
      "ms-python.python"
    ];

    # Workspace lifecycle hooks.
    # The onCreate hook for 'pip install' is no longer needed because Nix now
    # manages all Python packages.
    workspace = {
      onCreate = {};
    };

    # Configure a web preview for your application.
    previews = {
      enable = true;
      previews = {
        web = {
          command = ["python3" "-m" "flask" "run" "--host" "0.0.0.0" "--port" "$PORT"];
          # The directory to run the command in.
          cwd = "positiva-automatizacion";
          manager = "web";
        };
      };
    };
  };
}
