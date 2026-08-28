package com.peti.app.reports

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import com.peti.app.PetiPayloadCard

@Composable
fun ReportsPanel(repository: ReportsRepository, petId: String, modifier: Modifier = Modifier) {
    val scope = rememberCoroutineScope(); var output by remember { mutableStateOf("") }
    Card(modifier, colors = CardDefaults.cardColors(containerColor = Color(0xFFEAF8F6)), elevation = CardDefaults.cardElevation(1.dp)) {
      Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Resumen semanal PETi", style = MaterialTheme.typography.titleLarge, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold)
        Text("Un resumen claro de los datos registrados. No sustituye la atención veterinaria.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button(onClick = { scope.launch { output = repository.list(petId) } }, modifier = Modifier.testTag("reportsHistory")) { Text("Ver historial") }; Button(onClick = { scope.launch { output = repository.generate(petId) } }, modifier = Modifier.testTag("reportGenerate")) { Text("Generar resumen") } }
        PetiPayloadCard(output, "Genera el primer resumen semanal para ver la evolución.", Modifier.testTag("reportsOutput"))
      }
    }
}
