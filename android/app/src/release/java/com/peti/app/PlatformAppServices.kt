package com.peti.app

import android.content.Context
import com.google.firebase.auth.FirebaseAuth
import com.peti.app.auth.AuthRepository
import com.peti.app.auth.FirebaseCredentialAuthRepository
import com.peti.app.pets.PetiApiClient
import com.peti.app.pets.PetRepository
import com.peti.app.pets.SpeciesRepository
import com.peti.app.analysis.AnalysisRepository
import com.peti.app.funding.FundingRepository
import com.peti.app.funding.ApiFundingRepository
import com.peti.app.media.ApiMediaUploadRepository
import com.peti.app.media.MediaUploadCoordinator
import com.peti.app.media.SharedPreferencesUploadTaskStore
import com.peti.app.phase6.ApiPhase6Repository
import com.peti.app.phase6.CachedPhase6Repository
import com.peti.app.records.ApiRecordsRepository
import com.peti.app.specialists.ApiSpecialistRepository
import com.peti.app.reports.ApiReportsRepository
import com.peti.app.future.ApiFutureRepository

object PlatformAppServicesImpl {
    @JvmStatic fun create(context: Context): AppServices {
        val auth: AuthRepository = FirebaseCredentialAuthRepository(context, BuildConfig.PETI_GOOGLE_WEB_CLIENT_ID)
        val api = PetiApiClient(AppConfig.apiBaseUrl, auth)
        return object : AppServices { override val auth = auth; override val species: SpeciesRepository = api; override val pets: PetRepository = api; override val analysis: AnalysisRepository = api; override val funding: FundingRepository = ApiFundingRepository(AppConfig.apiBaseUrl, auth); override val premiumReconciliation = com.peti.app.billing.ApiPremiumReconciliationPort(AppConfig.apiBaseUrl, auth); override val mediaUpload = MediaUploadCoordinator(ApiMediaUploadRepository(AppConfig.apiBaseUrl, auth, context.contentResolver), SharedPreferencesUploadTaskStore(context), context); override val phase6 = CachedPhase6Repository(ApiPhase6Repository(AppConfig.apiBaseUrl, auth), auth, context); override val records = ApiRecordsRepository(AppConfig.apiBaseUrl, auth); override val specialists = ApiSpecialistRepository(AppConfig.apiBaseUrl, auth); override val reports = ApiReportsRepository(AppConfig.apiBaseUrl, auth); override val future = ApiFutureRepository(AppConfig.apiBaseUrl, auth) }
    }
}
