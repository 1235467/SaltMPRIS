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

## Building the Plugin

```bash
gradle plugin
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
pixi run python saltplayer_mpris_http.py
```

## Advantages over Window Automation

- ✅ Full metadata (title, artist, album, album artist)
- ✅ Accurate playback state
- ✅ Real-time position updates
- ✅ No dependency on window title parsing
- ✅ Works on any platform (X11, Wayland, etc.)
- ✅ More reliable and maintainable
