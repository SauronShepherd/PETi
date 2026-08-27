package com.peti.app.future

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

@Composable
fun FuturePanel(repository: FutureRepository, petId: String, modifier: Modifier = Modifier) {
    val scope = rememberCoroutineScope(); var query by remember { mutableStateOf("") }; var output by remember { mutableStateOf("") }
    Column(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Pet history tools", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(query, { query = it }, label = { Text("Search recorded history") }, modifier = Modifier.testTag("historySearch"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button(onClick = { scope.launch { output = repository.search(query, petId) } }, modifier = Modifier.testTag("historySearchButton")) { Text("Search") }; Button(onClick = { scope.launch { output = repository.export(petId) } }, modifier = Modifier.testTag("historyExport")) { Text("Export") } }
        Text("Assistant answers are grounded in saved sources and may say when no source matches.")
        Text(output.take(3_000), modifier = Modifier.testTag("historyOutput"))
    }
}
