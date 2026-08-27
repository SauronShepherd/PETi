package com.peti.app

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.peti.app.auth.AuthState
import com.peti.app.auth.PersistentLocalAuthRepository
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test

class LocalAuthPersistenceTest {
    @Test fun localSessionRestoresAcrossRepositoryInstancesAndSignOutClearsIt() = runBlocking {
        val context = ApplicationProvider.getApplicationContext<Context>()
        context.getSharedPreferences("peti_local_auth", Context.MODE_PRIVATE).edit().clear().commit()
        val first = PersistentLocalAuthRepository(context, "instrumented-user")
        first.signIn()
        assertEquals(AuthState.Authenticated("instrumented-user"), first.authState.value)

        val restored = PersistentLocalAuthRepository(context, "other-user")
        assertEquals(AuthState.Authenticated("instrumented-user"), restored.authState.value)
        restored.signOut()
        assertEquals(AuthState.SignedOut, PersistentLocalAuthRepository(context).authState.value)
    }
}
