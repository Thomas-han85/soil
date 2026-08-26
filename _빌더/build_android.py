# -*- coding: utf-8 -*-
"""토질 틈틈봇 안드로이드 프로젝트 생성 — PMP 틈틈봇 구조를 그대로 이식

동작
  화면 ON → OverlayService가 감지 → LockScreenActivity(showWhenLocked)가 잠금화면 위에 카드
  런처 아이콘 → MainActivity = 전체 학습 모드
  재부팅 → BootReceiver가 서비스 재시작

PMP와 다른 점
  · 카드가 HTML에 이미 내장되어 있어 questions.json 주입이 필요 없다
  · TTS 브리지는 유지 — 잠금화면에서 질문을 읽어준다(운전 중·손 못 쓸 때)
  · 답을 보기 전에는 닫아도 '못 함'으로 기록되지 않는다(건너뛰기)

사용: python -X utf8 build_android.py
"""
import os, io, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
BOT = os.path.dirname(HERE)
APP = os.path.join(BOT, "android")
PKG = "com.handong.tojitteum"
PKGDIR = os.path.join(APP, "app/src/main/java", *PKG.split("."))

def W(rel, text):
    p = os.path.join(APP, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)

os.makedirs(PKGDIR, exist_ok=True)

# ─────────────────────────────── Manifest
W("app/src/main/AndroidManifest.xml", '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW"/>
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE"/>
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>
    <uses-permission android:name="android.permission.WAKE_LOCK"/>

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/AppTheme">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>

        <activity
            android:name=".LockScreenActivity"
            android:exported="false"
            android:excludeFromRecents="true"
            android:launchMode="singleInstance"
            android:showWhenLocked="true"
            android:turnScreenOn="true"
            android:theme="@style/LockTheme"
            android:configChanges="orientation|screenSize|keyboardHidden"/>

        <service
            android:name=".OverlayService"
            android:exported="false"
            android:foregroundServiceType="specialUse">
            <property
                android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
                android:value="lockscreen study card overlay"/>
        </service>

        <receiver
            android:name=".BootReceiver"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED"/>
            </intent-filter>
        </receiver>

    </application>
</manifest>
''')

# ─────────────────────────────── MainActivity
W("app/src/main/java/com/handong/tojitteum/Shell.kt", """package com.handong.tojitteum

import android.content.Context
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import java.io.File
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.URL

/**
 * 앱 껍데기(index.html)를 원격에서 자동 갱신한다.
 *
 * 왜 가상 도메인을 쓰나
 *   file:// 로 열면 파일 경로가 바뀔 때 origin 도 바뀌어 localStorage(학습기록)가 날아간다.
 *   요청을 가로채 항상 https://toji.local 로 보이게 하면, 내용이 어디서 오든 기록은 한자리에 쌓인다.
 *
 * 안전장치
 *   받아온 HTML 이 온전할 때만 교체한다. 깨진 파일을 올려도 이전 껍데기가 그대로 살아 있고,
 *   갱신은 Kotlin 쪽에서 돌기 때문에 껍데기가 죽어도 다음 실행에서 스스로 복구된다.
 */
object Shell {
    const val HOST = "toji.local"
    const val URL = "https://toji.local/index.html"
    private const val REMOTE = "https://raw.githubusercontent.com/Thomas-han85/soil/main/index.html"
    private const val MIN = 50000

    private fun local(ctx: Context) = File(ctx.filesDir, "shell.html")

    fun open(ctx: Context): InputStream {
        val f = local(ctx)
        return if (f.exists() && f.length() > MIN) f.inputStream()
               else ctx.assets.open("index.html")
    }

    fun refresh(ctx: Context) {
        Thread {
            try {
                val c = URL(REMOTE + "?t=" + System.currentTimeMillis()).openConnection() as HttpURLConnection
                c.connectTimeout = 8000
                c.readTimeout = 20000
                c.setRequestProperty("Cache-Control", "no-cache")
                val body = c.inputStream.bufferedReader().readText()
                c.disconnect()
                val ok = body.length > MIN &&
                         body.contains("function checkUpdate") &&
                         body.trimEnd().endsWith("</html>")
                if (ok && body != runCatching { local(ctx).readText() }.getOrNull()) {
                    val tmp = File(ctx.filesDir, "shell.tmp")
                    tmp.writeText(body)
                    local(ctx).delete()
                    tmp.renameTo(local(ctx))
                }
            } catch (e: Exception) {
                // 오프라인이면 그냥 지금 것을 쓴다
            }
        }.start()
    }
}

/** https://toji.local 요청을 로컬 껍데기로 응답한다 */
class ShellClient(private val ctx: Context) : WebViewClient() {
    override fun shouldInterceptRequest(v: WebView, req: WebResourceRequest): WebResourceResponse? {
        if (req.url.host == Shell.HOST) {
            return try {
                WebResourceResponse("text/html", "utf-8", Shell.open(ctx))
            } catch (e: Exception) { null }
        }
        return null
    }
}
""")

W("app/src/main/java/com/handong/tojitteum/MainActivity.kt", '''package com.handong.tojitteum

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
''')

# ─────────────────────────────── LockScreenActivity
W("app/src/main/java/com/handong/tojitteum/LockScreenActivity.kt", '''package com.handong.tojitteum

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
        web.webViewClient = ShellClient(this)
        web.loadUrl(Shell.URL + "?lock=1")

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
''')

# ─────────────────────────────── OverlayService
W("app/src/main/java/com/handong/tojitteum/OverlayService.kt", '''package com.handong.tojitteum

import android.app.*
import android.content.*
import android.os.Build
import android.os.IBinder

/** 포그라운드 서비스 — 화면 ON을 감지해 카드를 띄운다 */
class OverlayService : Service() {

    private var lastShow = 0L

    private val screenReceiver = object : BroadcastReceiver() {
        override fun onReceive(ctx: Context?, intent: Intent?) {
            if (intent?.action == Intent.ACTION_SCREEN_ON) {
                /* 너무 잦은 노출은 오히려 방해가 된다 — 최소 간격을 둔다 */
                val gap = getSharedPreferences("toji", Context.MODE_PRIVATE).getInt("min_gap_sec", 60) * 1000L
                val now = System.currentTimeMillis()
                if (now - lastShow < gap) return
                lastShow = now
                val i = Intent(this@OverlayService, LockScreenActivity::class.java)
                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                startActivity(i)
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        startForeground(NOTIF_ID, buildNotification())
        registerReceiver(screenReceiver, IntentFilter().apply { addAction(Intent.ACTION_SCREEN_ON) })
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY
    override fun onDestroy() { try { unregisterReceiver(screenReceiver) } catch (_: Exception) {}; super.onDestroy() }
    override fun onBind(intent: Intent?): IBinder? = null

    private fun buildNotification(): Notification {
        val ch = "toji_lock"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val nm = getSystemService(NotificationManager::class.java)
            if (nm.getNotificationChannel(ch) == null) {
                nm.createNotificationChannel(
                    NotificationChannel(ch, "토질 틈틈 잠금화면", NotificationManager.IMPORTANCE_MIN)
                )
            }
        }
        val pi = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE
        )
        val b = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
            Notification.Builder(this, ch) else Notification.Builder(this)
        return b.setContentTitle("토질 틈틈 학습")
            .setContentText("잠금화면 학습이 켜져 있습니다")
            .setSmallIcon(android.R.drawable.ic_menu_help)
            .setContentIntent(pi)
            .setOngoing(true)
            .build()
    }

    companion object {
        const val NOTIF_ID = 1001
        fun start(ctx: Context) {
            val i = Intent(ctx, OverlayService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) ctx.startForegroundService(i)
            else ctx.startService(i)
        }
    }
}
''')

# ─────────────────────────────── BootReceiver
W("app/src/main/java/com/handong/tojitteum/BootReceiver.kt", '''package com.handong.tojitteum

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
''')

# ─────────────────────────────── gradle
W("app/build.gradle", """plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}
android {
    namespace '%s'
    compileSdk 34
    defaultConfig {
        applicationId '%s'
        minSdk 26
        targetSdk 34
        versionCode 1
        versionName '1.0'
    }
    buildTypes { release { minifyEnabled false } }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = '17' }
}
dependencies { }
""" % (PKG, PKG))

W("build.gradle", """plugins {
    id 'com.android.application' version '8.5.2' apply false
    id 'org.jetbrains.kotlin.android' version '1.9.24' apply false
}
""")
W("settings.gradle", '''pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement { repositories { google(); mavenCentral() } }
rootProject.name = "TojiTteum"
include ':app'
''')
W("gradle.properties", "org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8\nandroid.useAndroidX=true\n")
W("gradle/wrapper/gradle-wrapper.properties", """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.7-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""")
W(".gitignore", ".gradle/\nbuild/\nlocal.properties\n*.iml\n.idea/\n")

# ─────────────────────────────── res
W("app/src/main/res/values/strings.xml", '<resources>\n    <string name="app_name">토질 틈틈</string>\n</resources>\n')
W("app/src/main/res/values/colors.xml", '<resources>\n    <color name="ic_bg">#1E3450</color>\n</resources>\n')
W("app/src/main/res/values/themes.xml", '''<resources>
    <style name="AppTheme" parent="@android:style/Theme.Material.Light.NoActionBar"/>
    <style name="LockTheme" parent="@android:style/Theme.Material.NoActionBar">
        <item name="android:windowIsTranslucent">true</item>
        <item name="android:windowBackground">@android:color/transparent</item>
        <item name="android:windowContentOverlay">@null</item>
        <item name="android:backgroundDimEnabled">true</item>
    </style>
</resources>
''')
for f in ("ic_launcher", "ic_launcher_round"):
    W("app/src/main/res/mipmap-anydpi-v26/%s.xml" % f, '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_bg"/>
    <foreground android:drawable="@drawable/ic_launcher_fg"/>
</adaptive-icon>
''')
W("app/src/main/res/drawable/ic_launcher_fg.xml", '''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#B08D57" android:pathData="M26,50h56v9h-56z"/>
    <path android:fillColor="#9A7A49" android:pathData="M26,61h56v9h-56z"/>
    <path android:fillColor="#84683D" android:pathData="M26,72h56v9h-56z"/>
    <path android:fillColor="#8EC9A4" android:pathData="M54,26m-11,0a11,11 0 1,0 22,0a11,11 0 1,0 -22,0"/>
</vector>
''')

# Actions 워크플로우는 저장소 루트(.github/workflows/)에 있다 — 하위 폴더는 인식되지 않는다

# ─────────────────────────────── assets = 웹앱 그대로
os.makedirs(os.path.join(APP, "app/src/main/assets"), exist_ok=True)
for f in ("index.html", "cards.json"):
    src = os.path.join(BOT, f)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(APP, "app/src/main/assets", f))

n = sum(len(fs) for _, _, fs in os.walk(APP))
print("✔ android/ 생성 — 파일 %d개 · 패키지 %s" % (n, PKG))
for root, dirs, files in os.walk(APP):
    dirs[:] = [d for d in dirs if d not in (".gradle", "build")]
    for f in sorted(files):
        p = os.path.join(root, f)
        print("   %-62s %7d" % (os.path.relpath(p, APP).replace("\\", "/"), os.path.getsize(p)))
