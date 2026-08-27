package com.peti.app.phase6

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.launch
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject

private fun firstOccurrenceId(raw: String, preferred: String? = null): String? = runCatching {
    val values = JSONArray(raw)
    var first: String? = null
    for (index in 0 until values.length()) {
        val id = values.getJSONObject(index).optString("id").takeIf { it.isNotBlank() } ?: continue
        if (first == null) first = id
        if (id == preferred) return@runCatching id
    }
    first
}.getOrNull()

private fun occurrenceLabels(raw: String): List<String> = runCatching {
    val values = JSONArray(raw)
    buildList {
        for (index in 0 until values.length()) {
            val occurrence = values.getJSONObject(index)
            val status = occurrence.optString("status", "UPCOMING")
            val dueAt = occurrence.optString("due_at", "")
            add("Care occurrence · $status${if (dueAt.isNotBlank()) " · $dueAt" else ""}")
        }
    }
}.getOrDefault(emptyList())

private fun containsOccurrenceId(raw: String, occurrenceId: String): Boolean = runCatching {
    val values = JSONArray(raw)
    (0 until values.length()).any { index -> values.getJSONObject(index).optString("id") == occurrenceId }
}.getOrDefault(false)

private fun occurrenceActionKey(occurrenceId: String, action: String, payload: String = "") =
    UUID.nameUUIDFromBytes("$occurrenceId:$action:$payload".toByteArray()).toString()

private fun jsonQuote(value: String): String = JSONObject.quote(value)

