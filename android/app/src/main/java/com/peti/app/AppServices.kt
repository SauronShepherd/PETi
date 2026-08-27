package com.peti.app

import android.content.Context
import com.peti.app.auth.AuthRepository
import com.peti.app.pets.PetRepository
import com.peti.app.pets.SpeciesRepository
import com.peti.app.analysis.AnalysisRepository
import com.peti.app.funding.FundingRepository
import com.peti.app.media.MediaUploadCoordinator
import com.peti.app.phase6.Phase6Repository
import com.peti.app.records.RecordsRepository
import com.peti.app.specialists.SpecialistRepository
import com.peti.app.reports.ReportsRepository
import com.peti.app.future.FutureRepository
import com.peti.app.billing.PremiumReconciliationPort

interface AppServices { val auth: AuthRepository; val species: SpeciesRepository; val pets: PetRepository; val analysis: AnalysisRepository; val funding: FundingRepository; val premiumReconciliation: PremiumReconciliationPort; val mediaUpload: MediaUploadCoordinator; val phase6: Phase6Repository; val records: RecordsRepository; val specialists: SpecialistRepository; val reports: ReportsRepository; val future: FutureRepository }
fun createAppServices(context: Context): AppServices {
    val implementation = Class.forName("com.peti.app.PlatformAppServicesImpl").getDeclaredMethod("create", Context::class.java)
    return implementation.invoke(null, context) as AppServices
}
