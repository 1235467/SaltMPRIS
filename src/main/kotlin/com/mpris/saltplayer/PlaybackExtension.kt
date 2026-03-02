package com.mpris.saltplayer

import com.xuncorp.spw.workshop.api.PlaybackExtensionPoint
import org.pf4j.Extension

/**
 * Playback extension that tracks current playback state
 */
@Extension
class PlaybackExtension : PlaybackExtensionPoint {

    override fun onStateChanged(state: PlaybackExtensionPoint.State) {
        PlaybackState.playerState = when (state) {
            PlaybackExtensionPoint.State.Idle -> "Stopped"
            PlaybackExtensionPoint.State.Buffering -> "Playing"
            PlaybackExtensionPoint.State.Ready -> "Playing"
            PlaybackExtensionPoint.State.Ended -> "Stopped"
        }
        PlaybackState.playbackStatus = when (state) {
            PlaybackExtensionPoint.State.Idle,
            PlaybackExtensionPoint.State.Ended -> "Stopped"
            PlaybackExtensionPoint.State.Buffering,
            PlaybackExtensionPoint.State.Ready -> if (PlaybackState.isPlaying) "Playing" else "Paused"
        }
    }

    override fun onIsPlayingChanged(isPlaying: Boolean) {
        PlaybackState.isPlaying = isPlaying
        PlaybackState.playbackStatus = if (isPlaying) "Playing" else "Paused"
    }

    override fun onBeforeLoadLyrics(mediaItem: PlaybackExtensionPoint.MediaItem): String? {
        // Update current track metadata
        PlaybackState.currentTrack = TrackMetadata(
            title = mediaItem.title,
            artist = mediaItem.artist,
            album = mediaItem.album,
            albumArtist = mediaItem.albumArtist,
            path = mediaItem.path
        )
        return null // Use default lyrics loading
    }

    override fun onPositionUpdated(position: Long) {
        PlaybackState.position = position
    }
}

/**
 * Track metadata data class
 */
data class TrackMetadata(
    val title: String,
    val artist: String,
    val album: String,
    val albumArtist: String,
    val path: String
)

/**
 * Shared playback state
 */
object PlaybackState {
    @Volatile
    var currentTrack: TrackMetadata? = null

    @Volatile
    var isPlaying: Boolean = false

    @Volatile
    var playbackStatus: String = "Stopped"

    @Volatile
    var playerState: String = "Stopped"

    @Volatile
    var position: Long = 0L
}
