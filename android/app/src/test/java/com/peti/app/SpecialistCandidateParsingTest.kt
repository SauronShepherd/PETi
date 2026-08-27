package com.peti.app

import com.peti.app.specialists.parseInitialScanCandidates
import org.junit.Assert.assertEquals
import org.junit.Test

class SpecialistCandidateParsingTest {
    @Test
    fun parsesPendingCandidatesWithProvenance() {
        val candidates = parseInitialScanCandidates("""[{"id":"c1","field_type":"COAT_COLOR","candidate_value":"black","status":"PENDING_REVIEW","provenance_status":"AI_SUGGESTED"}]""")
        assertEquals(1, candidates.size)
        assertEquals("COAT_COLOR", candidates.single().fieldType)
        assertEquals("AI_SUGGESTED", candidates.single().provenanceStatus)
    }
}
