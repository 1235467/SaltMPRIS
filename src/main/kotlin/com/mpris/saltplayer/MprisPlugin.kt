package com.mpris.saltplayer

import com.xuncorp.spw.workshop.api.PluginContext
import com.xuncorp.spw.workshop.api.SpwPlugin
import com.xuncorp.spw.workshop.api.UnstableSpwWorkshopApi
import com.xuncorp.spw.workshop.api.WorkshopApi

@OptIn(UnstableSpwWorkshopApi::class)
class MprisPlugin(
    pluginContext: PluginContext
) : SpwPlugin(pluginContext) {

    private val httpServer = MprisHttpServer(port = 8765)

    override fun start() {
        try {
            httpServer.start()
            WorkshopApi.ui.toast(
                "MPRIS Bridge Plugin started on port 8765",
                WorkshopApi.Ui.ToastType.Success
            )
            println("MPRIS Bridge Plugin: HTTP server started successfully")
        } catch (e: Exception) {
            WorkshopApi.ui.toast(
                "MPRIS Bridge Plugin failed to start: ${e.message}",
                WorkshopApi.Ui.ToastType.Error
            )
            println("MPRIS Bridge Plugin error: ${e.message}")
            e.printStackTrace()
        }
    }

    override fun stop() {
        httpServer.stop()
        WorkshopApi.ui.toast(
            "MPRIS Bridge Plugin stopped",
            WorkshopApi.Ui.ToastType.Warning
        )
        println("MPRIS Bridge Plugin: Stopped")
    }

    override fun delete() {
        httpServer.stop()
        WorkshopApi.ui.toast(
            "MPRIS Bridge Plugin deleted",
            WorkshopApi.Ui.ToastType.Error
        )
    }

    override fun update() {
        WorkshopApi.ui.toast(
            "MPRIS Bridge Plugin updated",
            WorkshopApi.Ui.ToastType.Success
        )
    }
}
