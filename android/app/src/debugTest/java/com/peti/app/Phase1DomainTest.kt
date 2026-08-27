package com.peti.app

import com.peti.app.auth.FakeAuthRepository
import com.peti.app.pets.FakePetRepository
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test

class Phase1DomainTest {
    @Test fun fakeAuthUsesLocalCredentialShape() = runBlocking { val auth = FakeAuthRepository("test-user-a"); auth.signIn(); assertEquals("local-test:test-user-a", auth.getAccessToken()) }
    @Test fun selectedPetCannotCrossAccounts() { val store=com.peti.app.pets.SelectedPetStore(); val pet=com.peti.app.pets.Pet("p1","user-a","DOG","Milo"); store.save("user-a","p1"); assertEquals(null,store.resolve("user-b",listOf(pet))); assertEquals(pet,store.resolve("user-a",listOf(pet))) }
    @Test fun fakePetCreateIsIdempotent() = runBlocking { val repo=FakePetRepository(); val a=repo.createPet("Milo","DOG","key"); val b=repo.createPet("Milo","DOG","key"); assertEquals(a.id,b.id); assertEquals(1,repo.listPets().size) }
}
