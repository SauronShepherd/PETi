package com.peti.app.funding

enum class OperationType { PETI_CHECK, AI_PHOTO_STANDARD, AI_VIDEO_STANDARD, AI_AUDIO_STANDARD, AI_DOCUMENT_EXTRACTION, AI_SPECIALIST_STANDARD, MEDIA_RETENTION_UNIT }
data class FundingQuote(val operationType: OperationType, val requiredCredits: Int, val availableCredits: Int, val currentlyFundable: Boolean, val additionalCreditsRequired: Int, val rewardedAdAvailable: Boolean)
data class CreditSummary(val availableCredits: Int, val reservedCredits: Int)
data class RewardIntent(val id: String, val nonce: String, val expectedCreditAmount: Int, val status: String)

interface RewardedAdGateway { suspend fun show(intent: RewardIntent): Boolean }

class FakeRewardedAdGateway(private val available: Boolean = false) : RewardedAdGateway {
    override suspend fun show(intent: RewardIntent): Boolean = available
}

class UnavailableRewardedAdGateway : RewardedAdGateway {
    override suspend fun show(intent: RewardIntent): Boolean = false
}
