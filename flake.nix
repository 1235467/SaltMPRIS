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

        # Fixed-output derivation: fetch all Gradle dependencies with network access.
        pluginDeps = pkgs.stdenv.mkDerivation {
          pname = "saltmpris-plugin-deps";
          version = "0-unstable";
          src = ./.;

          nativeBuildInputs = [ pkgs.gradle pkgs.jdk21 ];

          outputHashAlgo = "sha256";
          outputHashMode = "recursive";
          # Replace this hash after the first build attempt:
          #   nix build .#pluginDeps 2>&1 | grep 'got:'
          outputHash = pkgs.lib.fakeHash;

          JAVA_HOME = "${pkgs.jdk21}";
          GRADLE_USER_HOME = "$(mktemp -d)";

          buildPhase = ''
            export GRADLE_USER_HOME=$(mktemp -d)
            gradle --no-daemon resolveDependencies
          '';

          installPhase = ''
            find $GRADLE_USER_HOME/caches/modules-2 -type f \
              | sort > /dev/null  # normalize
            cp -r $GRADLE_USER_HOME $out
          '';
        };

        plugin = pkgs.stdenv.mkDerivation {
          pname = "saltmpris-plugin";
          version = "1.0.0";
          src = ./.;

          nativeBuildInputs = [ pkgs.gradle pkgs.jdk21 ];

          JAVA_HOME = "${pkgs.jdk21}";

          buildPhase = ''
            export GRADLE_USER_HOME=${pluginDeps}
            gradle --no-daemon --offline plugin
          '';

          installPhase = ''
            mkdir -p $out
            cp build/libs/*.zip $out/
          '';
        };

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
          inherit plugin mpris-bridge;
          inherit pluginDeps;
          default = mpris-bridge;
        };

        apps.default = {
          type = "app";
          program = "${mpris-bridge}/bin/saltmpris-bridge";
        };

        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.jdk21
            pkgs.gradle
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
