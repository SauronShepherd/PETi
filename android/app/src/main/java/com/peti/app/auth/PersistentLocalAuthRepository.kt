package com.peti.app.auth

import android.content.Context
import com.peti.app.BuildConfig
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** Local-only session persistence used by debug/internal fake-auth variants. */
class PersistentLocalAuthRepository(
    context: Context,
    private val defaultIdentity: String = "test-user-a",
) : AuthRepository {
    private val preferences = context.getSharedPreferences("peti_local_auth", Context.MODE_PRIVATE)
    private val mutableState = MutableStateFlow<AuthState>(
        preferences.getString(KEY_IDENTITY, null)?.let { AuthState.Authenticated(it) } ?: AuthState.SignedOut,
    )
    override val authState: StateFlow<AuthState> = mutableState.asStateFlow()

    override suspend fun signIn() {
        val identity = preferences.getString(KEY_IDENTITY, null) ?: defaultIdentity
        preferences.edit().putString(KEY_IDENTITY, identity).apply()
        mutableState.value = AuthState.Authenticated(identity)
    }

    override suspend fun signOut() {
        preferences.edit().remove(KEY_IDENTITY).apply()
        mutableState.value = AuthState.SignedOut
    }

    override suspend fun getAccessToken(forceRefresh: Boolean): String? =
        (authState.value as? AuthState.Authenticated)?.userId?.let {
            val prefix = if (BuildConfig.PETI_ENVIRONMENT == "DEV") "internal-test" else "session"
            "$prefix:$it"
        }

    private companion object { const val KEY_IDENTITY = "identity" }
}
