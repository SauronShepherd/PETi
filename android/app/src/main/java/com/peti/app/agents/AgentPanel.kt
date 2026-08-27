package com.peti.app.agents

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

@Composable
fun AgentPanel(repository: AgentRepository, petId: String, modifier: Modifier = Modifier) {
    val scope = rememberCoroutineScope(); var goal by remember { mutableStateOf("") }; var runId by remember { mutableStateOf<String?>(null) }; var output by remember { mutableStateOf("") }
    Column(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Ask PETi", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(goal, { goal = it }, label = { Text("What should PETi review?") }, modifier = Modifier.testTag("agentGoal"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { scope.launch { output = repository.createRun(petId, goal, null); runId = output } }, modifier = Modifier.testTag("agentStart")) { Text("Start") }
            runId?.let { id -> Button(onClick = { scope.launch { output = repository.getRun(id) } }, modifier = Modifier.testTag("agentRefresh")) { Text("Refresh") }; OutlinedButton(onClick = { scope.launch { output = repository.cancelRun(id) } }, modifier = Modifier.testTag("agentCancel")) { Text("Cancel") } }
        }
        Text("PETi shows evidence, waiting states and safe limitations explicitly.")
        Text(output.take(4_000), modifier = Modifier.testTag("agentOutput"))
    }
}
