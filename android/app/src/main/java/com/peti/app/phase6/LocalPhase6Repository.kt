package com.peti.app.phase6

import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant
import java.time.ZoneOffset
import java.util.UUID

/** Local-only care-history transport used by debug and internal builds. */
class LocalPhase6Repository : Phase6Repository {
    private val measurements = mutableListOf<JSONObject>()
    private val care = mutableListOf<JSONObject>()
    private val occurrences = mutableListOf<JSONObject>()
    private var preferences = JSONObject().put("care_notifications_enabled", true)
    private val devices = mutableListOf<JSONObject>()

    private fun array(values: List<JSONObject>) = JSONArray().also { result -> values.forEach { result.put(it) } }.toString()

    override suspend fun timeline(animalId: String, itemType: String?): String {
        val items = JSONArray()
        measurements.filter { it.optString("animal_id") == animalId }.forEach {
            items.put(JSONObject().put("id", "measurement:${it.optString("id")}").put("item_type", "${it.optString("measurement_type")}_MEASUREMENT").put("source_entity_type", "MEASUREMENT").put("source_entity_id", it.optString("id")).put("summary", "${it.optString("original_value")} ${it.optString("original_unit")}"))
        }
        occurrences.filter { it.optString("animal_id") == animalId && it.optString("status") in setOf("COMPLETED", "SKIPPED") }.forEach {
            items.put(JSONObject().put("id", "care:${it.optString("id")}").put("item_type", "CARE_COMPLETION").put("source_entity_type", "CARE_OCCURRENCE").put("source_entity_id", it.optString("id")).put("summary", it.optString("status")))
        }
        if (itemType == null) return items.toString()
        val filtered = JSONArray()
        for (index in 0 until items.length()) {
            val item = items.getJSONObject(index)
            val matches = when (itemType) {
                "CHECKS" -> item.optString("item_type") == "PETI_CHECK"
                "MEASUREMENTS" -> item.optString("item_type").endsWith("_MEASUREMENT")
                "CARE" -> item.optString("item_type").startsWith("CARE_")
                else -> item.optString("item_type") == itemType
            }
            if (matches) filtered.put(item)
        }
        return filtered.toString()
    }

    override suspend fun measurements(animalId: String, sourceClass: String?, includeAiEstimates: Boolean): String = array(
        measurements.filter {
            it.optString("animal_id") == animalId &&
                (sourceClass == null || it.optString("source_class") == sourceClass) &&
                (includeAiEstimates || it.optString("source_class") != "AI_ESTIMATED")
        }
    )

    override suspend fun measurementTrend(animalId: String, sourceClass: String?, includeAiEstimates: Boolean): String =
        measurements(animalId, sourceClass, includeAiEstimates)

    override suspend fun logMeasurement(animalId: String, requestJson: String, idempotencyKey: String): String {
        val request = JSONObject(requestJson)
        val existing = measurements.firstOrNull { it.optString("idempotency_key") == idempotencyKey }
        if (existing != null) return existing.toString()
        val record = JSONObject(request.toString())
            .put("id", UUID.randomUUID().toString())
            .put("animal_id", animalId)
            .put("idempotency_key", idempotencyKey)
            .put("recorded_at", Instant.now().toString())
        measurements += record
        return record.toString()
    }

    override suspend fun care(animalId: String) = array(care.filter { it.optString("animal_id") == animalId })

    override suspend fun occurrences(animalId: String) = array(occurrences.filter { it.optString("animal_id") == animalId })

    override suspend fun createCare(animalId: String, requestJson: String, idempotencyKey: String): String {
        val existing = care.firstOrNull { it.optString("idempotency_key") == idempotencyKey }
        if (existing != null) return existing.toString()
        val item = JSONObject(requestJson).put("id", UUID.randomUUID().toString()).put("animal_id", animalId).put("idempotency_key", idempotencyKey)
        val dueAt = item.optString("due_at")
        val status = if (runCatching { Instant.parse(dueAt).isBefore(Instant.now()) }.getOrDefault(false)) "OVERDUE" else "UPCOMING"
        val occurrence = JSONObject().put("id", UUID.randomUUID().toString()).put("animal_id", animalId).put("care_id", item.optString("id")).put("due_at", dueAt).put("status", status)
        care += item
        occurrences += occurrence
        return item.toString()
    }

    override suspend fun occurrenceAction(occurrenceId: String, action: String, requestJson: String?, idempotencyKey: String?): String {
        val occurrence = occurrences.firstOrNull { it.optString("id") == occurrenceId } ?: return "{}"
        if (action == "reschedule" && requestJson != null) {
            occurrence.put("due_at", JSONObject(requestJson).optString("due_at"))
        }
        occurrence.put("status", when (action) {
            "complete" -> "COMPLETED"
            "skip" -> "SKIPPED"
            "reschedule" -> "DUE"
            else -> action.uppercase()
        })
        if (action == "complete" || action == "skip") {
            val item = care.firstOrNull { it.optString("id") == occurrence.optString("care_id") }
            val nextDue = item?.let { nextDueAt(it, occurrence.optString("due_at")) }
            if (nextDue != null && occurrences.none { it.optString("care_id") == item.optString("id") && it.optString("due_at") == nextDue }) {
                occurrences += JSONObject().put("id", UUID.randomUUID().toString()).put("animal_id", occurrence.optString("animal_id")).put("care_id", item.optString("id")).put("due_at", nextDue).put("status", "UPCOMING")
            }
        }
        return occurrence.toString()
    }

    private fun nextDueAt(item: JSONObject, current: String): String? = runCatching {
        val due = Instant.parse(current).atZone(ZoneOffset.UTC)
        val days = item.optInt("repeat_days", 0)
        when {
            days > 0 -> due.plusDays(days.toLong()).toInstant().toString()
            item.optString("repeat_frequency") == "DAILY" -> due.plusDays(item.optInt("repeat_interval", 1).toLong()).toInstant().toString()
            item.optString("repeat_frequency") == "WEEKLY" -> due.plusWeeks(item.optInt("repeat_interval", 1).toLong()).toInstant().toString()
            item.optString("repeat_frequency") == "MONTHLY" -> {
                val target = item.optInt("day_of_month", due.dayOfMonth).coerceAtLeast(1)
                val month = due.plusMonths(item.optInt("repeat_interval", 1).toLong())
                month.withDayOfMonth(target.coerceAtMost(month.toLocalDate().lengthOfMonth())).toInstant().toString()
            }
            item.optString("repeat_frequency") == "CUSTOM_INTERVAL" -> due.plusDays(item.optInt("repeat_interval", 1).toLong()).toInstant().toString()
            else -> null
        }
    }.getOrNull()

    override suspend fun notificationPreferences() = preferences.toString()

    override suspend fun updateNotificationPreferences(requestJson: String): String {
        val patch = JSONObject(requestJson)
        patch.keys().forEach { key -> preferences.put(key, patch.get(key)) }
        return preferences.toString()
    }

    override suspend fun registerDevice(requestJson: String): String {
        val device = JSONObject(requestJson).put("id", UUID.randomUUID().toString())
        devices.removeAll { it.optString("installation_id") == device.optString("installation_id") }
        devices += device
        return device.toString()
    }
}
