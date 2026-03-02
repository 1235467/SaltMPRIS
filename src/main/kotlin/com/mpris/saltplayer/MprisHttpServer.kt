package com.mpris.saltplayer

import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import com.xuncorp.spw.workshop.api.WorkshopApi

/**
 * HTTP server that exposes playback state for MPRIS bridge
 */
class MprisHttpServer(private val port: Int = 8765) {
    private var server: NettyApplicationEngine? = null

    fun start() {
        server = embeddedServer(Netty, port = port) {
            install(ContentNegotiation) {
                json(Json {
                    prettyPrint = true
                    isLenient = true
                })
            }

            routing {
                get("/status") {
                    val track = PlaybackState.currentTrack
                    val response = StatusResponse(
                        playbackStatus = PlaybackState.playbackStatus,
                        isPlaying = PlaybackState.isPlaying,
                        position = PlaybackState.position,
                        track = if (track != null) {
                            TrackResponse(
                                title = track.title,
                                artist = track.artist,
                                album = track.album,
                                albumArtist = track.albumArtist,
                                path = track.path
                            )
                        } else null
                    )
                    call.respond(response)
                }

                post("/play") {
                    WorkshopApi.playback.play()
                    call.respond(mapOf("status" to "ok"))
                }

                post("/pause") {
                    WorkshopApi.playback.pause()
                    call.respond(mapOf("status" to "ok"))
                }

                post("/playpause") {
                    if (PlaybackState.isPlaying) {
                        WorkshopApi.playback.pause()
                    } else {
                        WorkshopApi.playback.play()
                    }
                    call.respond(mapOf("status" to "ok"))
                }

                post("/next") {
                    WorkshopApi.playback.next()
                    call.respond(mapOf("status" to "ok"))
                }

                post("/previous") {
                    WorkshopApi.playback.previous()
                    call.respond(mapOf("status" to "ok"))
                }

                post("/seek/{position}") {
                    val position = call.parameters["position"]?.toLongOrNull()
                    if (position == null || position < 0) {
                        call.respond(mapOf("status" to "error", "message" to "invalid position"))
                    } else {
                        WorkshopApi.playback.seekTo(position)
                        call.respond(mapOf("status" to "ok"))
                    }
                }

                get("/health") {
                    call.respond(mapOf("status" to "ok"))
                }
            }
        }.start(wait = false)

        println("MPRIS HTTP Server started on port $port")
    }

    fun stop() {
        server?.stop(1000, 2000)
        println("MPRIS HTTP Server stopped")
    }
}

@Serializable
data class StatusResponse(
    val playbackStatus: String,
    val isPlaying: Boolean,
    val position: Long,
    val track: TrackResponse?
)

@Serializable
data class TrackResponse(
    val title: String,
    val artist: String,
    val album: String,
    val albumArtist: String,
    val path: String
)
