package com.peti.app

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import org.json.JSONArray
import org.json.JSONObject

/** User-facing summary for API payloads; raw JSON is not the primary UI. */
@Composable
fun PetiPayloadCard(raw: String, emptyLabel: String, modifier: Modifier = Modifier) {
    val lines = runCatching {
        val value = raw.trim()
        if (value.startsWith("[")) {
            val array = JSONArray(value)
            if (array.length() == 0) listOf(emptyLabel) else buildList {
                add("${array.length()} elementos guardados")
                for (index in 0 until minOf(array.length(), 4)) {
                    val item = array.optJSONObject(index) ?: continue
                    val title = item.optString("title").ifBlank { item.optString("fact_type").ifBlank { item.optString("id") } }
                    val state = item.optString("status").ifBlank { item.optString("extraction_status") }
                    add(listOf(title, state).filter { it.isNotBlank() }.joinToString(" · "))
                }
            }
        } else {
            val objectValue = JSONObject(value)
            listOf("Estado: ${objectValue.optString("status").ifBlank { objectValue.optString("generation_status").ifBlank { "Disponible" } }}")
        }
    }.getOrDefault(listOf(raw.take(500)))
    Card(modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = Color(0xFFF8FCFB))) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            lines.forEachIndexed { index, line ->
                Text(line, style = if (index == 0) MaterialTheme.typography.titleSmall else MaterialTheme.typography.bodyMedium,
                    color = if (index == 0) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface)
            }
        }
    }
}
