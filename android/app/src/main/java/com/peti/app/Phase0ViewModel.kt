package com.peti.app

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class Phase0UiState(val environment: AppEnvironment, val backendReachable: Boolean = false)

class Phase0ViewModel : ViewModel() {
    private val mutableState = MutableStateFlow(Phase0UiState(AppConfig.environment))
    val state: StateFlow<Phase0UiState> = mutableState.asStateFlow()
}
