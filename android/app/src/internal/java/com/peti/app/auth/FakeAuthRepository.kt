package com.peti.app.auth
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
class FakeAuthRepository(private val identity: String = "test-user-a") : AuthRepository {
    private val mutableState = MutableStateFlow<AuthState>(AuthState.SignedOut)
    override val authState: StateFlow<AuthState> = mutableState.asStateFlow()
    override suspend fun signIn() { mutableState.value = AuthState.Authenticated(identity) }
    override suspend fun signOut() { mutableState.value = AuthState.SignedOut }
    override suspend fun getAccessToken(forceRefresh: Boolean): String? = if (authState.value is AuthState.Authenticated) "internal-test:$identity" else null
}
