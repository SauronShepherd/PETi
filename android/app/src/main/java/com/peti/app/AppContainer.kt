package com.peti.app

/** Punto de composición de dependencias de la aplicación. */
class AppContainer(val environment: AppEnvironment = AppConfig.environment) {
    val petiViewModelFactory: () -> Phase0ViewModel = { Phase0ViewModel() }
}
