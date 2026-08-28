package com.peti.app.agents

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

@Composable
fun AgentPanel(repository: AgentRepository, petId: String, modifier: Modifier = Modifier) {
    val scope = rememberCoroutineScope(); var goal by remember { mutableStateOf("") }; var runId by remember { mutableStateOf<String?>(null) }; var output by remember { mutableStateOf("") }
    Card(modifier, colors = CardDefaults.cardColors(containerColor = Color(0xFFEAF8F6)), elevation = CardDefaults.cardElevation(1.dp)) {
      Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Asistente PETi", style = MaterialTheme.typography.titleLarge, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold)
        Text("Conversa sobre la historia guardada de tu mascota con respuestas basadas en fuentes.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        OutlinedTextField(goal, { goal = it }, label = { Text("What should PETi review?") }, modifier = Modifier.testTag("agentGoal"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { scope.launch { output = repository.createRun(petId, goal, null); runId = output } }, modifier = Modifier.testTag("agentStart")) { Text("Start") }
            runId?.let { id -> Button(onClick = { scope.launch { output = repository.getRun(id) } }, modifier = Modifier.testTag("agentRefresh")) { Text("Refresh") }; OutlinedButton(onClick = { scope.launch { output = repository.cancelRun(id) } }, modifier = Modifier.testTag("agentCancel")) { Text("Cancel") } }
        }
        Text("PETi muestra la evidencia, los estados de espera y sus límites de seguridad.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(output.take(4_000), modifier = Modifier.testTag("agentOutput"))
      }
    }
}
