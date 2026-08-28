package com.peti.app.phase6

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
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
import com.peti.app.PetiPayloadCard

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
            add("Recordatorio · $status${if (dueAt.isNotBlank()) " · $dueAt" else ""}")
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
    var timeline by remember(animalId) { mutableStateOf("Cargando línea de tiempo…") }
    var timelineFilter by remember(animalId) { mutableStateOf<String?>(null) }
    var measurements by remember(animalId) { mutableStateOf("Todavía no hay mediciones") }
    var trend by remember(animalId) { mutableStateOf("Todavía no hay evolución") }
    var care by remember(animalId) { mutableStateOf("Todavía no hay cuidados") }
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
        status = if (granted) "Notificaciones activadas" else "Los recordatorios se guardan; las notificaciones están desactivadas"
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
                deepLinkStatus = if (containsOccurrenceId(occurrences, pendingOccurrenceId)) "Recordatorio abierto" else "No se ha encontrado el recordatorio"
            }
        }.onFailure { status = "No se han podido cargar los datos" }
    }
    LaunchedEffect(animalId, pendingOccurrenceId) { refresh() }

    Card(modifier, colors = CardDefaults.cardColors(containerColor = androidx.compose.material3.MaterialTheme.colorScheme.surface), elevation = CardDefaults.cardElevation(1.dp)) {
      Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        HorizontalDivider()
        Text("Línea de tiempo", style = androidx.compose.material3.MaterialTheme.typography.titleLarge, modifier = Modifier.testTag("phase6TimelineHeading"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { timelineFilter = null; scope.launch { timeline = repository.timeline(animalId) } }, modifier = Modifier.testTag("phase6TimelineAll")) { Text("Todo") }
            Button(onClick = { timelineFilter = "CHECKS"; scope.launch { timeline = repository.timeline(animalId, "CHECKS") } }, modifier = Modifier.testTag("phase6TimelineChecks")) { Text("Análisis") }
            Button(onClick = { timelineFilter = "MEASUREMENTS"; scope.launch { timeline = repository.timeline(animalId, "MEASUREMENTS") } }, modifier = Modifier.testTag("phase6TimelineMeasurements")) { Text("Mediciones") }
            Button(onClick = { timelineFilter = "CARE"; scope.launch { timeline = repository.timeline(animalId, "CARE") } }, modifier = Modifier.testTag("phase6TimelineCare")) { Text("Cuidados") }
        }
        deepLinkStatus?.let { Text(it, modifier = Modifier.testTag("phase6DeepLinkStatus")) }
        PetiPayloadCard(timeline, "Todavía no hay actividad registrada.", Modifier.testTag("phase6Timeline"))
        Button(onClick = { refresh() }, modifier = Modifier.testTag("phase6Refresh")) { Text("Actualizar historial") }

        Text("Mediciones y evolución", style = androidx.compose.material3.MaterialTheme.typography.titleLarge, modifier = Modifier.testTag("phase6MeasurementsHeading"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { measuredOnly = false; includeAiEstimates = false; scope.launch { measurements = repository.measurements(animalId); trend = repository.measurementTrend(animalId) } }, modifier = Modifier.testTag("phase6AllMeasurements")) { Text("Todas") }
            Button(onClick = { measuredOnly = true; includeAiEstimates = false; scope.launch { measurements = repository.measurements(animalId, sourceClass = "MEASURED"); trend = repository.measurementTrend(animalId, sourceClass = "MEASURED") } }, modifier = Modifier.testTag("phase6MeasuredOnly")) { Text("Solo registradas") }
            Button(onClick = { measuredOnly = false; includeAiEstimates = true; scope.launch { measurements = repository.measurements(animalId, includeAiEstimates = true); trend = repository.measurementTrend(animalId, includeAiEstimates = true) } }, modifier = Modifier.testTag("phase6IncludeAiEstimates")) { Text("Incluir estimaciones PETi") }
        }
        Text(if (measuredOnly) "Historial de mediciones registradas" else if (includeAiEstimates) "Incluye estimaciones explícitas de PETi" else "Historial registrado; sin estimaciones de PETi", modifier = Modifier.testTag("phase6MeasurementFilter"))
        PetiPayloadCard(measurements, "Aún no hay mediciones guardadas.", Modifier.testTag("phase6Measurements"))
        Text("Evolución", modifier = Modifier.testTag("phase6TrendHeading"))
        PetiPayloadCard(trend, "Necesitamos más mediciones para mostrar una evolución.", Modifier.testTag("phase6Trend"))
        OutlinedTextField(value, { value = it }, label = { Text("Valor") }, modifier = Modifier.fillMaxWidth().testTag("phase6MeasurementValue"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { unit = "lb" }, modifier = Modifier.testTag("phase6UnitLb")) { Text("lb") }
            Button(onClick = { unit = "kg" }, modifier = Modifier.testTag("phase6UnitKg")) { Text("kg") }
            Button(onClick = { unit = "°F" }, modifier = Modifier.testTag("phase6UnitF")) { Text("°F") }
            Button(onClick = { unit = "°C" }, modifier = Modifier.testTag("phase6UnitC")) { Text("°C") }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { sourceClass = "MEASURED" }, modifier = Modifier.testTag("phase6SourceMeasured")) { Text("Medida") }
            Button(onClick = { sourceClass = "DOCUMENTED" }, modifier = Modifier.testTag("phase6SourceDocumented")) { Text("Documento") }
            Button(onClick = { sourceClass = "OWNER_REPORTED" }, modifier = Modifier.testTag("phase6SourceReported")) { Text("Reportada") }
        }
        Text("Origen: $sourceClass", modifier = Modifier.testTag("phase6MeasurementSource"))
        Text("La temperatura se introduce manualmente; PETi no mide la temperatura corporal con el teléfono.", modifier = Modifier.testTag("phase6ManualTemperatureNotice"))
        Button(onClick = {
            val type = if (unit == "lb" || unit == "kg") "WEIGHT" else "TEMPERATURE"
            scope.launch {
                val canonicalValue = value.replace(',', '.')
                runCatching { repository.logMeasurement(animalId, "{\"measurement_type\":${jsonQuote(type)},\"original_value\":${jsonQuote(canonicalValue)},\"original_unit\":${jsonQuote(unit)},\"source_class\":${jsonQuote(sourceClass)}}", UUID.randomUUID().toString()) }
                    .onSuccess { status = "Medición guardada en $unit"; refresh() }
                    .onFailure { status = "No se ha podido guardar la medición" }
            }
        }, modifier = Modifier.testTag("phase6SaveMeasurement")) { Text("Guardar medición") }

        Text("Cuidados y recordatorios", style = androidx.compose.material3.MaterialTheme.typography.titleLarge, modifier = Modifier.testTag("phase6CareHeading"))
        Text("Los recordatorios se guardan aunque no se permitan las notificaciones.", modifier = Modifier.testTag("phase6NotificationExplanation"))
        Button(onClick = {
            val next = !careNotificationsEnabled
            scope.launch { runCatching { repository.updateNotificationPreferences("{\"care_notifications_enabled\":$next}") }.onSuccess { careNotificationsEnabled = next; status = if (next) "Notificaciones de cuidados activadas" else "Notificaciones de cuidados desactivadas" }.onFailure { status = "No se han podido guardar las preferencias" } }
        }, modifier = Modifier.testTag("phase6CareNotificationToggle")) { Text(if (careNotificationsEnabled) "Desactivar notificaciones" else "Activar notificaciones") }
        Button(onClick = { notificationPermission.launch("android.permission.POST_NOTIFICATIONS") }, modifier = Modifier.testTag("phase6RequestNotifications")) { Text("Permitir notificaciones") }
        PetiPayloadCard(care, "No hay cuidados configurados.", Modifier.testTag("phase6Care"))
        PetiPayloadCard(occurrences, "No hay recordatorios próximos.", Modifier.testTag("phase6Occurrences"))
        occurrenceLabels(occurrences).forEach { label ->
            Text(label, modifier = Modifier.testTag("phase6OccurrenceStatus"))
        }
        val selectedOccurrenceId = firstOccurrenceId(occurrences, pendingOccurrenceId)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = {
                selectedOccurrenceId?.let { id -> scope.launch { runCatching { repository.occurrenceAction(id, "complete", idempotencyKey = occurrenceActionKey(id, "complete")) }.onSuccess { status = "Cuidado completado"; refresh() }.onFailure { status = "No se ha podido completar el cuidado" } } }
            }, enabled = selectedOccurrenceId != null, modifier = Modifier.testTag("phase6CompleteCare")) { Text("Completar") }
            Button(onClick = {
                selectedOccurrenceId?.let { id -> scope.launch { runCatching { repository.occurrenceAction(id, "skip", idempotencyKey = occurrenceActionKey(id, "skip")) }.onSuccess { status = "Cuidado omitido"; refresh() }.onFailure { status = "No se ha podido omitir el cuidado" } } }
            }, enabled = selectedOccurrenceId != null, modifier = Modifier.testTag("phase6SkipCare")) { Text("Omitir") }
            Button(onClick = {
                selectedOccurrenceId?.let { id ->
                    val dueAt = java.time.Instant.now().plusSeconds(86_400).toString()
                    val request = "{\"due_at\":\"$dueAt\"}"
                    scope.launch { runCatching { repository.occurrenceAction(id, "reschedule", request, occurrenceActionKey(id, "reschedule", request)) }.onSuccess { status = "Cuidado reprogramado"; refresh() }.onFailure { status = "No se ha podido reprogramar el cuidado" } }
                }
            }, enabled = selectedOccurrenceId != null, modifier = Modifier.testTag("phase6RescheduleCare")) { Text("Reprogramar") }
        }
        OutlinedTextField(careTitle, { careTitle = it }, label = { Text("Título del cuidado") }, modifier = Modifier.fillMaxWidth().testTag("phase6CareTitle"))
        OutlinedTextField(careNotes, { careNotes = it.take(500) }, label = { Text("Notas (opcional)") }, modifier = Modifier.fillMaxWidth().testTag("phase6CareNotes"))
        Text("Categoría: $careCategory", modifier = Modifier.testTag("phase6CareCategoryLabel"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { careCategory = "CUSTOM" }, modifier = Modifier.testTag("phase6CategoryCustom")) { Text("Personalizado") }
            Button(onClick = { careCategory = "APPOINTMENT" }, modifier = Modifier.testTag("phase6CategoryAppointment")) { Text("Cita") }
            Button(onClick = { careCategory = "BODY_CHECK" }, modifier = Modifier.testTag("phase6CategoryBodyCheck")) { Text("Revisión") }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { careCategory = "VACCINATION" }, modifier = Modifier.testTag("phase6CategoryVaccination")) { Text("Vacuna") }
            Button(onClick = { careCategory = "PARASITE_PREVENTION" }, modifier = Modifier.testTag("phase6CategoryParasite")) { Text("Parásitos") }
            Button(onClick = { careCategory = "MEDICATION_OR_FOLLOWUP" }, modifier = Modifier.testTag("phase6CategoryMedication")) { Text("Seguimiento") }
        }
        Text("Repetición: $repeatFrequency", modifier = Modifier.testTag("phase6CareRepeatLabel"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { repeatFrequency = "ONCE" }, modifier = Modifier.testTag("phase6RepeatOnce")) { Text("Una vez") }
            Button(onClick = { repeatFrequency = "DAILY" }, modifier = Modifier.testTag("phase6RepeatDaily")) { Text("Diaria") }
            Button(onClick = { repeatFrequency = "WEEKLY" }, modifier = Modifier.testTag("phase6RepeatWeekly")) { Text("Semanal") }
            Button(onClick = { repeatFrequency = "MONTHLY" }, modifier = Modifier.testTag("phase6RepeatMonthly")) { Text("Mensual") }
        }
        Button(onClick = {
            scope.launch {
                runCatching { repository.createCare(animalId, "{\"category\":${jsonQuote(careCategory)},\"title\":${jsonQuote(careTitle)},\"notes\":${jsonQuote(careNotes)},\"due_at\":${jsonQuote(java.time.Instant.now().toString())},\"repeat_frequency\":${jsonQuote(repeatFrequency)},\"repeat_interval\":1,\"notification_enabled\":$careNotificationsEnabled,\"timezone\":\"UTC\"}", UUID.randomUUID().toString()) }
                    .onSuccess { status = "Cuidado guardado"; refresh() }
                    .onFailure { status = "No se ha podido guardar el cuidado" }
            }
        }, modifier = Modifier.testTag("phase6SaveCare")) { Text("Añadir cuidado") }
        if (status.isNotBlank()) Text(status, modifier = Modifier.testTag("phase6Status"), color = androidx.compose.material3.MaterialTheme.colorScheme.primary)
      }
    }
}
