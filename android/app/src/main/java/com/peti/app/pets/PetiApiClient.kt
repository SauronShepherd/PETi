package com.peti.app.pets

import com.peti.app.auth.AccessTokenProvider
import com.peti.app.auth.CorrelationIds
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID
import com.peti.app.analysis.*

/** Minimal API adapter. Firestore is intentionally absent from Android. */
class PetiApiClient(private val baseUrl: String, private val tokens: AccessTokenProvider) : SpeciesRepository, PetRepository, AnalysisRepository {
    private suspend fun request(method: String, path: String, body: String? = null, idempotencyKey: String? = null): String {
        val connection = (URL(baseUrl + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method; connectTimeout = 10_000; readTimeout = 10_000; setRequestProperty("Accept", "application/json"); setRequestProperty("X-Correlation-ID", CorrelationIds.next())
            tokens.getAccessToken(false)?.let { setRequestProperty("Authorization", "Bearer $it") }
            idempotencyKey?.let { setRequestProperty("Idempotency-Key", it) }
            if (body != null) { doOutput = true; setRequestProperty("Content-Type", "application/json"); outputStream.use { it.write(body.toByteArray()) } }
        }
        val response = (if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream).bufferedReader().readText()
        if (connection.responseCode !in 200..299) error(response.ifBlank { "HTTP ${connection.responseCode}" })
        return response
    }
    override suspend fun listSpecies(): List<SpeciesSummary> = request("GET", "/v1/species").parseSpecies()
    override suspend fun listPets(): List<Pet> = request("GET", "/v1/pets").parsePets()
    override suspend fun createPet(displayName: String, species: String, idempotencyKey: String): Pet = request("POST", "/v1/pets", "{\"display_name\":\"${displayName.jsonEscaped()}\",\"species\":\"${species.jsonEscaped()}\"}", idempotencyKey).parsePet()
    override suspend fun updatePet(id: String, displayName: String): Pet = request("PATCH", "/v1/pets/$id", "{\"display_name\":\"${displayName.jsonEscaped()}\"}").parsePet()
    override suspend fun deletePet(id: String) { request("DELETE", "/v1/pets/$id") }
    override suspend fun create(animalId: String, mediaAssetIds: List<String>, fundingReservationId: String, idempotencyKey: String, userContext: String?): AnalysisJob {
        val media = mediaAssetIds.joinToString(",") { "\"${it.jsonEscaped()}\"" }
        val context = userContext?.let { "\"${it.jsonEscaped()}\"" } ?: "null"
        return request("POST", "/v1/pets/$animalId/checks", "{\"animal_id\":\"${animalId.jsonEscaped()}\",\"media_asset_ids\":[$media],\"user_context\":$context,\"funding_reservation_id\":\"${fundingReservationId.jsonEscaped()}\"}", idempotencyKey).parseAnalysisJob()
    }
    override suspend fun get(jobId: String): AnalysisJob = request("GET", "/v1/analyses/$jobId").parseAnalysisJob()
    override suspend fun listHistory(animalId: String): List<AnalysisJob> =
        request("GET", "/v1/pets/$animalId/checks").parseAnalysisJobs()
    private fun String.jsonEscaped() = replace("\\", "\\\\").replace("\"", "\\\"")
    private fun String.parsePet() = Pet(Regex("\"id\":\"([^\"]+)\"" ).find(this)!!.groupValues[1], Regex("\"owner_user_id\":\"([^\"]+)\"" ).find(this)!!.groupValues[1], Regex("\"species\":\"([^\"]+)\"" ).find(this)!!.groupValues[1], Regex("\"display_name\":\"([^\"]+)\"" ).find(this)!!.groupValues[1])
    private fun String.parsePets() = Regex("\\{[^{}]*\"id\":\"[^{}]+\\}").findAll(this).map { it.value.parsePet() }.toList()
    private fun String.parseSpecies() = Regex("\"species_code\":\"([^\"]+)\"[^{}]*\"display_name\":\"([^\"]+)\"").findAll(this).map { SpeciesSummary(it.groupValues[1], it.groupValues[2], true) }.toList()
    private fun String.parseAnalysisJob(): AnalysisJob {
        val id = Regex("\"id\":\"([^\"]+)\"").find(this)!!.groupValues[1]
        val animal = Regex("\"animal_id\":\"([^\"]+)\"").find(this)!!.groupValues[1]
        val type = Regex("\"analysis_type\":\"([^\"]+)\"").find(this)?.groupValues?.get(1) ?: "PETI_CHECK"
        val status = Regex("\"status\":\"([^\"]+)\"").find(this)!!.groupValues[1]
        val parsed = runCatching { AnalysisStatus.valueOf(status) }.getOrDefault(AnalysisStatus.FAILED_FINAL)
        val media = Regex("\\\"media_asset_ids\\\":\\[(.*?)\\]").find(this)?.groupValues?.get(1)
            ?.let { Regex("\\\"([^\\\"]+)\\\"").findAll(it).map { match -> match.groupValues[1] }.toList() }
            ?: emptyList()
        val result = parseAnalysisResult(id)
        return AnalysisJob(id, animal, type, parsed, media, result)
    }
    private fun String.parseAnalysisResult(jobId: String): AnalysisResult? {
        val marker = "\"result\":{"
        val start = indexOf(marker)
        if (start < 0) return null
        val section = substring(start)
        fun field(name: String): String =
            Regex("\\\"$name\\\":\\\"((?:\\\\.|[^\\\"])*)\\\"").find(section)?.groupValues?.get(1)?.jsonUnescaped() ?: ""
        val id = field("id")
        if (id.isEmpty()) return null
        val evidenceQuality = Regex("\\\"evidence_quality\\\":(?:\\\"([^\\\"]+)\\\"|\\{[^}]*\\\"level\\\":\\\"([^\\\"]+)\\\")").find(section)
            ?.let { it.groupValues[1].ifEmpty { it.groupValues[2] } } ?: "LOW"
        val limitations = Regex("\\\"limitations\\\":\\[(.*?)\\]").find(section)?.groupValues?.get(1)
            ?.let { Regex("\\\"([^\\\"]*)\\\"").findAll(it).map { match -> match.groupValues[1] }.toList() }
            ?: emptyList()
        val sourceMediaIds = Regex("\\\"source_media_ids\\\":\\[(.*?)\\]").find(section)?.groupValues?.get(1)
            ?.let { Regex("\\\"([^\\\"]+)\\\"").findAll(it).map { match -> match.groupValues[1] }.toList() }
            ?: emptyList()
        fun items(name: String): List<String> = Regex("\\\"$name\\\":\\[(.*?)\\]").find(section)?.groupValues?.get(1)
            ?.let { Regex("(?:\\\"text\\\":)?\\\"((?:\\\\.|[^\\\"])*)\\\"").findAll(it).map { match -> match.groupValues[1].jsonUnescaped() }.toList() }
            ?: emptyList()
        return AnalysisResult(id, jobId, field("summary"), field("safety_state"), field("provider"), field("provider_model"), evidenceQuality, limitations, sourceMediaIds, items("observations"), items("uncertainties"), items("possible_interpretations"), items("red_flags"), items("recommended_actions"))
    }
    private fun String.jsonUnescaped(): String = replace("\\\\\"", "\"").replace("\\\\\\\\", "\\\\").replace("\\\\n", "\n")
    private fun String.parseAnalysisJobs(): List<AnalysisJob> =
        topLevelObjects().map { it.parseAnalysisJob() }

    private fun String.topLevelObjects(): List<String> {
        val objects = mutableListOf<String>()
        var depth = 0
        var start = -1
        var quoted = false
        var escaped = false
        forEachIndexed { index, character ->
            if (quoted) {
                if (escaped) escaped = false
                else if (character == '\\') escaped = true
                else if (character == '"') quoted = false
                return@forEachIndexed
            }
            if (character == '"') quoted = true
            else if (character == '{') {
                if (depth == 0) start = index
                depth += 1
            } else if (character == '}') {
                depth -= 1
                if (depth == 0 && start >= 0) {
                    objects += substring(start, index + 1)
                    start = -1
                }
            }
        }
        return objects
    }
}
