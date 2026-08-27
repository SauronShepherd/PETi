package com.peti.app.funding

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay

data class FundingUiState(val summary: CreditSummary? = null, val quote: FundingQuote? = null, val status: String = "", val loading: Boolean = false, val error: String? = null)

class FundingViewModel(private val repository: FundingRepository, private val ads: RewardedAdGateway) : ViewModel() {
    private val _state = MutableStateFlow(FundingUiState())
    val state: StateFlow<FundingUiState> = _state.asStateFlow()
    private var lastOperation: OperationType = OperationType.PETI_CHECK
    fun refresh() = viewModelScope.launch { runCatching { repository.getCredits() }.onSuccess { _state.value = _state.value.copy(summary = it, error = null) }.onFailure { _state.value = _state.value.copy(error = it.message) } }
    fun request(operation: OperationType) = viewModelScope.launch {
        lastOperation = operation
        _state.value = _state.value.copy(loading = true, error = null)
        runCatching { repository.quote(operation) }.onSuccess { quote -> _state.value = _state.value.copy(quote = quote, loading = false, status = if (quote.currentlyFundable) "Funded" else "Funding required") }.onFailure { _state.value = _state.value.copy(loading = false, error = it.message) }
    }
    fun watchAdAndRefresh() = viewModelScope.launch {
        val intent = runCatching { repository.createRewardIntent() }.getOrElse { _state.value = _state.value.copy(error = it.message); return@launch }
        _state.value = _state.value.copy(status = "Showing rewarded ad…")
        if (!ads.show(intent)) { _state.value = _state.value.copy(status = "Ad unavailable"); return@launch }
        _state.value = _state.value.copy(status = "Verifying reward…")
        runCatching {
            repeat(15) {
                if (repository.rewardIntentStatus(intent.id) == "GRANTED") return@runCatching
                delay(2_000)
            }
            error("Reward verification is still pending")
        }.onSuccess {
            refresh()
            request(lastOperation)
        }.onFailure { _state.value = _state.value.copy(error = it.message, status = "Reward not yet verified") }
    }

    suspend fun reserve(operation: OperationType, operationRequestId: String, idempotencyKey: String): String {
        _state.value = _state.value.copy(loading = true, error = null, status = "Reserving credit…")
        return runCatching { repository.reserve(operation, operationRequestId, idempotencyKey) }
            .onSuccess { _state.value = _state.value.copy(loading = false, status = "Credit reserved") }
            .onFailure { _state.value = _state.value.copy(loading = false, error = it.message, status = "") }
            .getOrThrow()
    }
}

class FakeFundingRepository : FundingRepository {
    private var balance = 3
    private val grantedIntents = mutableSetOf<String>()
    override suspend fun getCredits() = CreditSummary(balance, 0)
    override suspend fun quote(operationType: OperationType) = FundingQuote(operationType, 1, balance, balance >= 1, if (balance >= 1) 0 else 1, balance < 1)
    override suspend fun createRewardIntent() = RewardIntent("fake-intent", "fake-nonce", 1, "FAKE")
    override suspend fun rewardIntentStatus(intentId: String): String {
        if (grantedIntents.add(intentId)) balance += 1
        return "GRANTED"
    }
    override suspend fun reserve(operationType: OperationType, operationRequestId: String, idempotencyKey: String): String { if (balance < 1) error("FUNDING_REQUIRED"); balance -= 1; return "fake-reservation" }
}
