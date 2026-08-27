package com.peti.app
import android.content.Context
import com.peti.app.auth.PersistentLocalAuthRepository
import com.peti.app.pets.FakePetRepository
import com.peti.app.pets.FakeSpeciesRepository
import com.peti.app.analysis.FakeAnalysisRepository
import com.peti.app.funding.*
import com.peti.app.phase6.LocalPhase6Repository
import com.peti.app.records.LocalRecordsRepository
import com.peti.app.specialists.LocalSpecialistRepository
import com.peti.app.reports.LocalReportsRepository
import com.peti.app.future.LocalFutureRepository
object PlatformAppServicesImpl { @JvmStatic fun create(context: Context): AppServices = object : AppServices { override val auth = PersistentLocalAuthRepository(context); override val species = FakeSpeciesRepository(); override val pets = FakePetRepository(); override val analysis = FakeAnalysisRepository(); override val funding: FundingRepository = FakeFundingRepository(); override val premiumReconciliation = com.peti.app.billing.RejectingPremiumReconciliationPort(); override val mediaUpload = com.peti.app.media.MediaUploadCoordinator(com.peti.app.media.FakeMediaUploadRepository(), com.peti.app.media.SharedPreferencesUploadTaskStore(context), context); override val phase6 = LocalPhase6Repository(); override val records = LocalRecordsRepository(context); override val specialists = LocalSpecialistRepository(); override val reports = LocalReportsRepository(); override val future = LocalFutureRepository() } }
