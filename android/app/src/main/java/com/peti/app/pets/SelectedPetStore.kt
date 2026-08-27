package com.peti.app.pets

import android.content.Context

/** Selected pet is convenience state only and is always scoped by canonical PETi user id. */
interface SelectedPetStorePort {
    fun save(userId: String, selectedPetId: String)
    fun resolve(userId: String, ownedPets: List<Pet>): Pet?
    fun clear()
}

class SelectedPetStore : SelectedPetStorePort {
    private var ownerUserId: String? = null
    private var petId: String? = null
    override fun save(userId: String, selectedPetId: String) { ownerUserId = userId; petId = selectedPetId }
    override fun resolve(userId: String, ownedPets: List<Pet>): Pet? {
        if (ownerUserId != null && ownerUserId != userId) return ownedPets.firstOrNull { it.ownerUserId == userId }
        return ownedPets.firstOrNull { it.id == petId && it.ownerUserId == userId } ?: ownedPets.firstOrNull { it.ownerUserId == userId }
    }
    override fun clear() { ownerUserId = null; petId = null }
}

class PersistentSelectedPetStore(context: Context) : SelectedPetStorePort {
    private val preferences = context.getSharedPreferences("peti_selected_pet", Context.MODE_PRIVATE)
    override fun save(userId: String, petId: String) { preferences.edit().putString("user", userId).putString("pet", petId).apply() }
    override fun resolve(userId: String, ownedPets: List<Pet>): Pet? {
        if (preferences.getString("user", null) != userId) return ownedPets.firstOrNull { it.ownerUserId == userId }
        return ownedPets.firstOrNull { it.id == preferences.getString("pet", null) && it.ownerUserId == userId } ?: ownedPets.firstOrNull { it.ownerUserId == userId }
    }
    override fun clear() { preferences.edit().clear().apply() }
}
