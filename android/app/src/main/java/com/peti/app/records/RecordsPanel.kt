package com.peti.app.records

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import org.json.JSONObject
import com.peti.app.PetiPayloadCard

@Composable
fun RecordsPanel(repository: RecordsRepository, petId: String, modifier: Modifier = Modifier, onOpenSource: (String) -> Unit = {}) {
    val scope = rememberCoroutineScope(); var records by remember(petId) { mutableStateOf("Cargando registros…") }; var status by remember { mutableStateOf("") }; var selected by remember { mutableStateOf<String?>(null) }; var candidates by remember { mutableStateOf("") }; var candidateId by remember { mutableStateOf("") }
    fun refresh() { scope.launch { runCatching { repository.list(petId) }.onSuccess { records = it }.onFailure { status = "Los registros no están disponibles" } } }
    LaunchedEffect(petId) { refresh() }
    Card(modifier, colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), elevation = CardDefaults.cardElevation(1.dp)) {
      Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Historial y registros", style = MaterialTheme.typography.headlineSmall, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold, color = Color(0xFF173E43))
        Text("Todo lo importante, en orden cronológico y con su origen visible.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { AssistChip(onClick = {}, label = { Text("Todos") }); AssistChip(onClick = {}, label = { Text("Salud") }); AssistChip(onClick = {}, label = { Text("Documentos") }) }
        PetiPayloadCard(records, "Todavía no hay documentos para esta mascota.", Modifier.testTag("recordsList"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { refresh() }, modifier = Modifier.testTag("recordsRefresh")) { Text("Actualizar") }
            selected?.let { id ->
                Button(onClick = { scope.launch { runCatching { repository.access(id) }.onSuccess { response ->
                    val readUrl = runCatching { JSONObject(response).optString("read_url") }.getOrDefault("")
                    if (readUrl.isNotBlank()) onOpenSource(readUrl) else status = "Authorized source access ready"
                }.onFailure { status = "La fuente no está disponible" } } }, modifier = Modifier.testTag("recordOpen")) { Text("Abrir fuente") }
                Button(onClick = { scope.launch { runCatching { repository.extract(id) }.onSuccess { status = "Hay sugerencias listas para revisar" }.onFailure { status = "La extracción no está disponible ahora" } } }, modifier = Modifier.testTag("recordExtract")) { Text("Extraer información") }
                Button(onClick = { scope.launch { candidates = repository.candidates(id) } }, modifier = Modifier.testTag("recordCandidates")) { Text("Revisar sugerencias") }
            }
        }
        OutlinedTextField(selected.orEmpty(), { selected = it }, label = { Text("Identificador del registro") }, modifier = Modifier.testTag("recordId"))
        if (candidates.isNotBlank()) Text("Candidate facts: ${candidates.take(2_000)}", modifier = Modifier.testTag("recordCandidatesText"))
        if (candidates.isNotBlank()) {
            OutlinedTextField(candidateId, { candidateId = it }, label = { Text("Candidate id") }, modifier = Modifier.testTag("candidateId"))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { scope.launch { runCatching { repository.review(candidateId, "confirm") }.onSuccess { status = "Candidate confirmed" }.onFailure { status = "Candidate could not be confirmed" } } }, modifier = Modifier.testTag("candidateConfirm")) { Text("Confirm") }
                Button(onClick = { scope.launch { runCatching { repository.review(candidateId, "correct", "{}").also { status = "Candidate corrected" } }.onFailure { status = "Candidate could not be corrected" } } }, modifier = Modifier.testTag("candidateCorrect")) { Text("Correct") }
                Button(onClick = { scope.launch { runCatching { repository.review(candidateId, "reject") }.onSuccess { status = "Candidate rejected" }.onFailure { status = "Candidate could not be rejected" } } }, modifier = Modifier.testTag("candidateReject")) { Text("Reject") }
            }
        }
        status.takeIf { it.isNotBlank() }?.let { Text(it, modifier = Modifier.testTag("recordsStatus"), color = MaterialTheme.colorScheme.primary) }
      }
    }
}
