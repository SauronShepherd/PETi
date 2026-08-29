package com.peti.app

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.peti.app.pets.Pet

private val Ink = Color(0xFF173E43)
private val Teal = Color(0xFF0AA69D)
private val Mint = Color(0xFFE6F7F4)
private val Peach = Color(0xFFFFEEE8)

@Composable
fun PetiDashboard(pet: Pet, onScan: () -> Unit, onHistory: () -> Unit, modifier: Modifier = Modifier) {
    Column(modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column { Text("¡Hola! 👋", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, color = Ink); Text("Aquí está el resumen de hoy.", color = MaterialTheme.colorScheme.onSurfaceVariant) }
            Surface(shape = CircleShape, color = Peach, modifier = Modifier.size(44.dp)) { Box(contentAlignment = Alignment.Center) { Text("♧", color = Teal, style = MaterialTheme.typography.titleLarge) } }
        }
        Card(shape = MaterialTheme.shapes.large, colors = CardDefaults.cardColors(containerColor = Color.White), elevation = CardDefaults.cardElevation(1.dp)) {
            Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Surface(shape = CircleShape, color = Color(0xFFFFCFC5), modifier = Modifier.size(76.dp)) { Box(contentAlignment = Alignment.Center) { Text("🐶", style = MaterialTheme.typography.headlineMedium) } }
                Spacer(Modifier.width(14.dp)); Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) { Text("Mi mascota", color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.labelLarge); Text(pet.displayName, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = Ink); Text("${pet.species.lowercase().replaceFirstChar { it.uppercase() }} · ${if (pet.profileComplete) "Perfil completo" else "Completar perfil"}", color = if (pet.profileComplete) Teal else MaterialTheme.colorScheme.secondary, fontWeight = FontWeight.SemiBold) }; Text("⌄", style = MaterialTheme.typography.headlineSmall, color = Ink)
            }
        }
        if (pet.profileComplete) Card(shape = MaterialTheme.shapes.large, colors = CardDefaults.cardColors(containerColor = Color.White), elevation = CardDefaults.cardElevation(1.dp)) {
            Column(Modifier.fillMaxWidth().padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) { Text("Puntuación de salud", color = MaterialTheme.colorScheme.onSurfaceVariant); Row(verticalAlignment = Alignment.Bottom) { Text("92", style = MaterialTheme.typography.displaySmall, fontWeight = FontWeight.Bold, color = Ink); Text(" / 100", modifier = Modifier.padding(bottom = 8.dp), color = MaterialTheme.colorScheme.onSurfaceVariant); Spacer(Modifier.weight(1f)); Text("♡", style = MaterialTheme.typography.displaySmall, color = Teal) }; Text("¡Excelente! ${pet.displayName} está en muy buen estado.", color = Teal, fontWeight = FontWeight.SemiBold); LinearProgressIndicator(progress = { .92f }, modifier = Modifier.fillMaxWidth().height(8.dp), color = Teal, trackColor = Mint) }
        }
        if (pet.profileComplete) Card(shape = MaterialTheme.shapes.large, colors = CardDefaults.cardColors(containerColor = Peach), elevation = CardDefaults.cardElevation(0.dp)) { Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) { Text("♧", style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.secondary); Spacer(Modifier.width(12.dp)); Column(Modifier.weight(1f)) { Text("Próximo recordatorio", color = MaterialTheme.colorScheme.secondary, fontWeight = FontWeight.Bold); Text("Revisa los cuidados de ${pet.displayName}", color = Ink); Text("Hoy · 18:00", color = MaterialTheme.colorScheme.onSurfaceVariant) }; Text("›", style = MaterialTheme.typography.headlineMedium, color = Ink) } }
        if (!pet.profileComplete) Card(shape = MaterialTheme.shapes.large, colors = CardDefaults.cardColors(containerColor = Mint), elevation = CardDefaults.cardElevation(0.dp)) { Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) { Text("Completa el perfil de ${pet.displayName}", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = Ink); Text("Añade raza, edad y peso para personalizar sus cuidados. Todavía no mostramos métricas hasta tener datos reales.", color = MaterialTheme.colorScheme.onSurfaceVariant) } }
        Text("Resumen de actividad", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = Ink)
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) { Metric("♧", "Paseos", "1 / 2", "completados", Mint, Modifier.weight(1f)); Metric("⌁", "Comidas", "2 / 2", "completadas", Color(0xFFFFF3E6), Modifier.weight(1f)); Metric("◔", "Sueño", "8.2 h", "bien", Color(0xFFF1EEFF), Modifier.weight(1f)) }
        Card(shape = MaterialTheme.shapes.large, colors = CardDefaults.cardColors(containerColor = Mint), elevation = CardDefaults.cardElevation(0.dp)) { Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) { Text("✦", style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.secondary); Spacer(Modifier.width(12.dp)); Column(Modifier.weight(1f)) { Text("Mejor siguiente paso", fontWeight = FontWeight.Bold, color = Ink); Text("Observa cómo se encuentra tu mascota hoy.", color = MaterialTheme.colorScheme.onSurfaceVariant) }; Text("›", style = MaterialTheme.typography.headlineMedium, color = Ink) } }
        Button(onClick = onScan, modifier = Modifier.fillMaxWidth().height(54.dp), shape = MaterialTheme.shapes.medium) { Text("Analizar a ${pet.displayName}", fontWeight = FontWeight.Bold) }
        OutlinedButton(onClick = onHistory, modifier = Modifier.fillMaxWidth().height(52.dp), shape = MaterialTheme.shapes.medium) { Text("Ver historial y registros") }
    }
}

@Composable
private fun Metric(icon: String, title: String, value: String, caption: String, color: Color, modifier: Modifier) { Card(modifier, shape = MaterialTheme.shapes.medium, colors = CardDefaults.cardColors(containerColor = color), elevation = CardDefaults.cardElevation(0.dp)) { Column(Modifier.padding(11.dp), verticalArrangement = Arrangement.spacedBy(3.dp)) { Text(icon, color = Teal, style = MaterialTheme.typography.titleLarge); Text(title, color = Ink, style = MaterialTheme.typography.labelLarge); Text(value, color = Ink, fontWeight = FontWeight.Bold); Text(caption, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.labelSmall) } } }
