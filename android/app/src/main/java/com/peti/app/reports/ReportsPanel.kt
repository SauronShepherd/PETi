package com.peti.app.reports

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

@Composable
fun ReportsPanel(repository: ReportsRepository, petId: String, modifier: Modifier = Modifier) {
    val scope = rememberCoroutineScope(); var output by remember { mutableStateOf("") }
    Column(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Weekly PETi Report", style = MaterialTheme.typography.titleMedium)
        Text("Reports summarize recorded evidence and do not replace veterinary care.")
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button(onClick = { scope.launch { output = repository.list(petId) } }, modifier = Modifier.testTag("reportsHistory")) { Text("History") }; Button(onClick = { scope.launch { output = repository.generate(petId) } }, modifier = Modifier.testTag("reportGenerate")) { Text("Generate") } }
        Text(output.take(3_000), modifier = Modifier.testTag("reportsOutput"))
    }
}
