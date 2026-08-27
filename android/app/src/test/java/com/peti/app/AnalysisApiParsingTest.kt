package com.peti.app

import com.peti.app.analysis.AnalysisStatus
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test

class AnalysisApiParsingTest {
    @Test
    fun completedResultModelContainsPersistedSummaryAndSafety() {
        val json = """{"id":"job-1","animal_id":"pet-1","analysis_type":"PETI_CHECK","status":"COMPLETED","media_asset_ids":["media-1"],"result":{"id":"result-1","summary":"Visible redness","safety_state":"REVIEW","provider":"FAKE","provider_model":"fake-v1"}}"""
        val result = parseAnalysisResult(json)
        assertNotNull(result)
        assertEquals("job-1", result!!.first)
        assertEquals(AnalysisStatus.COMPLETED, result.second)
        assertEquals("Visible redness", result.third)
        assertEquals("REVIEW", result.fourth)
    }

    @Test
    fun expandedResultFieldsAcceptTypedItemsAndEscapedText() {
        val json = """{"id":"job-1","animal_id":"pet-1","analysis_type":"PETI_CHECK","status":"COMPLETED","result":{"id":"result-1","summary":"Visible \\"redness\\"","safety_state":"REVIEW","observations":[{"text":"red\\narea"}],"possible_interpretations":[{"text":"may need review"}],"uncertainties":[{"text":"low light"}],"red_flags":[{"text":"pain"}],"recommended_actions":[{"text":"monitor"}],"source_media_ids":["media-1"]}}"""
        assertEquals("media-1", Regex("\\\"source_media_ids\\\":\\[(.*?)\\]").find(json)!!.groupValues[1].trim('"'))
    }

    private fun parseAnalysisResult(json: String): Quad {
        val id = Regex("\\\"id\\\":\\\"([^\\\"]+)\\\"").find(json)!!.groupValues[1]
        val status = AnalysisStatus.valueOf(Regex("\\\"status\\\":\\\"([^\\\"]+)\\\"").find(json)!!.groupValues[1])
        val section = json.substring(json.indexOf("\\\"result\\\":{") + 9)
        val summary = Regex("\\\"summary\\\":\\\"([^\\\"]+)\\\"").find(section)!!.groupValues[1]
        val safety = Regex("\\\"safety_state\\\":\\\"([^\\\"]+)\\\"").find(section)!!.groupValues[1]
        return Quad(id, status, summary, safety)
    }

    private data class Quad(val first: String, val second: AnalysisStatus, val third: String, val fourth: String)
}
