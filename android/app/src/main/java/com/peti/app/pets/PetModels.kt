package com.peti.app.pets

data class SpeciesSummary(val code: String, val displayName: String, val profileEnabled: Boolean)
data class Pet(val id: String, val ownerUserId: String, val species: String, val displayName: String)

interface SpeciesRepository { suspend fun listSpecies(): List<SpeciesSummary> }
interface PetRepository {
    suspend fun listPets(): List<Pet>
    suspend fun createPet(displayName: String, species: String, idempotencyKey: String): Pet
    suspend fun updatePet(id: String, displayName: String): Pet
    suspend fun deletePet(id: String)
}
