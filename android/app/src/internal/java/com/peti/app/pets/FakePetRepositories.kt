package com.peti.app.pets
class FakeSpeciesRepository : SpeciesRepository { override suspend fun listSpecies() = listOf(SpeciesSummary("DOG", "Dog", true)) }
class FakePetRepository(private val owner: String = "user-1") : PetRepository {
    private val pets = linkedMapOf<String, Pet>()
    override suspend fun listPets() = pets.values.toList()
    override suspend fun createPet(displayName: String, species: String, idempotencyKey: String): Pet = pets.getOrPut(idempotencyKey) { Pet(idempotencyKey, owner, species, displayName) }
    override suspend fun updatePet(id: String, displayName: String): Pet { val old = pets[id] ?: error("PET_NOT_FOUND"); return old.copy(displayName = displayName).also { pets[id] = it } }
    override suspend fun deletePet(id: String) { pets.remove(id) }
}
