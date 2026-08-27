package com.peti.app

/** Minimal DI composition root for Phase 0; production adapters are added in later phases. */
class AppContainer(val environment: AppEnvironment = AppConfig.environment) {
    val phase0ViewModelFactory: () -> Phase0ViewModel = { Phase0ViewModel() }
}
