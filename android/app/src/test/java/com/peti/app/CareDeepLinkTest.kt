package com.peti.app

import com.peti.app.phase6.CareDeepLink
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class CareDeepLinkTest {
    @Test fun parsesOnlyOpaqueOccurrenceIds() {
        assertEquals("occ-123", CareDeepLink.occurrenceId(CareDeepLink.forOccurrence("occ-123")))
        assertNull(CareDeepLink.occurrenceId("https://example.invalid/occ-123"))
        assertNull(CareDeepLink.occurrenceId("peti://care/occurrence/../../other"))
    }
}
