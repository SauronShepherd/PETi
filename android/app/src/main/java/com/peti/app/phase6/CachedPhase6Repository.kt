package com.peti.app.phase6

import android.content.Context
import com.peti.app.auth.AuthRepository

/**
 * Disposable, user-scoped read cache for care history.
 * Writes always go to the delegate first; successful writes invalidate related
 * cached projections. Cache misses and failed writes are never fabricated.
 */
class CachedPhase6Repository(
    private val delegate: Phase6Repository,
    private val auth: AuthRepository,
    context: Context,
) : Phase6Repository {
    private val preferences = context.getSharedPreferences("peti_phase6_cache", Context.MODE_PRIVATE)

    private fun userScope(): String = when (val state = auth.authState.value) {
        is com.peti.app.auth.AuthState.Authenticated -> state.userId.replace(Regex("[^A-Za-z0-9_-]"), "_")
        else -> "signed-out"
    }

    private fun key(name: String) = "${userScope()}:$name"

    private suspend fun readCached(name: String, loader: suspend () -> String): String {
        return runCatching { loader() }.onSuccess { value -> preferences.edit().putString(key(name), value).apply() }
            .getOrElse { preferences.getString(key(name), null) ?: throw it }
    }

    private fun invalidate(vararg names: String) {
        preferences.edit().apply { names.forEach { remove(key(it)) } }.apply()
    }

    override suspend fun timeline(animalId: String, itemType: String?): String {
        val suffix = "timeline:$animalId:${itemType ?: "ALL"}"
        return readCached(suffix) { delegate.timeline(animalId, itemType) }
    }

    override suspend fun measurements(animalId: String, sourceClass: String?, includeAiEstimates: Boolean): String {
        val suffix = "measurements:$animalId:${sourceClass ?: "all"}:$includeAiEstimates"
        return readCached(suffix) { delegate.measurements(animalId, sourceClass, includeAiEstimates) }
    }

    override suspend fun measurementTrend(animalId: String, sourceClass: String?, includeAiEstimates: Boolean): String {
        val suffix = "trend:$animalId:${sourceClass ?: "all"}:$includeAiEstimates"
        return readCached(suffix) { delegate.measurementTrend(animalId, sourceClass, includeAiEstimates) }
    }

    override suspend fun logMeasurement(animalId: String, requestJson: String, idempotencyKey: String): String {
        val result = delegate.logMeasurement(animalId, requestJson, idempotencyKey)
        invalidateByPrefix("timeline:$animalId:")
        invalidateByPrefix("measurements:$animalId:", "trend:$animalId:")
        return result
    }

    override suspend fun care(animalId: String) = readCached("care:$animalId") { delegate.care(animalId) }

    override suspend fun occurrences(animalId: String) = readCached("occurrences:$animalId") { delegate.occurrences(animalId) }

    override suspend fun createCare(animalId: String, requestJson: String, idempotencyKey: String): String {
        val result = delegate.createCare(animalId, requestJson, idempotencyKey)
        invalidate("care:$animalId", "occurrences:$animalId")
        invalidateByPrefix("timeline:$animalId:")
        return result
    }

    override suspend fun occurrenceAction(occurrenceId: String, action: String, requestJson: String?, idempotencyKey: String?): String {
        return delegate.occurrenceAction(occurrenceId, action, requestJson, idempotencyKey)
            .also { invalidateAllPetProjections() }
    }

    override suspend fun notificationPreferences() = readCached("notification-preferences") { delegate.notificationPreferences() }

    override suspend fun updateNotificationPreferences(requestJson: String): String {
        val result = delegate.updateNotificationPreferences(requestJson)
        invalidate("notification-preferences")
        return result
    }

    override suspend fun registerDevice(requestJson: String) = delegate.registerDevice(requestJson)

    private fun invalidateByPrefix(vararg prefixes: String) {
        val prefix = "${userScope()}:"
        preferences.all.keys.filter { key -> prefixes.any { key.startsWith(prefix + it) } }
            .let { keys -> preferences.edit().apply { keys.forEach(::remove) }.apply() }
    }

    private fun invalidateAllPetProjections() {
        val prefix = "${userScope()}:"
        preferences.all.keys.filter { key -> key.startsWith(prefix + "timeline:") || key.startsWith(prefix + "care:") || key.startsWith(prefix + "occurrences:") }
            .let { keys -> preferences.edit().apply { keys.forEach(::remove) }.apply() }
    }
}
