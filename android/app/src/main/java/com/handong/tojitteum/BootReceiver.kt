package com.handong.tojitteum

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            val enabled = context.getSharedPreferences("toji", Context.MODE_PRIVATE)
                .getBoolean("lock_enabled", false)
            if (enabled) OverlayService.start(context)
        }
    }
}
