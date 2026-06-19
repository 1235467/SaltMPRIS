#!/usr/bin/env python3
"""
Salt Player MPRIS Bridge (HTTP-based)
Queries Salt Player plugin HTTP endpoint and exposes MPRIS D-Bus interface
"""

import logging
import requests
import time
from typing import Optional, Dict
import os
import hashlib
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

# Configuration
HTTP_ENDPOINT = "http://localhost:8765/status"
POLL_INTERVAL = 1000  # milliseconds

log = logging.getLogger("saltmpris")


class SaltPlayerHttpController:
    """Controls Salt Player via HTTP API"""

    MAX_BACKOFF = 30  # seconds

    def __init__(self):
        self.last_status = None
        self._consecutive_failures = 0

    def get_status(self) -> Optional[Dict]:
        """Get current playback status from HTTP endpoint"""
        try:
            response = requests.get(HTTP_ENDPOINT, timeout=1)
            if response.status_code == 200:
                self.last_status = response.json()
                if self._consecutive_failures > 0:
                    log.info("Reconnected to Salt Player plugin")
                self._consecutive_failures = 0
                return self.last_status
        except requests.exceptions.RequestException as e:
            self._consecutive_failures += 1
            if self._consecutive_failures == 1:
                log.warning("Lost connection to Salt Player plugin: %s", e)
            elif self._consecutive_failures % 10 == 0:
                log.warning(
                    "Still disconnected (%d consecutive failures)",
                    self._consecutive_failures,
                )

        return self.last_status

    @property
    def is_connected(self) -> bool:
        return self._consecutive_failures == 0

    def _post(self, path: str, timeout: float = 1.0) -> bool:
        try:
            response = requests.post(f"http://localhost:8765{path}", timeout=timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            log.warning("Error calling %s: %s", path, e)
            return False

    def play(self) -> bool:
        return self._post("/play")

    def pause(self) -> bool:
        return self._post("/pause")

    def play_pause(self) -> bool:
        return self._post("/playpause")

    def next(self) -> bool:
        return self._post("/next")

    def previous(self) -> bool:
        return self._post("/previous")

    def seek_to(self, position_ms: int) -> bool:
        return self._post(f"/seek/{position_ms}")


class SaltPlayerMPRIS(dbus.service.Object):
    """MPRIS2 D-Bus interface for Salt Player"""

    MPRIS_IFACE = 'org.mpris.MediaPlayer2'
    MPRIS_PLAYER_IFACE = 'org.mpris.MediaPlayer2.Player'
    MPRIS_PATH = '/org/mpris/MediaPlayer2'

    def __init__(self, bus_name):
        super().__init__(bus_name, self.MPRIS_PATH)
        self.controller = SaltPlayerHttpController()
        self.properties = {
            'CanQuit': False,
            'CanRaise': False,
            'HasTrackList': False,
            'Identity': 'Salt Player',
            'SupportedUriSchemes': [],
            'SupportedMimeTypes': [],
            'CanControl': True,
            'CanPlay': True,
            'CanPause': True,
            'CanSeek': True,
            'CanGoNext': True,
            'CanGoPrevious': True,
            'PlaybackStatus': 'Stopped',
            'Metadata': dbus.Dictionary({}, signature='sv'),
            'Position': dbus.Int64(0)
        }
        self._poll_interval = POLL_INTERVAL

        # Start polling
        GLib.timeout_add(self._poll_interval, self.update_status)

    def update_status(self) -> bool:
        """Poll Salt Player HTTP endpoint for current status"""
        status = self.controller.get_status()

        if not status:
            # If disconnected, slow down polling to reduce log spam
            if not self.controller.is_connected:
                backoff = min(
                    POLL_INTERVAL * (2 ** min(self._backoff_level(), 5)),
                    self.controller.MAX_BACKOFF * 1000,
                )
                if backoff > self._poll_interval:
                    self._poll_interval = backoff
                    GLib.timeout_add(self._poll_interval, self.update_status)
                    return False  # Stop current timer
            return True  # Continue polling

        # Restore normal poll interval after reconnection
        if self._poll_interval != POLL_INTERVAL:
            self._poll_interval = POLL_INTERVAL
            GLib.timeout_add(self._poll_interval, self.update_status)
            return False  # Stop current (slow) timer

        # Update playback status
        playback_status = status.get('playbackStatus', 'Stopped')
        if playback_status != self.properties['PlaybackStatus']:
            self.properties['PlaybackStatus'] = playback_status
            self.PropertiesChanged(
                self.MPRIS_PLAYER_IFACE,
                {'PlaybackStatus': playback_status},
                []
            )

        # Update position
        position = status.get('position', 0)
        self.properties['Position'] = dbus.Int64(position * 1000)  # Convert to microseconds

        # Update metadata
        track = status.get('track')
        if track:
            title = (track.get('title') or '').strip()
            if not title:
                path = (track.get('path') or '').strip()
                title = os.path.splitext(os.path.basename(path))[0] if path else ''
            if not title:
                title = 'Unknown'

            path = (track.get('path') or '').strip()
            track_id_source = path if path else f"{title}|{track.get('artist','')}|{track.get('album','')}"
            track_id_hash = hashlib.sha1(track_id_source.encode('utf-8', errors='ignore')).hexdigest()
            track_id = dbus.ObjectPath(f"/org/mpris/MediaPlayer2/track/{track_id_hash}")

            mpris_metadata = dbus.Dictionary({
                'mpris:trackid': track_id,
                'xesam:title': title,
                'xesam:album': (track.get('album') or ''),
                'mpris:length': dbus.Int64(0),  # Duration not available from framework
            }, signature='sv')

            # Add artist
            artist = (track.get('artist') or '').strip()
            if artist:
                mpris_metadata['xesam:artist'] = dbus.Array([artist], signature='s')

            # Add album artist
            album_artist = (track.get('albumArtist') or '').strip()
            if album_artist:
                mpris_metadata['xesam:albumArtist'] = dbus.Array([album_artist], signature='s')

            if mpris_metadata != self.properties['Metadata']:
                self.properties['Metadata'] = mpris_metadata
                self.PropertiesChanged(
                    self.MPRIS_PLAYER_IFACE,
                    {'Metadata': mpris_metadata},
                    []
                )
        else:
            if self.properties['Metadata']:
                self.properties['Metadata'] = dbus.Dictionary({}, signature='sv')
                self.PropertiesChanged(
                    self.MPRIS_PLAYER_IFACE,
                    {'Metadata': self.properties['Metadata']},
                    []
                )

        return True  # Continue polling

    def _backoff_level(self) -> int:
        return min(self.controller._consecutive_failures, 5)

    # MPRIS Root Interface
    @dbus.service.method(MPRIS_IFACE)
    def Raise(self):
        pass

    @dbus.service.method(MPRIS_IFACE)
    def Quit(self):
        pass

    # MPRIS Player Interface
    @dbus.service.method(MPRIS_PLAYER_IFACE)
    def Play(self):
        log.debug("Play()")
        self.controller.play()
        self.update_status()

    @dbus.service.method(MPRIS_PLAYER_IFACE)
    def Pause(self):
        log.debug("Pause()")
        self.controller.pause()
        self.update_status()

    @dbus.service.method(MPRIS_PLAYER_IFACE)
    def PlayPause(self):
        log.debug("PlayPause()")
        self.controller.play_pause()
        self.update_status()

    @dbus.service.method(MPRIS_PLAYER_IFACE)
    def Stop(self):
        log.debug("Stop()")
        self.controller.pause()
        self.update_status()

    @dbus.service.method(MPRIS_PLAYER_IFACE)
    def Next(self):
        log.debug("Next()")
        self.controller.next()
        self.update_status()

    @dbus.service.method(MPRIS_PLAYER_IFACE)
    def Previous(self):
        log.debug("Previous()")
        self.controller.previous()
        self.update_status()

    @dbus.service.method(MPRIS_PLAYER_IFACE, in_signature='x')
    def Seek(self, offset):
        current_us = int(self.properties.get('Position', 0))
        target_us = max(0, current_us + int(offset))
        log.debug("Seek(%d) -> %d", offset, target_us)
        self.controller.seek_to(target_us // 1000)
        self.update_status()

    @dbus.service.method(MPRIS_PLAYER_IFACE, in_signature='ox')
    def SetPosition(self, track_id, position):
        log.debug("SetPosition(%s, %d)", track_id, position)
        self.controller.seek_to(int(position) // 1000)
        self.update_status()

    @dbus.service.method(MPRIS_PLAYER_IFACE, in_signature='s')
    def OpenUri(self, uri):
        pass

    # Properties Interface
    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        if prop in self.properties:
            return self.properties[prop]
        raise dbus.exceptions.DBusException(
            f'Property {prop} not found',
            name='org.freedesktop.DBus.Error.UnknownProperty'
        )

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface == self.MPRIS_IFACE:
            return {
                'CanQuit': self.properties['CanQuit'],
                'CanRaise': self.properties['CanRaise'],
                'HasTrackList': self.properties['HasTrackList'],
                'Identity': self.properties['Identity'],
                'SupportedUriSchemes': self.properties['SupportedUriSchemes'],
                'SupportedMimeTypes': self.properties['SupportedMimeTypes']
            }
        elif interface == self.MPRIS_PLAYER_IFACE:
            return {
                'CanControl': self.properties['CanControl'],
                'CanPlay': self.properties['CanPlay'],
                'CanPause': self.properties['CanPause'],
                'CanSeek': self.properties['CanSeek'],
                'CanGoNext': self.properties['CanGoNext'],
                'CanGoPrevious': self.properties['CanGoPrevious'],
                'PlaybackStatus': self.properties['PlaybackStatus'],
                'Metadata': self.properties['Metadata'],
                'Position': self.properties['Position']
            }
        return {}

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    log.info("Starting Salt Player MPRIS bridge")

    # Setup D-Bus
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    name = dbus.service.BusName('org.mpris.MediaPlayer2.saltplayer', bus)

    # Create MPRIS interface
    mpris = SaltPlayerMPRIS(name)

    log.info("Polling %s every %dms", HTTP_ENDPOINT, POLL_INTERVAL)

    # Run main loop
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        log.info("Shutting down")
        loop.quit()


if __name__ == '__main__':
    main()
