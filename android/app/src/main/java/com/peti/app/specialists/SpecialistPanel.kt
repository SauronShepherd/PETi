package com.peti.app.specialists

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import com.peti.app.funding.FundingViewModel
import com.peti.app.funding.OperationType
import kotlinx.coroutines.launch
import java.util.UUID
import com.peti.app.PetiPayloadCard

@Composable
fun SpecialistPanel(repository: SpecialistRepository, funding: FundingViewModel, petId: String, modifier: Modifier = Modifier) {
    val scope = rememberCoroutineScope(); var type by remember { mutableStateOf("DOG_INITIAL_SCAN") }; var mediaIds by remember { mutableStateOf("") }; var output by remember { mutableStateOf("") }; var freshnessConfirmed by remember { mutableStateOf(false) }; var producerConfirmed by remember { mutableStateOf(false) }; var candidates by remember { mutableStateOf(emptyList<InitialScanCandidateUi>()) }; var correctionValues by remember { mutableStateOf(emptyMap<String, String>()) }
    val types = listOf("DOG_INITIAL_SCAN", "DOG_DENTAL_CHECK", "DOG_FECES_CHECK", "DOG_BODY_CHECK")
    Card(modifier, colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), elevation = CardDefaults.cardElevation(1.dp)) {
      Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Analizar y entender", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, color = Color(0xFF173E43))
        Text("Elige qué quieres observar. PETi te ayuda a interpretar señales visibles de forma segura.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) { types.forEach { value ->
            val (title, description, icon, tint) = when (value) {
                "DOG_INITIAL_SCAN" -> ScanOption("Vídeo", "Observa comportamiento, movimiento y postura.", "▣", Color(0xFFE2F7F4))
                "DOG_DENTAL_CHECK" -> ScanOption("Foto", "Detecta detalles visibles de dientes y encías.", "◉", Color(0xFFFFF0E4))
                "DOG_FECES_CHECK" -> ScanOption("Digestivo / heces", "Evalúa el aspecto visible de sus heces.", "✿", Color(0xFFF0EAFE))
                else -> ScanOption("Condición corporal", "Compara postura y condición corporal.", "♢", Color(0xFFFFE9E5))
            }
            Card(colors = CardDefaults.cardColors(containerColor = tint), shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth().testTag("specialist-$value"), onClick = { type = value }) { Row(Modifier.padding(14.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) { Text(icon, style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.primary); Spacer(Modifier.width(14.dp)); Column(Modifier.weight(1f)) { Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold); Text(description, color = MaterialTheme.colorScheme.onSurfaceVariant) }; Text("›", style = MaterialTheme.typography.headlineMedium) } }
        } }
        if (type == "DOG_INITIAL_SCAN") {
            Text("Captura inicial", style = MaterialTheme.typography.titleSmall)
            Text("Necesitamos una vista del rostro y otra del cuerpo completo. Las sugerencias siempre se revisan antes de guardar.")
        }
        if (type == "DOG_DENTAL_CHECK") {
            Text("Seguridad del análisis dental", style = MaterialTheme.typography.titleSmall)
            Text("Haz fotos solo si tu perro está cómodo. No fuerces la boca y detén la captura si muestra estrés.")
            Text("PETi solo describe lo que es visible y no sustituye al veterinario.")
        }
        if (type == "DOG_FECES_CHECK") {
            Text("Captura de heces", style = MaterialTheme.typography.titleSmall)
            Text("Confirm the sample is fresh before disposal, belongs to this dog, and is not mixed with another dog's sample.")
            Text("PETi can describe visible stool appearance only. A photo cannot test parasites, infection, occult blood, microbiome, internal disease, dehydration, or definitive cause.")
            Text("Wash hands after handling the sample.")
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Checkbox(checked = freshnessConfirmed, onCheckedChange = { freshnessConfirmed = it }, modifier = Modifier.testTag("fecesFreshness"))
                Text("La muestra es fresca")
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Checkbox(checked = producerConfirmed, onCheckedChange = { producerConfirmed = it }, modifier = Modifier.testTag("fecesProducer"))
                Text("La muestra pertenece a esta mascota")
            }
        }
        if (type == "DOG_BODY_CHECK") {
            Text("Captura de condición corporal", style = MaterialTheme.typography.titleSmall)
            Text("Toma una vista lateral y otra superior con una postura natural y buena iluminación.")
            Text("Es una observación visual, no una báscula ni un analizador de grasa corporal.")
        }
        OutlinedTextField(mediaIds, { mediaIds = it }, label = { Text("Identificadores de imágenes") }, modifier = Modifier.testTag("specialistMediaIds"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { scope.launch { runCatching {
                val media = mediaIds.split(',').map { it.trim() }.filter { it.isNotBlank() }
                val operationRequestId = UUID.randomUUID().toString()
                val operation = if (type == "DOG_INITIAL_SCAN") OperationType.AI_PHOTO_STANDARD else OperationType.AI_SPECIALIST_STANDARD
                val reservationId = funding.reserve(operation, operationRequestId, operationRequestId)
                val context = if (type == "DOG_DENTAL_CHECK") ",\"owner_context\":[]" else if (type == "DOG_FECES_CHECK") ",\"capture_manifest\":{\"freshness_confirmation\":\"${if (freshnessConfirmed) "FRESH_BEFORE_DISPOSAL" else "UNKNOWN"}\",\"producer_confirmation\":$producerConfirmed,\"multi_dog_environment\":false,\"whole_sample_coverage\":true},\"owner_context\":{}" else if (type == "DOG_BODY_CHECK") ",\"capture_manifest\":{\"steps\":[{\"step_id\":\"SIDE_STANDING\"},{\"step_id\":\"TOP_STANDING\"}]}" else ""
                repository.create(petId, type, "{\"media_asset_ids\":[${media.joinToString { "\"$it\"" }}],\"funding_reservation_id\":\"$reservationId\",\"operation_request_id\":\"$operationRequestId\"$context}", operationRequestId)
            }.onSuccess { output = it }.onFailure { output = "El análisis no está disponible ahora." } } }, modifier = Modifier.testTag("specialistStart")) { Text("Iniciar") }
            Button(onClick = { scope.launch { output = repository.list(petId, type) } }, modifier = Modifier.testTag("specialistHistory")) { Text("Historial") }
        }
        if (type == "DOG_INITIAL_SCAN" && output.contains("id")) {
            Button(onClick = { scope.launch { runCatching { repository.candidates(output.substringAfter("\"id\":\"").substringBefore("\"")) }.onSuccess { payload -> candidates = parseInitialScanCandidates(payload); output = payload }.onFailure { output = "No hay sugerencias disponibles." } } }, modifier = Modifier.testTag("initialScanCandidates")) { Text("Revisar sugerencias") }
        }
        if (type == "DOG_INITIAL_SCAN" && candidates.isNotEmpty()) {
            Text("Revisa cada sugerencia", style = MaterialTheme.typography.titleSmall)
            candidates.filter { it.status == "PENDING_REVIEW" }.forEach { candidate ->
                Card(modifier = Modifier.fillMaxWidth().testTag("candidate-${candidate.id}")) {
                    Column(Modifier.padding(8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("${candidate.fieldType}: ${candidate.candidateValue}")
                        Text("Sugerencia de PETi: confírmala antes de actualizar tu perfil.")
                        OutlinedTextField(
                            value = correctionValues[candidate.id] ?: "",
                            onValueChange = { value -> correctionValues = correctionValues + (candidate.id to value) },
                            label = { Text("Valor corregido") },
                            modifier = Modifier.fillMaxWidth().testTag("candidate-value-${candidate.id}"),
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                            Button(onClick = { scope.launch { output = repository.review(candidate.id, "confirm") ; candidates = candidates.map { if (it.id == candidate.id) it.copy(status = "CONFIRMED", provenanceStatus = "USER_CONFIRMED") else it } } }, modifier = Modifier.testTag("candidate-confirm-${candidate.id}")) { Text("Confirmar") }
                            Button(onClick = { scope.launch { val value = correctionValues[candidate.id].orEmpty().trim(); if (value.isNotEmpty()) { output = repository.review(candidate.id, "correct", "{\"value\":\"$value\"}"); candidates = candidates.map { if (it.id == candidate.id) it.copy(status = "CORRECTED", provenanceStatus = "USER_CORRECTED") else it } } else output = "Enter a corrected value" } }, modifier = Modifier.testTag("candidate-correct-${candidate.id}")) { Text("Correct") }
                            OutlinedButton(onClick = { scope.launch { output = repository.review(candidate.id, "reject"); candidates = candidates.map { if (it.id == candidate.id) it.copy(status = "REJECTED") else it } } }, modifier = Modifier.testTag("candidate-reject-${candidate.id}")) { Text("Rechazar") }
                            OutlinedButton(onClick = { scope.launch { output = repository.review(candidate.id, "skip"); candidates = candidates.map { if (it.id == candidate.id) it.copy(status = "SKIPPED") else it } } }, modifier = Modifier.testTag("candidate-skip-${candidate.id}")) { Text("Skip") }
                        }
                    }
                }
            }
        }
        if (output.contains("QUEUED")) {
            Button(onClick = { scope.launch { val id = output.substringAfter("\"id\":\"").substringBefore("\""); output = repository.get(id, type) } }, modifier = Modifier.testTag("specialistRefresh")) { Text("Actualizar resultado") }
        }
        PetiPayloadCard(output, "Aún no hay resultados para mostrar.", Modifier.testTag("specialistOutput"))
      }
    }
}

private data class ScanOption(val title: String, val description: String, val icon: String, val tint: Color)
