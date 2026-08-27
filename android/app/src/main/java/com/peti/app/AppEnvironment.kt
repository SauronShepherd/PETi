package com.peti.app

enum class AppEnvironment(val apiBaseUrl: String, val fakeServices: Boolean) {
    LOCAL("http://10.0.2.2:8000", true),
    DEV("https://dev-api.peti.example", false),
    STAGING("https://staging-api.peti.example", false),
    PRODUCTION("https://api.peti.example", false)
}

object AppConfig {
    // Non-secret, build-variant configuration. Production credentials never live in the APK.
    val environment: AppEnvironment = runCatching {
        AppEnvironment.valueOf(BuildConfig.PETI_ENVIRONMENT)
    }.getOrDefault(AppEnvironment.LOCAL)
    val apiBaseUrl: String = BuildConfig.PETI_API_BASE_URL
}
