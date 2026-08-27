package com.peti.app.records

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import com.peti.app.auth.AccessTokenProvider
import com.peti.app.auth.CorrelationIds
import java.net.HttpURLConnection
import java.net.URL

interface RecordsRepository {
    suspend fun list(petId: String): String
    suspend fun create(petId: String, body: String, idempotencyKey: String): String
    suspend fun access(recordId: String): String
    suspend fun candidates(recordId: String): String
    suspend fun extract(recordId: String): String
    suspend fun review(candidateId: String, action: String, body: String? = null): String
    suspend fun deletionPreview(recordId: String): String
    suspend fun delete(recordId: String, confirmDependencies: Boolean): String
    suspend fun clearLocalAccount() {}
}

class ApiRecordsRepository(private val baseUrl: String, private val tokens: AccessTokenProvider) : RecordsRepository {
    private suspend fun request(method: String, path: String, body: String? = null, idempotencyKey: String? = null): String {
        val c = (URL(baseUrl + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method; connectTimeout = 10_000; readTimeout = 10_000
            setRequestProperty("Accept", "application/json")
            setRequestProperty("X-Correlation-ID", CorrelationIds.next())
            tokens.getAccessToken(false)?.let { setRequestProperty("Authorization", "Bearer $it") }
            idempotencyKey?.let { setRequestProperty("Idempotency-Key", it) }
            if (body != null) { doOutput = true; setRequestProperty("Content-Type", "application/json"); outputStream.use { it.write(body.toByteArray()) } }
        }
        val stream = if (c.responseCode in 200..299) c.inputStream else c.errorStream
        val text = stream.bufferedReader().use { it.readText() }
        if (c.responseCode !in 200..299) error(text.ifBlank { "HTTP ${c.responseCode}" })
        return text
    }
    override suspend fun list(petId: String) = request("GET", "/v1/pets/$petId/records")
    override suspend fun create(petId: String, body: String, idempotencyKey: String) = request("POST", "/v1/pets/$petId/records", body, idempotencyKey)
    override suspend fun access(recordId: String) = request("POST", "/v1/records/$recordId/access")
    override suspend fun candidates(recordId: String) = request("GET", "/v1/records/$recordId/candidate-facts")
    override suspend fun extract(recordId: String) = request("POST", "/v1/records/$recordId/extract", "{}")
    override suspend fun review(candidateId: String, action: String, body: String?) = request("POST", "/v1/candidate-facts/$candidateId/$action", body)
    override suspend fun deletionPreview(recordId: String) = request("GET", "/v1/records/$recordId/deletion-preview")
    override suspend fun delete(recordId: String, confirmDependencies: Boolean) = request("DELETE", "/v1/records/$recordId?confirm_dependencies=$confirmDependencies")
}

class LocalRecordsRepository(private val context: Context? = null) : RecordsRepository {
    private val prefs get() = context?.getSharedPreferences("peti_local_records", Context.MODE_PRIVATE)
    private fun load(name: String) = runCatching { JSONArray(prefs?.getString(name, "[]") ?: "[]") }.getOrDefault(JSONArray())
    private fun save(name: String, value: JSONArray) { prefs?.edit()?.putString(name, value.toString())?.apply() }

    override suspend fun list(petId: String): String {
        val result = JSONArray(); val all = load("records")
        for (i in 0 until all.length()) if (all.getJSONObject(i).optString("pet_id") == petId) result.put(all.getJSONObject(i))
        return result.toString()
    }

    override suspend fun create(petId: String, body: String, idempotencyKey: String): String {
        val all = load("records")
        for (i in 0 until all.length()) if (all.getJSONObject(i).optString("idempotency_key") == idempotencyKey) return all.getJSONObject(i).toString()
        val item = JSONObject(body).put("id", "local-record-${System.currentTimeMillis()}").put("pet_id", petId).put("idempotency_key", idempotencyKey)
        all.put(item); save("records", all); return item.toString()
    }

    override suspend fun access(recordId: String) = "{\"status\":\"LOCAL_ACCESS\",\"record_id\":\"$recordId\"}"

    override suspend fun candidates(recordId: String): String {
        val all = load("candidates"); val result = JSONArray()
        for (i in 0 until all.length()) if (all.getJSONObject(i).optString("record_id") == recordId) result.put(all.getJSONObject(i))
        return result.toString()
    }

    override suspend fun extract(recordId: String): String {
        val existing = JSONArray(candidates(recordId)); if (existing.length() == 0) {
            val all = load("candidates"); all.put(JSONObject().put("id", "local-candidate-$recordId").put("record_id", recordId).put("fact_type", "WEIGHT").put("candidate_value", "22.4").put("candidate_unit", "lb").put("status", "PENDING_REVIEW")); save("candidates", all)
        }
        return "{\"extraction_status\":\"REVIEW_REQUIRED\"}"
    }

    override suspend fun review(candidateId: String, action: String, body: String?): String {
        val all = load("candidates")
        for (i in 0 until all.length()) if (all.getJSONObject(i).optString("id") == candidateId) { all.getJSONObject(i).put("status", action.uppercase()); save("candidates", all); return all.getJSONObject(i).toString() }
        error("CANDIDATE_FACT_NOT_FOUND")
    }
    override suspend fun deletionPreview(recordId: String) = "{\"record_id\":\"$recordId\",\"dependent_documented_fact_count\":0}"
    override suspend fun delete(recordId: String, confirmDependencies: Boolean): String {
        val all = load("records"); val kept = JSONArray()
        for (i in 0 until all.length()) if (all.getJSONObject(i).optString("id") != recordId) kept.put(all.getJSONObject(i))
        save("records", kept)
        val candidates = load("candidates"); val candidateKept = JSONArray()
        for (i in 0 until candidates.length()) if (candidates.getJSONObject(i).optString("record_id") != recordId) candidateKept.put(candidates.getJSONObject(i))
        save("candidates", candidateKept)
        return "{}"
    }
    override suspend fun clearLocalAccount() {
        // Sign-out is a privacy boundary: complete the wipe before auth state
        // changes, so a fast account switch cannot observe stale records.
        prefs?.edit()?.remove("records")?.remove("candidates")?.commit()
    }
}
