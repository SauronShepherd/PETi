package com.peti.app

import com.peti.app.phase6.MeasurementConversions
import org.junit.Assert.assertEquals
import org.junit.Test

class Phase6MeasurementTest {
    @Test fun preservesDeterministicWeightConversion() {
        assertEquals("10.16", MeasurementConversions.convert("22.4", "lb").first)
        assertEquals("kg", MeasurementConversions.convert("22.4", "lb").second)
    }

    @Test fun preservesDeterministicTemperatureConversion() {
        assertEquals("38.722", MeasurementConversions.convert("101.7", "F").first)
        assertEquals("°C", MeasurementConversions.convert("101.7", "F").second)
    }
}
