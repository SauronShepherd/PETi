package com.peti.app

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.peti.app.pets.PersistentSelectedPetStore
import com.peti.app.pets.Pet
import org.junit.Assert.assertEquals
import org.junit.Test

class Phase1PersistenceTest {
    @Test fun selectedPetIsScopedToCanonicalUser() {
        val context = ApplicationProvider.getApplicationContext<Context>(); val store = PersistentSelectedPetStore(context); store.clear()
        val petA = Pet("a", "user-a", "DOG", "Milo"); val petB = Pet("b", "user-b", "DOG", "Nala")
        store.save("user-a", "a"); assertEquals(petA, store.resolve("user-a", listOf(petA))); assertEquals(petB, store.resolve("user-b", listOf(petB))); store.clear()
    }
}
