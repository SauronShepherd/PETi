package com.peti.app.funding

import android.app.Activity
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.MobileAds
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.rewarded.RewardItem
import com.google.android.gms.ads.rewarded.RewardedAd
import com.google.android.gms.ads.rewarded.RewardedAdLoadCallback
import com.google.android.gms.ads.rewarded.ServerSideVerificationOptions
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

enum class OperationType { PETI_CHECK, AI_PHOTO_STANDARD, AI_VIDEO_STANDARD, AI_AUDIO_STANDARD, AI_DOCUMENT_EXTRACTION, AI_SPECIALIST_STANDARD, MEDIA_RETENTION_UNIT }
data class FundingQuote(val operationType: OperationType, val requiredCredits: Int, val availableCredits: Int, val currentlyFundable: Boolean, val additionalCreditsRequired: Int, val rewardedAdAvailable: Boolean)
data class CreditSummary(val availableCredits: Int, val reservedCredits: Int)
data class RewardIntent(val id: String, val nonce: String, val expectedCreditAmount: Int, val status: String)

interface RewardedAdGateway { suspend fun show(intent: RewardIntent): Boolean }

class FakeRewardedAdGateway(private val available: Boolean = true) : RewardedAdGateway {
    override suspend fun show(intent: RewardIntent): Boolean = available
}

class UnavailableRewardedAdGateway : RewardedAdGateway {
    override suspend fun show(intent: RewardIntent): Boolean = false
}

class AdMobRewardedAdGateway(private val activity: Activity, private val adUnitId: String) : RewardedAdGateway {
    override suspend fun show(intent: RewardIntent): Boolean = suspendCancellableCoroutine { continuation ->
        if (adUnitId.isBlank() || adUnitId.startsWith("REQUIRED_")) {
            continuation.resume(false)
            return@suspendCancellableCoroutine
        }
        MobileAds.initialize(activity)
        RewardedAd.load(activity, adUnitId, AdRequest.Builder().build(), object : RewardedAdLoadCallback() {
            override fun onAdFailedToLoad(error: LoadAdError) { if (continuation.isActive) continuation.resume(false) }
            override fun onAdLoaded(ad: RewardedAd) {
                ad.setServerSideVerificationOptions(ServerSideVerificationOptions.Builder().setCustomData(intent.id).build())
                ad.show(activity) { _: RewardItem -> if (continuation.isActive) continuation.resume(true) }
            }
        })
    }
}
