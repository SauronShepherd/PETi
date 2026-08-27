package com.peti.app.specialists

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import com.peti.app.funding.FundingViewModel
import com.peti.app.funding.OperationType
import kotlinx.coroutines.launch
import java.util.UUID

@Composable
fun SpecialistPanel(repository: SpecialistRepository, funding: FundingViewModel, petId: String, modifier: Modifier = Modifier) {
    val scope = rememberCoroutineScope(); var type by remember { mutableStateOf("DOG_INITIAL_SCAN") }; var mediaIds by remember { mutableStateOf("") }; var output by remember { mutableStateOf("") }; var freshnessConfirmed by remember { mutableStateOf(false) }; var producerConfirmed by remember { mutableStateOf(false) }; var candidates by remember { mutableStateOf(emptyList<InitialScanCandidateUi>()) }; var correctionValues by remember { mutableStateOf(emptyMap<String, String>()) }
    val types = listOf("DOG_INITIAL_SCAN", "DOG_DENTAL_CHECK", "DOG_FECES_CHECK", "DOG_BODY_CHECK")
    Column(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Dog specialist checks", style = MaterialTheme.typography.titleMedium)
        Text("Cloud visual assistance is non-diagnostic. Select one dog and review every result before using it.")
        Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) { types.forEach { value -> Button(onClick = { type = value }, modifier = Modifier.testTag("specialist-$value")) { Text(value.removePrefix("DOG_").replace('_', ' ')) } } }
        if (type == "DOG_INITIAL_SCAN") {
            Text("Initial Scan capture", style = MaterialTheme.typography.titleSmall)
            Text("Required: face view and one full-body side or standing view. Optional: top view and distinguishing marks.")
            Text("Suggestions remain candidates: Confirm, Correct, Reject, or Skip. PETi never changes the canonical profile automatically.")
        }
        if (type == "DOG_DENTAL_CHECK") {
            Text("Dental Check safety", style = MaterialTheme.typography.titleSmall)
            Text("Only take photos if your dog is comfortable.")
            Text("Do not force the mouth open.")
            Text("Stop if your dog becomes stressed or may bite.")
            Text("Visible-only findings preserve areas not assessed and never claim periodontal stage, pocket depth, roots, bone, or pulp health.")
        }
        if (type == "DOG_FECES_CHECK") {
            Text("Feces Check capture", style = MaterialTheme.typography.titleSmall)
            Text("Confirm the sample is fresh before disposal, belongs to this dog, and is not mixed with another dog's sample.")
            Text("PETi can describe visible stool appearance only. A photo cannot test parasites, infection, occult blood, microbiome, internal disease, dehydration, or definitive cause.")
            Text("Wash hands after handling the sample.")
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Checkbox(checked = freshnessConfirmed, onCheckedChange = { freshnessConfirmed = it }, modifier = Modifier.testTag("fecesFreshness"))
                Text("Fresh sample before disposal")
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Checkbox(checked = producerConfirmed, onCheckedChange = { producerConfirmed = it }, modifier = Modifier.testTag("fecesProducer"))
                Text("This sample came from this dog")
            }
        }
        if (type == "DOG_BODY_CHECK") {
            Text("Body Check capture", style = MaterialTheme.typography.titleSmall)
            Text("Required views: natural side-standing and top-standing. Keep pose, distance, lighting, and coat presentation consistent for future comparison.")
            Text("Body Check is visual assistance, not a scale or body-fat analyzer. Measured and documented weights remain separate.")
        }
        OutlinedTextField(mediaIds, { mediaIds = it }, label = { Text("Ready image media IDs") }, modifier = Modifier.testTag("specialistMediaIds"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { funding.request(if (type == "DOG_INITIAL_SCAN") OperationType.AI_PHOTO_STANDARD else OperationType.AI_SPECIALIST_STANDARD) }, modifier = Modifier.testTag("specialistFundingQuote")) { Text("Check funding") }
            Button(onClick = { funding.watchAdAndRefresh() }, modifier = Modifier.testTag("specialistRewardedFunding")) { Text("Earn credits") }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { scope.launch { runCatching {
                val media = mediaIds.split(',').map { it.trim() }.filter { it.isNotBlank() }
                val operationRequestId = UUID.randomUUID().toString()
                val operation = if (type == "DOG_INITIAL_SCAN") OperationType.AI_PHOTO_STANDARD else OperationType.AI_SPECIALIST_STANDARD
                val reservationId = funding.reserve(operation, operationRequestId, operationRequestId)
                val context = if (type == "DOG_DENTAL_CHECK") ",\"owner_context\":[]" else if (type == "DOG_FECES_CHECK") ",\"capture_manifest\":{\"freshness_confirmation\":\"${if (freshnessConfirmed) "FRESH_BEFORE_DISPOSAL" else "UNKNOWN"}\",\"producer_confirmation\":$producerConfirmed,\"multi_dog_environment\":false,\"whole_sample_coverage\":true},\"owner_context\":{}" else if (type == "DOG_BODY_CHECK") ",\"capture_manifest\":{\"steps\":[{\"step_id\":\"SIDE_STANDING\"},{\"step_id\":\"TOP_STANDING\"}]}" else ""
                repository.create(petId, type, "{\"media_asset_ids\":[${media.joinToString { "\"$it\"" }}],\"funding_reservation_id\":\"$reservationId\",\"operation_request_id\":\"$operationRequestId\"$context}", operationRequestId)
            }.onSuccess { output = it }.onFailure { output = "Specialist check unavailable" } } }, modifier = Modifier.testTag("specialistStart")) { Text("Start") }
            Button(onClick = { scope.launch { output = repository.list(petId, type) } }, modifier = Modifier.testTag("specialistHistory")) { Text("History") }
        }
        if (type == "DOG_INITIAL_SCAN" && output.contains("id")) {
            Button(onClick = { scope.launch { runCatching { repository.candidates(output.substringAfter("\"id\":\"").substringBefore("\"")) }.onSuccess { payload -> candidates = parseInitialScanCandidates(payload); output = payload }.onFailure { output = "Suggestions unavailable" } } }, modifier = Modifier.testTag("initialScanCandidates")) { Text("Review scan suggestions") }
        }
        if (type == "DOG_INITIAL_SCAN" && candidates.isNotEmpty()) {
            Text("Review each suggestion", style = MaterialTheme.typography.titleSmall)
            candidates.filter { it.status == "PENDING_REVIEW" }.forEach { candidate ->
                Card(modifier = Modifier.fillMaxWidth().testTag("candidate-${candidate.id}")) {
                    Column(Modifier.padding(8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("${candidate.fieldType}: ${candidate.candidateValue}")
                        Text("AI suggestion — confirm it before it can update your profile.")
                        OutlinedTextField(
                            value = correctionValues[candidate.id] ?: "",
                            onValueChange = { value -> correctionValues = correctionValues + (candidate.id to value) },
                            label = { Text("Corrected value") },
                            modifier = Modifier.fillMaxWidth().testTag("candidate-value-${candidate.id}"),
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                            Button(onClick = { scope.launch { output = repository.review(candidate.id, "confirm") ; candidates = candidates.map { if (it.id == candidate.id) it.copy(status = "CONFIRMED", provenanceStatus = "USER_CONFIRMED") else it } } }, modifier = Modifier.testTag("candidate-confirm-${candidate.id}")) { Text("Confirm") }
                            Button(onClick = { scope.launch { val value = correctionValues[candidate.id].orEmpty().trim(); if (value.isNotEmpty()) { output = repository.review(candidate.id, "correct", "{\"value\":\"$value\"}"); candidates = candidates.map { if (it.id == candidate.id) it.copy(status = "CORRECTED", provenanceStatus = "USER_CORRECTED") else it } } else output = "Enter a corrected value" } }, modifier = Modifier.testTag("candidate-correct-${candidate.id}")) { Text("Correct") }
                            OutlinedButton(onClick = { scope.launch { output = repository.review(candidate.id, "reject"); candidates = candidates.map { if (it.id == candidate.id) it.copy(status = "REJECTED") else it } } }, modifier = Modifier.testTag("candidate-reject-${candidate.id}")) { Text("Reject") }
                            OutlinedButton(onClick = { scope.launch { output = repository.review(candidate.id, "skip"); candidates = candidates.map { if (it.id == candidate.id) it.copy(status = "SKIPPED") else it } } }, modifier = Modifier.testTag("candidate-skip-${candidate.id}")) { Text("Skip") }
                        }
                    }
                }
            }
        }
        if (output.contains("QUEUED")) {
            Button(onClick = { scope.launch { val id = output.substringAfter("\"id\":\"").substringBefore("\""); output = repository.get(id, type) } }, modifier = Modifier.testTag("specialistRefresh")) { Text("Refresh result") }
        }
        Text(output.take(3_000), modifier = Modifier.testTag("specialistOutput"))
    }
}
