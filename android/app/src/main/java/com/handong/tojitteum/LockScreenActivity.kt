package com.handong.tojitteum

import android.app.Activity
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.webkit.JavascriptInterface
import java.util.Locale
import android.view.Gravity
import android.view.ViewGroup
import android.webkit.WebView
import android.widget.Button
import android.widget.FrameLayout

/** 화면을 켤 때마다 잠금화면 위에 뜨는 카드 한 장 */
class LockScreenActivity : Activity() {

    private var tts: TextToSpeech? = null
    private var ttsReady = false

    inner class TtsBridge {
        @JavascriptInterface fun speak(text: String) {
            if (ttsReady) { tts?.setSpeechRate(1.15f); tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "toji") }
        }
        @JavascriptInterface fun stop() { tts?.stop() }
        @JavascriptInterface fun available(): Boolean = ttsReady
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        tts = TextToSpeech(this) { st ->
            if (st == TextToSpeech.SUCCESS) { tts?.language = Locale.KOREAN; tts?.setSpeechRate(1.15f); ttsReady = true }
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
        } else {
            @Suppress("DEPRECATION")
            window.addFlags(
                android.view.WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
                android.view.WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON or
                android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
            )
        }

        val root = FrameLayout(this)
        root.setBackgroundColor(Color.parseColor("#CC0B1220"))

        val web = WebView(this)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.allowFileAccess = true
        web.addJavascriptInterface(TtsBridge(), "AndroidTTS")
        web.setBackgroundColor(Color.TRANSPARENT)
        /* lock=1 → 앱이 잠금화면 모드로 뜬다. 카드 한 장만 보여주고 필터/푸터를 숨긴다 */
        web.loadUrl("file:///android_asset/index.html?lock=1")

        val lp = FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.MATCH_PARENT
        )
        lp.setMargins(24, 90, 24, 90)
        root.addView(web, lp)

        val close = Button(this)
        close.text = "✕ 닫기"
        close.setOnClickListener { finish() }
        val clp = FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT,
            ViewGroup.LayoutParams.WRAP_CONTENT
        )
        clp.gravity = Gravity.TOP or Gravity.END
        clp.setMargins(0, 36, 36, 0)
        root.addView(close, clp)

        setContentView(root)
    }

    override fun onDestroy() { tts?.stop(); tts?.shutdown(); super.onDestroy() }
}
