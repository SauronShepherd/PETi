package com.peti.app.funding

import com.peti.app.auth.AccessTokenProvider
import com.peti.app.auth.CorrelationIds
import java.net.HttpURLConnection
import java.net.URL

interface FundingRepository {
    suspend fun getCredits(): CreditSummary
    suspend fun quote(operationType: OperationType): FundingQuote
    suspend fun createRewardIntent(): RewardIntent
    suspend fun rewardIntentStatus(intentId: String): String
    suspend fun reserve(operationType: OperationType, operationRequestId: String, idempotencyKey: String): String
}

/** Backend-only economic API boundary. It deliberately has no local balance mutation method. */
class ApiFundingRepository(private val baseUrl: String, private val tokens: AccessTokenProvider) : FundingRepository {
    private suspend fun request(method: String, path: String, body: String? = null, idempotencyKey: String? = null): String {
        val c = (URL(baseUrl + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method; connectTimeout = 10_000; readTimeout = 10_000
            setRequestProperty("Accept", "application/json")
            setRequestProperty("X-Correlation-ID", CorrelationIds.next())
            tokens.getAccessToken(false)?.let { setRequestProperty("Authorization", "Bearer $it") }
            idempotencyKey?.let { setRequestProperty("Idempotency-Key", it) }
            if (body != null) { doOutput = true; setRequestProperty("Content-Type", "application/json"); outputStream.use { it.write(body.toByteArray()) } }
        }
        val text = (if (c.responseCode in 200..299) c.inputStream else c.errorStream).bufferedReader().readText()
        if (c.responseCode !in 200..299) error(text.ifBlank { "HTTP ${c.responseCode}" })
        return text
    }
    override suspend fun getCredits(): CreditSummary { val r = request("GET", "/v1/credits"); return CreditSummary(r.number("available_credits"), r.number("reserved_credits")) }
    override suspend fun quote(operationType: OperationType): FundingQuote { val r = request("POST", "/v1/funding/quote", "{\"operation_type\":\"$operationType\"}"); return FundingQuote(operationType, r.number("required_credits"), r.number("available_credits"), r.boolean("currently_fundable"), r.number("additional_credits_required"), r.boolean("rewarded_ad_available")) }
    override suspend fun createRewardIntent(): RewardIntent { val r = request("POST", "/v1/ads/reward-intents", "{\"provider\":\"ADMOB\"}"); return RewardIntent(r.string("id"), r.string("nonce"), r.number("expected_credit_amount"), r.string("status")) }
    override suspend fun rewardIntentStatus(intentId: String): String = request("GET", "/v1/ads/reward-intents/$intentId").string("status")
    override suspend fun reserve(operationType: OperationType, operationRequestId: String, idempotencyKey: String): String = request("POST", "/v1/funding/reservations", "{\"operation_type\":\"$operationType\",\"operation_request_id\":\"$operationRequestId\"}", idempotencyKey).string("id")
    private fun String.number(key: String) = Regex("\\\"$key\\\":(\\d+)").find(this)?.groupValues?.get(1)?.toInt() ?: 0
    private fun String.boolean(key: String) = Regex("\\\"$key\\\":(true|false)").find(this)?.groupValues?.get(1) == "true"
    private fun String.string(key: String) = Regex("\\\"$key\\\":\\\"([^\\\"]+)\\\"").find(this)?.groupValues?.get(1) ?: error("missing $key")
}
