package com.peti.app.phase6

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.google.firebase.messaging.RemoteMessage
import com.peti.app.MainActivity

object PetiNotificationService {
    fun show(context: android.content.Context, message: RemoteMessage) {
        val occurrenceId = message.data["occurrence_id"]?.let(CareDeepLink::occurrenceId) ?: return
        val channelId = "peti-care"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) context.getSystemService(NotificationManager::class.java)?.createNotificationChannel(NotificationChannel(channelId, "Care reminders", NotificationManager.IMPORTANCE_DEFAULT))
        val intent = Intent(context, MainActivity::class.java).apply { action = Intent.ACTION_VIEW; data = android.net.Uri.parse(CareDeepLink.forOccurrence(occurrenceId)); flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP }
        val pending = PendingIntent.getActivity(context, occurrenceId.hashCode(), intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val notification = NotificationCompat.Builder(context, channelId).setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle("Care reminder").setContentText("A care item is due for your pet").setContentIntent(pending).setAutoCancel(true).build()
        if (NotificationManagerCompat.from(context).areNotificationsEnabled()) NotificationManagerCompat.from(context).notify(occurrenceId.hashCode(), notification)
    }
}
