package com.peti.app.billing

import android.app.Activity
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.ProductDetailsResponseListener
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesUpdatedListener
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import com.peti.app.auth.AccessTokenProvider
import com.peti.app.auth.CorrelationIds
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

data class PremiumProduct(val productId: String, val title: String, val formattedPrice: String)

interface PremiumReconciliationPort {
    suspend fun reconcile(productId: String, purchaseToken: String): Boolean
}

class ApiPremiumReconciliationPort(
    private val baseUrl: String,
    private val tokens: AccessTokenProvider,
) : PremiumReconciliationPort {
    override suspend fun reconcile(productId: String, purchaseToken: String): Boolean {
        val body = "{\"product_id\":\"${productId.jsonEscaped()}\",\"purchase_token\":\"${purchaseToken.jsonEscaped()}\"}"
        val connection = (URL(baseUrl + "/v1/billing/google-play/reconcile").openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"; connectTimeout = 10_000; readTimeout = 10_000
            setRequestProperty("Accept", "application/json")
            setRequestProperty("Content-Type", "application/json")
            setRequestProperty("X-Correlation-ID", CorrelationIds.next())
            tokens.getAccessToken(false)?.let { setRequestProperty("Authorization", "Bearer $it") }
            doOutput = true; outputStream.use { it.write(body.toByteArray()) }
        }
        val responseCode = connection.responseCode
        (if (responseCode in 200..299) connection.inputStream else connection.errorStream)?.use { it.readBytes() }
        return responseCode in 200..299
    }
    private fun String.jsonEscaped() = replace("\\", "\\\\").replace("\"", "\\\"")
}

class RejectingPremiumReconciliationPort : PremiumReconciliationPort {
    override suspend fun reconcile(productId: String, purchaseToken: String): Boolean = false
}

/** Play Billing client boundary; the backend remains the entitlement authority. */
class PlayBillingClientGateway(
    activity: Activity,
    private val reconciliation: PremiumReconciliationPort,
) : ProductDetailsResponseListener, PurchasesUpdatedListener {
    private val client = BillingClient.newBuilder(activity)
        .setListener(this)
        .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
        .build()
    private val products = mutableMapOf<String, ProductDetails>()
    private var purchaseResult: ((Boolean) -> Unit)? = null

    suspend fun connect(): Boolean = suspendCancellableCoroutine { continuation ->
        client.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(result: BillingResult) {
                if (result.responseCode == BillingClient.BillingResponseCode.OK) queryProducts()
                if (continuation.isActive) continuation.resume(result.responseCode == BillingClient.BillingResponseCode.OK)
            }
            override fun onBillingServiceDisconnected() = Unit
        })
    }

    fun queryProducts() {
        val params = QueryProductDetailsParams.newBuilder().setProductList(
            listOf("peti_premium_monthly", "peti_premium_yearly").map {
                QueryProductDetailsParams.Product.newBuilder()
                    .setProductId(it).setProductType(BillingClient.ProductType.SUBS).build()
            },
        ).build()
        client.queryProductDetailsAsync(params, this)
    }

    fun availableProducts(): List<PremiumProduct> = products.values.mapNotNull { detail ->
        detail.subscriptionOfferDetails?.firstOrNull()?.pricingPhases?.pricingPhaseList?.firstOrNull()?.let {
            PremiumProduct(detail.productId, detail.title, it.formattedPrice)
        }
    }

    suspend fun purchase(activity: Activity, productId: String): Boolean = suspendCancellableCoroutine { continuation ->
        val detail = products[productId] ?: run { continuation.resume(false); return@suspendCancellableCoroutine }
        val offer = detail.subscriptionOfferDetails?.firstOrNull() ?: run { continuation.resume(false); return@suspendCancellableCoroutine }
        purchaseResult = { success -> if (continuation.isActive) continuation.resume(success) }
        val params = BillingFlowParams.ProductDetailsParams.newBuilder()
            .setProductDetails(detail).setOfferToken(offer.offerToken).build()
        val result = client.launchBillingFlow(activity, BillingFlowParams.newBuilder().setProductDetailsParamsList(listOf(params)).build())
        if (result.responseCode != BillingClient.BillingResponseCode.OK) {
            purchaseResult = null
            continuation.resume(false)
        }
    }

    override fun onProductDetailsResponse(result: BillingResult, details: MutableList<ProductDetails>) {
        if (result.responseCode == BillingClient.BillingResponseCode.OK) details.forEach { products[it.productId] = it }
    }

    override fun onPurchasesUpdated(result: BillingResult, purchases: MutableList<Purchase>?) {
        val accepted = result.responseCode == BillingClient.BillingResponseCode.OK && !purchases.isNullOrEmpty()
        if (!accepted) { purchaseResult?.invoke(false); purchaseResult = null; return }
        val purchase = purchases!!.firstOrNull() ?: run { purchaseResult?.invoke(false); purchaseResult = null; return }
        CoroutineScope(Dispatchers.Main.immediate).launch {
            val success = purchase.products.firstOrNull()?.let { reconciliation.reconcile(it, purchase.purchaseToken) } == true
            purchaseResult?.invoke(success); purchaseResult = null
        }
    }

    fun restorePurchases() {
        client.queryPurchasesAsync(QueryPurchasesParams.newBuilder().setProductType(BillingClient.ProductType.SUBS).build()) { result, purchases ->
            if (result.responseCode == BillingClient.BillingResponseCode.OK) purchases.forEach { purchase ->
                purchase.products.firstOrNull()?.let { product -> CoroutineScope(Dispatchers.Main.immediate).launch { reconciliation.reconcile(product, purchase.purchaseToken) } }
            }
        }
    }

    fun close() { client.endConnection() }
}
