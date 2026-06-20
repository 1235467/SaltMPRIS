{
  description = "Salt Player MPRIS bridge + Kotlin plugin";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        python = pkgs.python3.withPackages (ps: [
          ps.dbus-python
          ps.pygobject3
          ps.requests
        ]);

        gradle = pkgs.gradle.override { java = pkgs.jdk21; };

        mpris-bridge = pkgs.writeShellApplication {
          name = "saltmpris-bridge";
          runtimeInputs = [ python pkgs.gobject-introspection pkgs.glib pkgs.dbus ];
          text = ''
            export GI_TYPELIB_PATH="${pkgs.glib}/lib/girepository-1.0''${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"
            exec ${python}/bin/python3 ${./saltplayer_mpris_http.py} "$@"
          '';
        };
      in
      {
        packages = {
          inherit mpris-bridge;
          default = mpris-bridge;
        };

        apps.default = {
          type = "app";
          program = "${mpris-bridge}/bin/saltmpris-bridge";
        };

        # Dev shell for building the Kotlin plugin:
        #   nix develop -c gradle plugin
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.jdk21
            gradle
            python
            pkgs.gobject-introspection
            pkgs.glib
            pkgs.dbus
          ];

          shellHook = ''
            export JAVA_HOME="${pkgs.jdk21}"
            export GI_TYPELIB_PATH="${pkgs.glib}/lib/girepository-1.0''${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"
          '';
        };
      });
}