@Composable
fun Phase6Panel(repository: Phase6Repository, animalId: String, pendingOccurrenceId: String? = null, modifier: Modifier = Modifier) {
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    var timeline by remember(animalId) { mutableStateOf("Loading Timeline…") }
    var timelineFilter by remember(animalId) { mutableStateOf<String?>(null) }
    var measurements by remember(animalId) { mutableStateOf("No measurements loaded") }
    var trend by remember(animalId) { mutableStateOf("No trend data") }
    var care by remember(animalId) { mutableStateOf("No Care items loaded") }
    var occurrences by remember(animalId) { mutableStateOf("[]") }
    var value by remember(animalId) { mutableStateOf("") }
    var unit by remember(animalId) { mutableStateOf("lb") }
    var sourceClass by remember(animalId) { mutableStateOf("MEASURED") }
    var measuredOnly by remember(animalId) { mutableStateOf(false) }
    var includeAiEstimates by remember(animalId) { mutableStateOf(false) }
    var careTitle by remember(animalId) { mutableStateOf("") }
    var careCategory by remember(animalId) { mutableStateOf("CUSTOM") }
    var careNotes by remember(animalId) { mutableStateOf("") }
    var repeatFrequency by remember(animalId) { mutableStateOf("ONCE") }
    var status by remember(animalId) { mutableStateOf("") }
    var careNotificationsEnabled by remember(animalId) { mutableStateOf(true) }
    var deepLinkStatus by remember(animalId, pendingOccurrenceId) { mutableStateOf<String?>(null) }
    val notificationPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        status = if (granted) "Notifications enabled" else "Reminders remain saved; device notifications are off"
        PetiMessagingRegistration.registerCurrent(context, if (granted) "GRANTED" else "DENIED")
    }

    fun refresh() = scope.launch {
        runCatching {
            timeline = repository.timeline(animalId, timelineFilter)
            measurements = repository.measurements(animalId, sourceClass = if (measuredOnly) "MEASURED" else null, includeAiEstimates = includeAiEstimates)
            trend = repository.measurementTrend(animalId, sourceClass = if (measuredOnly) "MEASURED" else null, includeAiEstimates = includeAiEstimates)
            care = repository.care(animalId)
            occurrences = repository.occurrences(animalId)
            careNotificationsEnabled = JSONObject(repository.notificationPreferences()).optBoolean("care_notifications_enabled", true)
            if (pendingOccurrenceId != null) {
                deepLinkStatus = if (containsOccurrenceId(occurrences, pendingOccurrenceId)) "Care occurrence opened" else "Care occurrence not found"
            }
        }.onFailure { status = "Unable to load Phase 6 data" }
    }
    LaunchedEffect(animalId, pendingOccurrenceId) { refresh() }

    Column(modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        HorizontalDivider()
        Text("Timeline", modifier = Modifier.testTag("phase6TimelineHeading"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { timelineFilter = null; scope.launch { timeline = repository.timeline(animalId) } }, modifier = Modifier.testTag("phase6TimelineAll")) { Text("All") }
            Button(onClick = { timelineFilter = "CHECKS"; scope.launch { timeline = repository.timeline(animalId, "CHECKS") } }, modifier = Modifier.testTag("phase6TimelineChecks")) { Text("Checks") }
            Button(onClick = { timelineFilter = "MEASUREMENTS"; scope.launch { timeline = repository.timeline(animalId, "MEASUREMENTS") } }, modifier = Modifier.testTag("phase6TimelineMeasurements")) { Text("Measurements") }
            Button(onClick = { timelineFilter = "CARE"; scope.launch { timeline = repository.timeline(animalId, "CARE") } }, modifier = Modifier.testTag("phase6TimelineCare")) { Text("Care") }
        }
        deepLinkStatus?.let { Text(it, modifier = Modifier.testTag("phase6DeepLinkStatus")) }
        Text(timeline.take(1_500), modifier = Modifier.testTag("phase6Timeline"))
        Button(onClick = { refresh() }, modifier = Modifier.testTag("phase6Refresh")) { Text("Refresh Timeline") }

        Text("Measurements", modifier = Modifier.testTag("phase6MeasurementsHeading"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { measuredOnly = false; includeAiEstimates = false; scope.launch { measurements = repository.measurements(animalId); trend = repository.measurementTrend(animalId) } }, modifier = Modifier.testTag("phase6AllMeasurements")) { Text("All") }
            Button(onClick = { measuredOnly = true; includeAiEstimates = false; scope.launch { measurements = repository.measurements(animalId, sourceClass = "MEASURED"); trend = repository.measurementTrend(animalId, sourceClass = "MEASURED") } }, modifier = Modifier.testTag("phase6MeasuredOnly")) { Text("Measured only") }
            Button(onClick = { measuredOnly = false; includeAiEstimates = true; scope.launch { measurements = repository.measurements(animalId, includeAiEstimates = true); trend = repository.measurementTrend(animalId, includeAiEstimates = true) } }, modifier = Modifier.testTag("phase6IncludeAiEstimates")) { Text("Include PETi estimates") }
        }
        Text(if (measuredOnly) "Measured-only history" else if (includeAiEstimates) "All provenance, including explicit PETi estimates" else "All recorded provenance; PETi estimates excluded", modifier = Modifier.testTag("phase6MeasurementFilter"))
        Text(measurements.take(1_000), modifier = Modifier.testTag("phase6Measurements"))
        Text("Deterministic trend", modifier = Modifier.testTag("phase6TrendHeading"))
        Text(trend.take(1_000), modifier = Modifier.testTag("phase6Trend"))
        OutlinedTextField(value, { value = it }, label = { Text("Value") }, modifier = Modifier.fillMaxWidth().testTag("phase6MeasurementValue"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { unit = "lb" }, modifier = Modifier.testTag("phase6UnitLb")) { Text("lb") }
            Button(onClick = { unit = "kg" }, modifier = Modifier.testTag("phase6UnitKg")) { Text("kg") }
            Button(onClick = { unit = "°F" }, modifier = Modifier.testTag("phase6UnitF")) { Text("°F") }
            Button(onClick = { unit = "°C" }, modifier = Modifier.testTag("phase6UnitC")) { Text("°C") }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { sourceClass = "MEASURED" }, modifier = Modifier.testTag("phase6SourceMeasured")) { Text("Measured") }
            Button(onClick = { sourceClass = "DOCUMENTED" }, modifier = Modifier.testTag("phase6SourceDocumented")) { Text("Documented") }
            Button(onClick = { sourceClass = "OWNER_REPORTED" }, modifier = Modifier.testTag("phase6SourceReported")) { Text("Reported") }
        }
        Text("Source: $sourceClass", modifier = Modifier.testTag("phase6MeasurementSource"))
        Text("Temperature is entered manually; PETi does not measure core temperature with your phone.", modifier = Modifier.testTag("phase6ManualTemperatureNotice"))
        Button(onClick = {
            val type = if (unit == "lb" || unit == "kg") "WEIGHT" else "TEMPERATURE"
            scope.launch {
                val canonicalValue = value.replace(',', '.')
                runCatching { repository.logMeasurement(animalId, "{\"measurement_type\":${jsonQuote(type)},\"original_value\":${jsonQuote(canonicalValue)},\"original_unit\":${jsonQuote(unit)},\"source_class\":${jsonQuote(sourceClass)}}", UUID.randomUUID().toString()) }
                    .onSuccess { status = "Measurement saved with original unit $unit"; refresh() }
                    .onFailure { status = "Measurement could not be saved" }
            }
        }, modifier = Modifier.testTag("phase6SaveMeasurement")) { Text("Save measurement") }

        Text("Care", modifier = Modifier.testTag("phase6CareHeading"))
        Text("Care reminders are saved even if notifications are denied.", modifier = Modifier.testTag("phase6NotificationExplanation"))
        Button(onClick = {
            val next = !careNotificationsEnabled
            scope.launch { runCatching { repository.updateNotificationPreferences("{\"care_notifications_enabled\":$next}") }.onSuccess { careNotificationsEnabled = next; status = if (next) "Care notifications enabled" else "Care notifications disabled" }.onFailure { status = "Notification preference could not be saved" } }
        }, modifier = Modifier.testTag("phase6CareNotificationToggle")) { Text(if (careNotificationsEnabled) "Disable care notifications" else "Enable care notifications") }
        Button(onClick = { notificationPermission.launch("android.permission.POST_NOTIFICATIONS") }, modifier = Modifier.testTag("phase6RequestNotifications")) { Text("Enable care notifications") }
        Text(care.take(1_000), modifier = Modifier.testTag("phase6Care"))
        Text(occurrences.take(1_000), modifier = Modifier.testTag("phase6Occurrences"))
        occurrenceLabels(occurrences).forEach { label ->
            Text(label, modifier = Modifier.testTag("phase6OccurrenceStatus"))
        }
        val selectedOccurrenceId = firstOccurrenceId(occurrences, pendingOccurrenceId)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = {
                selectedOccurrenceId?.let { id -> scope.launch { runCatching { repository.occurrenceAction(id, "complete", idempotencyKey = occurrenceActionKey(id, "complete")) }.onSuccess { status = "Care completed"; refresh() }.onFailure { status = "Care could not be completed" } } }
            }, enabled = selectedOccurrenceId != null, modifier = Modifier.testTag("phase6CompleteCare")) { Text("Complete") }
            Button(onClick = {
                selectedOccurrenceId?.let { id -> scope.launch { runCatching { repository.occurrenceAction(id, "skip", idempotencyKey = occurrenceActionKey(id, "skip")) }.onSuccess { status = "Care skipped"; refresh() }.onFailure { status = "Care could not be skipped" } } }
            }, enabled = selectedOccurrenceId != null, modifier = Modifier.testTag("phase6SkipCare")) { Text("Skip") }
            Button(onClick = {
                selectedOccurrenceId?.let { id ->
                    val dueAt = java.time.Instant.now().plusSeconds(86_400).toString()
                    val request = "{\"due_at\":\"$dueAt\"}"
                    scope.launch { runCatching { repository.occurrenceAction(id, "reschedule", request, occurrenceActionKey(id, "reschedule", request)) }.onSuccess { status = "Care rescheduled"; refresh() }.onFailure { status = "Care could not be rescheduled" } }
                }
            }, enabled = selectedOccurrenceId != null, modifier = Modifier.testTag("phase6RescheduleCare")) { Text("Reschedule") }
        }
        OutlinedTextField(careTitle, { careTitle = it }, label = { Text("Care title") }, modifier = Modifier.fillMaxWidth().testTag("phase6CareTitle"))
        OutlinedTextField(careNotes, { careNotes = it.take(500) }, label = { Text("Notes (optional)") }, modifier = Modifier.fillMaxWidth().testTag("phase6CareNotes"))
        Text("Category: $careCategory", modifier = Modifier.testTag("phase6CareCategoryLabel"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { careCategory = "CUSTOM" }, modifier = Modifier.testTag("phase6CategoryCustom")) { Text("Custom") }
            Button(onClick = { careCategory = "APPOINTMENT" }, modifier = Modifier.testTag("phase6CategoryAppointment")) { Text("Appointment") }
            Button(onClick = { careCategory = "BODY_CHECK" }, modifier = Modifier.testTag("phase6CategoryBodyCheck")) { Text("Body check") }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { careCategory = "VACCINATION" }, modifier = Modifier.testTag("phase6CategoryVaccination")) { Text("Vaccination") }
            Button(onClick = { careCategory = "PARASITE_PREVENTION" }, modifier = Modifier.testTag("phase6CategoryParasite")) { Text("Parasite") }
            Button(onClick = { careCategory = "MEDICATION_OR_FOLLOWUP" }, modifier = Modifier.testTag("phase6CategoryMedication")) { Text("Follow-up") }
        }
        Text("Repeat: $repeatFrequency", modifier = Modifier.testTag("phase6CareRepeatLabel"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { repeatFrequency = "ONCE" }, modifier = Modifier.testTag("phase6RepeatOnce")) { Text("Once") }
            Button(onClick = { repeatFrequency = "DAILY" }, modifier = Modifier.testTag("phase6RepeatDaily")) { Text("Daily") }
            Button(onClick = { repeatFrequency = "WEEKLY" }, modifier = Modifier.testTag("phase6RepeatWeekly")) { Text("Weekly") }
            Button(onClick = { repeatFrequency = "MONTHLY" }, modifier = Modifier.testTag("phase6RepeatMonthly")) { Text("Monthly") }
        }
        Button(onClick = {
            scope.launch {
                runCatching { repository.createCare(animalId, "{\"category\":${jsonQuote(careCategory)},\"title\":${jsonQuote(careTitle)},\"notes\":${jsonQuote(careNotes)},\"due_at\":${jsonQuote(java.time.Instant.now().toString())},\"repeat_frequency\":${jsonQuote(repeatFrequency)},\"repeat_interval\":1,\"notification_enabled\":$careNotificationsEnabled,\"timezone\":\"UTC\"}", UUID.randomUUID().toString()) }
                    .onSuccess { status = "Care item saved"; refresh() }
                    .onFailure { status = "Care item could not be saved" }
            }
        }, modifier = Modifier.testTag("phase6SaveCare")) { Text("Add Care") }
        if (status.isNotBlank()) Text(status, modifier = Modifier.testTag("phase6Status"))
    }
}
