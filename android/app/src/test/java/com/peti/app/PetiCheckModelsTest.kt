package com.peti.app

import com.peti.app.analysis.*
import org.junit.Assert.assertEquals
import org.junit.Test

class PetiCheckModelsTest {
    @Test fun insufficientEvidenceIsACompletedCustomerState() {
        val result = com.peti.app.analysis.AnalysisResult("r", "j", "Not enough evidence", "INSUFFICIENT_EVIDENCE", "FAKE", "fake-v1")
        assertEquals("INSUFFICIENT_EVIDENCE", result.safetyState)
    }
    @Test fun urgentResultIsStructured() {
        val result = PetiCheckResultV1("Veterinary review is recommended", safetyState = PetiCheckSafetyState.URGENT)
        assertEquals(PetiCheckSafetyState.URGENT, result.safetyState)
        assertEquals(emptyList<PetiCheckObservation>(), result.observations)
    }
}
