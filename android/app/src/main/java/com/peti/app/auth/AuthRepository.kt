package com.peti.app.auth

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

sealed interface AuthState { data object SignedOut : AuthState; data object SigningIn : AuthState; data class Authenticated(val userId: String) : AuthState; data class AuthError(val message: String) : AuthState }

interface AccessTokenProvider { suspend fun getAccessToken(forceRefresh: Boolean = false): String? }

interface AuthRepository : AccessTokenProvider {
    val authState: StateFlow<AuthState>
    suspend fun signIn()
    suspend fun signIn(email: String, password: String) = signIn()
    suspend fun signOut()
    override suspend fun getAccessToken(forceRefresh: Boolean): String?
}

/** Production adapter seam: Credential Manager + Firebase Auth belong only behind this boundary. */
interface FirebaseAuthRepository : AuthRepository
