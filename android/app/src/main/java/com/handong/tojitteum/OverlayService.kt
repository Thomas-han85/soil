package com.handong.tojitteum

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
