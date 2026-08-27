package com.peti.app

import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.peti.app.records.LocalRecordsRepository
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class LocalRecordsPersistenceTest {
    @Test
    fun recordsAndCandidateReviewSurviveRepositoryRecreation() = runBlocking {
        val context = ApplicationProvider.getApplicationContext<android.content.Context>()
        context.getSharedPreferences("peti_local_records", android.content.Context.MODE_PRIVATE).edit().clear().commit()
        val first = LocalRecordsRepository(context)
        val created = first.create("pet-1", "{\"title\":\"Visit\"}", "record-key-1")
        assertTrue(created.contains("local-record-"))
        first.extract(created.substringAfter("\"id\":\"").substringBefore("\""))

        val restarted = LocalRecordsRepository(context)
        val records = restarted.list("pet-1")
        assertTrue(records.contains("Visit"))
        val recordId = records.substringAfter("\"id\":\"").substringBefore("\"")
        val candidates = restarted.candidates(recordId)
        assertTrue(candidates.contains("PENDING_REVIEW"))
        val candidateId = candidates.substringAfter("\"id\":\"").substringBefore("\"")
        restarted.review(candidateId, "confirm")
        assertTrue(restarted.candidates(recordId).contains("CONFIRM"))
        restarted.delete(recordId, true)
        assertTrue(!LocalRecordsRepository(context).list("pet-1").contains(recordId))
        assertTrue(LocalRecordsRepository(context).candidates(recordId) == "[]")
        val accountData = LocalRecordsRepository(context)
        accountData.create("pet-2", "{\"title\":\"Private\"}", "record-key-2")
        accountData.clearLocalAccount()
        assertTrue(LocalRecordsRepository(context).list("pet-2") == "[]")
    }
}
