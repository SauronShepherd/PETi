package com.peti.app.auth

import android.content.Context
import androidx.credentials.CredentialManager
import androidx.credentials.GetCredentialRequest
import androidx.credentials.GetCredentialResponse
import com.google.android.libraries.identity.googleid.GetGoogleIdOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.GoogleAuthProvider
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.tasks.await

/** Real Google -> Credential Manager -> Firebase Auth adapter. It is never used by LOCAL fake auth. */
class FirebaseCredentialAuthRepository(
    private val context: Context,
    private val webClientId: String,
    private val firebaseAuth: FirebaseAuth = FirebaseAuth.getInstance(),
) : FirebaseAuthRepository {
    private val mutableState = MutableStateFlow<AuthState>(firebaseAuth.currentUser?.let { AuthState.Authenticated(it.uid) } ?: AuthState.SignedOut)
    override val authState: StateFlow<AuthState> = mutableState.asStateFlow()
    private val credentialManager = CredentialManager.create(context)

    override suspend fun signIn() {
        mutableState.value = AuthState.SigningIn
        try {
            require(webClientId.isNotBlank()) { "Google sign-in is not configured for this build" }
            val option = GetGoogleIdOption.Builder().setServerClientId(webClientId).setFilterByAuthorizedAccounts(false).build()
            val response: GetCredentialResponse = credentialManager.getCredential(context, GetCredentialRequest(listOf(option)))
            val credential = GoogleIdTokenCredential.createFrom(response.credential.data)
            firebaseAuth.signInWithCredential(GoogleAuthProvider.getCredential(credential.idToken, null)).await()
            mutableState.value = AuthState.Authenticated(firebaseAuth.currentUser?.uid ?: error("Firebase user unavailable"))
        } catch (error: Exception) { mutableState.value = AuthState.AuthError(error.message ?: "Sign-in failed") }
    }
    override suspend fun signOut() { firebaseAuth.signOut(); mutableState.value = AuthState.SignedOut }
    override suspend fun getAccessToken(forceRefresh: Boolean): String? = firebaseAuth.currentUser?.getIdToken(forceRefresh)?.await()?.token
}
