package com.peti.app.pets

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.UUID

data class PetUiState(val loading: Boolean = false, val pets: List<Pet> = emptyList(), val selected: Pet? = null, val error: String? = null)

class PetViewModel(private val repository: PetRepository, private val speciesRepository: SpeciesRepository, private val selectedStore: SelectedPetStorePort = SelectedPetStore()) : ViewModel() {
    private val mutableState = MutableStateFlow(PetUiState())
    val state: StateFlow<PetUiState> = mutableState.asStateFlow()
    fun load(userId: String) = viewModelScope.launch { mutableState.value = PetUiState(loading = true); runCatching { repository.listPets() }.onSuccess { pets -> mutableState.value = PetUiState(pets = pets, selected = selectedStore.resolve(userId, pets)) }.onFailure { mutableState.value = PetUiState(error = "Unable to load pets") } }
    fun select(userId: String, pet: Pet) { selectedStore.save(userId, pet.id); mutableState.value = mutableState.value.copy(selected = pet) }
    fun create(name: String, userId: String) = viewModelScope.launch { runCatching { val species = speciesRepository.listSpecies().firstOrNull { it.profileEnabled } ?: error("SPECIES_UNAVAILABLE"); repository.createPet(name.trim(), species.code, UUID.randomUUID().toString()) }.onSuccess { pet -> val pets = mutableState.value.pets + pet; selectedStore.save(userId, pet.id); mutableState.value = mutableState.value.copy(pets = pets, selected = pet) }.onFailure { mutableState.value = mutableState.value.copy(error = "Unable to create pet") } }
    fun update(name: String) = viewModelScope.launch { val current = mutableState.value.selected ?: return@launch; runCatching { repository.updatePet(current.id, name.trim()) }.onSuccess { updated -> mutableState.value = mutableState.value.copy(pets = mutableState.value.pets.map { if (it.id == updated.id) updated else it }, selected = updated) }.onFailure { mutableState.value = mutableState.value.copy(error = "Unable to update pet") } }
    fun deleteSelected(userId: String) = viewModelScope.launch { val current = mutableState.value.selected ?: return@launch; runCatching { repository.deletePet(current.id) }.onSuccess { val remaining = mutableState.value.pets.filterNot { it.id == current.id }; mutableState.value = mutableState.value.copy(pets = remaining, selected = remaining.firstOrNull()?.also { selectedStore.save(userId, it.id) }) }.onFailure { mutableState.value = mutableState.value.copy(error = "Unable to delete pet") } }
}
