package com.handong.tojitteum

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.speech.tts.TextToSpeech
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.app.Activity
import java.util.Locale

/** 런처 아이콘으로 들어오는 전체 학습 모드 */
class MainActivity : Activity() {

    private lateinit var web: WebView
    private var tts: TextToSpeech? = null
    private var ttsReady = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        tts = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.language = Locale.KOREAN
                tts?.setSpeechRate(1.15f)
                ttsReady = true
            }
        }
        web = WebView(this)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.allowFileAccess = true
        web.addJavascriptInterface(TtsBridge(), "AndroidTTS")
        web.webViewClient = ShellClient(this)
        setContentView(web)
        web.loadUrl(Shell.URL)
        Shell.refresh(this)

        requestNeededPermissions()
    }

    inner class TtsBridge {
        @JavascriptInterface
        fun speak(text: String) {
            if (ttsReady) { tts?.setSpeechRate(1.15f); tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "toji") }
        }
        @JavascriptInterface fun stop() { tts?.stop() }
        @JavascriptInterface fun available(): Boolean = ttsReady
    }

    override fun onDestroy() { tts?.stop(); tts?.shutdown(); super.onDestroy() }

    private fun requestNeededPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
            }
        }
        if (!Settings.canDrawOverlays(this)) {
            startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
        } else {
            enableLockFeature()
        }
    }

    override fun onResume() {
        super.onResume()
        if (Settings.canDrawOverlays(this)) enableLockFeature()
    }

    private fun enableLockFeature() {
        getSharedPreferences("toji", Context.MODE_PRIVATE).edit().putBoolean("lock_enabled", true).apply()
        OverlayService.start(this)
    }
}
