package com.peti.app.phase6

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.peti.app.AppConfig
import com.peti.app.AppEnvironment
import com.peti.app.BuildConfig
import com.peti.app.auth.FirebaseCredentialAuthRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.util.UUID

class PetiMessagingService : FirebaseMessagingService() {
    override fun onNewToken(token: String) {
        PetiMessagingRegistration.register(this, token, "UNKNOWN")
    }

    override fun onMessageReceived(message: RemoteMessage) {
        PetiNotificationService.show(this, message)
    }
}

object PetiMessagingRegistration {
    private fun installationId(context: android.content.Context): String {
        val preferences = context.getSharedPreferences("peti_phase6", android.content.Context.MODE_PRIVATE)
        return preferences.getString("installation_id", null) ?: UUID.randomUUID().toString().also {
            preferences.edit().putString("installation_id", it).apply()
        }
    }

    fun register(context: android.content.Context, token: String, permissionState: String) {
        if (AppConfig.environment == AppEnvironment.LOCAL) return
        if (BuildConfig.PETI_GOOGLE_WEB_CLIENT_ID.isBlank()) {
            Log.w("PETiNotifications", "FCM registration skipped: Google sign-in is not configured")
            return
        }
        CoroutineScope(Dispatchers.IO).launch {
            runCatching {
                val auth = FirebaseCredentialAuthRepository(context, BuildConfig.PETI_GOOGLE_WEB_CLIENT_ID)
                ApiPhase6Repository(AppConfig.apiBaseUrl, auth).registerDevice(
                    "{\"installation_id\":\"${installationId(context)}\",\"fcm_token\":\"${token.replace("\"", "") }\",\"platform\":\"ANDROID\",\"app_version\":\"${BuildConfig.VERSION_NAME}\",\"notifications_permission_state\":\"$permissionState\"}"
                )
            }.onFailure { Log.w("PETiNotifications", "FCM registration failed") }
        }
    }

    fun registerCurrent(context: android.content.Context, permissionState: String = "UNKNOWN") {
        if (AppConfig.environment == AppEnvironment.LOCAL) return
        com.google.firebase.messaging.FirebaseMessaging.getInstance().token
            .addOnSuccessListener { token -> register(context, token, permissionState) }
            .addOnFailureListener { Log.w("PETiNotifications", "FCM token unavailable") }
    }
}
