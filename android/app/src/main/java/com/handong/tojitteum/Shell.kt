package com.handong.tojitteum

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
