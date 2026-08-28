package com.peti.app.future

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import kotlinx.coroutines.launch

@Composable
fun FuturePanel(repository: FutureRepository, petId: String, modifier: Modifier = Modifier) {
    val scope = rememberCoroutineScope(); var query by remember { mutableStateOf("") }; var output by remember { mutableStateOf("") }
    Card(modifier, colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), elevation = CardDefaults.cardElevation(1.dp)) {
      Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Perfil y registros", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
        Text("Toda la información de tu mascota, organizada y a tu alcance.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFEAF7F5))) {
          Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text("Información de tu mascota", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
            Text("Consulta el historial y conserva las fuentes importantes en un solo lugar.", color = MaterialTheme.colorScheme.onSurfaceVariant)
          }
        }
        Text("Accesos rápidos", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        OutlinedTextField(query, { query = it }, label = { Text("Buscar en el historial") }, modifier = Modifier.testTag("historySearch"))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button(onClick = { scope.launch { output = repository.search(query, petId) } }, modifier = Modifier.testTag("historySearchButton")) { Text("Buscar") }; OutlinedButton(onClick = { scope.launch { output = repository.export(petId) } }, modifier = Modifier.testTag("historyExport")) { Text("Exportar") } }
        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
          Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("Información segura", fontWeight = FontWeight.Bold)
            Text("Las respuestas se basan en fuentes guardadas y señalan cuando no existe una coincidencia.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(output.take(3_000), modifier = Modifier.testTag("historyOutput"))
          }
        }
      }
    }
}
