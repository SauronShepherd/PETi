package com.peti.app

import android.content.Context
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import com.peti.app.auth.PersistentLocalAuthRepository
import com.peti.app.pets.PersistentSelectedPetStore
import com.peti.app.pets.Pet
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class AccountSwitchPersistenceTest {
    @Test fun accountSwitchCannotReuseAnotherUsersSelectedPet() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val store = PersistentSelectedPetStore(context)
        store.clear()
        store.save("user-a", "pet-a")
        val petA = Pet("pet-a", "user-a", "DOG", "A")
        assertEquals(petA, store.resolve("user-a", listOf(petA)))
        assertNotEquals(petA, store.resolve("user-b", listOf(petA)))
        store.clear()
    }

    @Test fun activityRecreationDoesNotEndTheAuthenticatedSession() = runBlocking {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val auth = PersistentLocalAuthRepository(context, "recreate-user")
        auth.signOut(); auth.signIn()
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            scenario.recreate()
            scenario.onActivity { check(!it.isFinishing) }
        }
        assertEquals("recreate-user", PersistentLocalAuthRepository(context).authState.value.let { (it as com.peti.app.auth.AuthState.Authenticated).userId })
        auth.signOut()
    }
}
