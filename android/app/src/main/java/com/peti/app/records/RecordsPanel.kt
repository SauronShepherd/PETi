package com.peti.app.records

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import org.json.JSONObject

@Composable
fun RecordsPanel(repository: RecordsRepository, petId: String, modifier: Modifier = Modifier, onOpenSource: (String) -> Unit = {}) {
    val scope = rememberCoroutineScope(); var records by remember(petId) { mutableStateOf("Loading Records…") }; var status by remember { mutableStateOf("") }; var selected by remember { mutableStateOf<String?>(null) }; var candidates by remember { mutableStateOf("") }; var candidateId by remember { mutableStateOf("") }
    fun refresh() { scope.launch { runCatching { repository.list(petId) }.onSuccess { records = it }.onFailure { status = "Records unavailable" } } }
    LaunchedEffect(petId) { refresh() }
    Column(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Records", style = MaterialTheme.typography.titleMedium)
        Text("Private veterinary documents. Viewing and review never require an ad.")
        Text(records.take(2_000), modifier = Modifier.testTag("recordsList"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { refresh() }, modifier = Modifier.testTag("recordsRefresh")) { Text("Refresh") }
            selected?.let { id ->
                Button(onClick = { scope.launch { runCatching { repository.access(id) }.onSuccess { response ->
                    val readUrl = runCatching { JSONObject(response).optString("read_url") }.getOrDefault("")
                    if (readUrl.isNotBlank()) onOpenSource(readUrl) else status = "Authorized source access ready"
                }.onFailure { status = "Source unavailable" } } }, modifier = Modifier.testTag("recordOpen")) { Text("Open") }
                Button(onClick = { scope.launch { runCatching { repository.extract(id) }.onSuccess { status = "Extraction suggestions ready for review" }.onFailure { status = "Extraction unavailable until funding and worker processing complete" } } }, modifier = Modifier.testTag("recordExtract")) { Text("Extract information") }
                Button(onClick = { scope.launch { candidates = repository.candidates(id) } }, modifier = Modifier.testTag("recordCandidates")) { Text("Review suggestions") }
            }
        }
        OutlinedTextField(selected.orEmpty(), { selected = it }, label = { Text("Record id") }, modifier = Modifier.testTag("recordId"))
        if (candidates.isNotBlank()) Text("Candidate facts: ${candidates.take(2_000)}", modifier = Modifier.testTag("recordCandidatesText"))
        if (candidates.isNotBlank()) {
            OutlinedTextField(candidateId, { candidateId = it }, label = { Text("Candidate id") }, modifier = Modifier.testTag("candidateId"))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { scope.launch { runCatching { repository.review(candidateId, "confirm") }.onSuccess { status = "Candidate confirmed" }.onFailure { status = "Candidate could not be confirmed" } } }, modifier = Modifier.testTag("candidateConfirm")) { Text("Confirm") }
                Button(onClick = { scope.launch { runCatching { repository.review(candidateId, "correct", "{}").also { status = "Candidate corrected" } }.onFailure { status = "Candidate could not be corrected" } } }, modifier = Modifier.testTag("candidateCorrect")) { Text("Correct") }
                Button(onClick = { scope.launch { runCatching { repository.review(candidateId, "reject") }.onSuccess { status = "Candidate rejected" }.onFailure { status = "Candidate could not be rejected" } } }, modifier = Modifier.testTag("candidateReject")) { Text("Reject") }
            }
        }
        status.takeIf { it.isNotBlank() }?.let { Text(it, modifier = Modifier.testTag("recordsStatus")) }
    }
}
