# Salt Player MPRIS Plugin

A Salt Player plugin that exposes playback information via HTTP for MPRIS D-Bus integration.

## Architecture

**Plugin Side (Kotlin):**
- Implements `PlaybackExtensionPoint` to receive playback events
- Runs HTTP server on port 8765
- Exposes `/status` endpoint with current track metadata and playback state

**Bridge Side (Python):**
- Queries HTTP endpoint for track info
- Exposes MPRIS D-Bus interface
- Enables media key control and desktop integration

## Prerequisites

This project uses a [Nix flake](https://nixos.wiki/wiki/Flakes) to provide all build dependencies (JDK 21, Gradle, Python + libraries). Install Nix with flakes enabled, then:

```bash
# Enter the dev shell (provides java, gradle, python, dbus libs)
nix develop

# Or run commands directly without entering the shell
nix develop -c <command>
```

## Building the Plugin

```bash
nix develop -c gradle plugin
```

The plugin will be built as `build/libs/plugin-saltplayer-mpris-1.0.0.zip`

## Installing the Plugin

Install using workshop function in SPW app.

## API Endpoints

### GET /status
Returns current playback status and track metadata:

```json
{
  "playbackStatus": "Playing",
  "isPlaying": true,
  "position": 45000,
  "track": {
    "title": "Song Title",
    "artist": "Artist Name",
    "album": "Album Name",
    "albumArtist": "Album Artist",
    "path": "C:\\Music\\song.mp3"
  }
}
```

### GET /health
Health check endpoint:

```json
{
  "status": "ok"
}
```

## Python MPRIS Bridge

The Python bridge queries the HTTP endpoint and exposes MPRIS interface:

```bash
# Run directly via nix (no dev shell needed)
nix run

# Or build it as a standalone script
nix build
./result/bin/saltmpris-bridge

# Or run from the dev shell
nix develop -c python3 saltplayer_mpris_http.py
```
