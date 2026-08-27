package com.peti.app

import com.peti.app.funding.FakeFundingRepository
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test

class FundingRepositoryTest {
    @Test fun fakeRewardIntentIsIdempotent() = runBlocking {
        val repository = FakeFundingRepository()
        assertEquals(3, repository.getCredits().availableCredits)
        assertEquals("GRANTED", repository.rewardIntentStatus("intent-1"))
        assertEquals(4, repository.getCredits().availableCredits)
        assertEquals("GRANTED", repository.rewardIntentStatus("intent-1"))
        assertEquals(4, repository.getCredits().availableCredits)
    }
}
