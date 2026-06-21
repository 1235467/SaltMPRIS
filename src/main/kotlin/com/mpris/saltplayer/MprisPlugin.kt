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
                "MPRIS Bridge started on port 8765",
                WorkshopApi.Ui.ToastType.Success
            )
        } catch (e: Exception) {
            WorkshopApi.ui.toast(
                "MPRIS Bridge failed to start: ${e.message}",
                WorkshopApi.Ui.ToastType.Error
            )
        }
    }

    override fun stop() {
        httpServer.stop()
    }

    override fun delete() {
        httpServer.stop()
    }

    override fun update() {
    }
}
