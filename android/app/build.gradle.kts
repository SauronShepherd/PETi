plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.google.dagger.hilt.android")
    id("org.jetbrains.kotlin.kapt")
}
if (file("google-services.json").exists()) {
    apply(plugin = "com.google.gms.google-services")
}
val releaseBuildRequested = gradle.startParameter.taskNames.any { it.contains("Release", ignoreCase = true) }
fun releaseInput(name: String): String =
    providers.gradleProperty(name).orElse(providers.environmentVariable(name)).orNull
        ?: if (releaseBuildRequested) error("Missing required release input: $name") else ""
val releaseAdmobAppId = releaseInput("PETI_ADMOB_APP_ID")
val releaseAdmobRewardedUnitId = releaseInput("PETI_ADMOB_REWARDED_AD_UNIT_ID")
val releaseApiBaseUrl = releaseInput("PETI_RELEASE_API_BASE_URL")
val googleWebClientId = providers.gradleProperty("PETI_GOOGLE_WEB_CLIENT_ID")
    .orElse(providers.environmentVariable("PETI_GOOGLE_WEB_CLIENT_ID"))
    .orElse(if (releaseBuildRequested) error("Missing required release input: PETI_GOOGLE_WEB_CLIENT_ID") else "")
    .get()
val internalApiBaseUrl = providers.gradleProperty("PETI_INTERNAL_API_BASE_URL")
    .orElse(providers.environmentVariable("PETI_INTERNAL_API_BASE_URL"))
    .orElse("https://peti-api-dev-g2vgrtwnqq-ew.a.run.app")
    .get()
android { namespace="com.peti.app"; compileSdk=36
    defaultConfig { applicationId="com.peti.app"; minSdk=26; targetSdk=36; versionCode=1; versionName="1.0.0"; testInstrumentationRunner="androidx.test.runner.AndroidJUnitRunner" }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    buildTypes {
        getByName("debug") {
            applicationIdSuffix=".debug"
            manifestPlaceholders["admobAppId"] = "ca-app-pub-3940256099942544~3347511713"
            buildConfigField("String", "PETI_ENVIRONMENT", "\"LOCAL\"")
            buildConfigField("String", "PETI_API_BASE_URL", "\"http://10.0.2.2:8000\"")
            buildConfigField("String", "PETI_ADMOB_REWARDED_AD_UNIT_ID", "\"ca-app-pub-3940256099942544/5224354917\"")
            buildConfigField("String", "PETI_GOOGLE_WEB_CLIENT_ID", "\"$googleWebClientId\"")
        }
        create("internal") {
            initWith(getByName("debug"))
            applicationIdSuffix = null
            isDebuggable = false
            isMinifyEnabled = false
            manifestPlaceholders["admobAppId"] = "ca-app-pub-3940256099942544~3347511713"
            buildConfigField("String", "PETI_ENVIRONMENT", "\"DEV\"")
            buildConfigField("String", "PETI_API_BASE_URL", "\"$internalApiBaseUrl\"")
            buildConfigField("String", "PETI_ADMOB_REWARDED_AD_UNIT_ID", "\"ca-app-pub-3940256099942544/5224354917\"")
            buildConfigField("String", "PETI_GOOGLE_WEB_CLIENT_ID", "\"$googleWebClientId\"")
        }
        getByName("release") {
            isMinifyEnabled=true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            manifestPlaceholders["admobAppId"] = releaseAdmobAppId
            buildConfigField("String", "PETI_ENVIRONMENT", "\"PRODUCTION\"")
            buildConfigField("String", "PETI_API_BASE_URL", "\"$releaseApiBaseUrl\"")
            buildConfigField("String", "PETI_ADMOB_REWARDED_AD_UNIT_ID", "\"$releaseAdmobRewardedUnitId\"")
            buildConfigField("String", "PETI_GOOGLE_WEB_CLIENT_ID", "\"$googleWebClientId\"")
        }
    }
    buildFeatures { compose=true; buildConfig=true }
    lint { abortOnError=true }
    testOptions {
        managedDevices {
            devices {
                create<com.android.build.api.dsl.ManagedVirtualDevice>("phase0Api35") {
                    device = "Pixel 2"
                    apiLevel = 35
                    systemImageSource = "aosp"
                }
            }
        }
    }
}
// The local debug variant deliberately uses applicationId `com.peti.app.debug`.
// The checked-in Firebase config is for the real/internal package, so keep
// Google Services processing enabled for internal/release and skip only debug.
tasks.matching { it.name == "processDebugGoogleServices" }.configureEach {
    enabled = false
}
dependencies {
    implementation(project(":features:funding"))
    implementation(platform("androidx.compose:compose-bom:2024.12.01"))
    implementation("androidx.activity:activity-compose:1.10.0")
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.work:work-runtime-ktx:2.10.0")
    implementation("androidx.camera:camera-core:1.4.1")
    implementation("androidx.camera:camera-camera2:1.4.1")
    implementation("androidx.camera:camera-lifecycle:1.4.1")
    implementation("androidx.camera:camera-video:1.4.1")
    implementation("androidx.camera:camera-view:1.4.1")
    implementation("com.google.guava:guava:33.3.1-android")
    implementation("com.android.billingclient:billing-ktx:7.1.1")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("com.google.dagger:hilt-android:2.52")
    kapt("com.google.dagger:hilt-compiler:2.52")
    implementation("androidx.credentials:credentials:1.5.0")
    implementation("androidx.credentials:credentials-play-services-auth:1.5.0")
    implementation("com.google.android.libraries.identity.googleid:googleid:1.1.1")
    implementation("com.google.firebase:firebase-auth:24.0.1")
    implementation("com.google.firebase:firebase-messaging:24.1.0")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2024.12.01"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
