package com.peti.app

import org.junit.Assert.assertEquals
import org.junit.Test

class HistoryJsonShapeTest {
    @Test
    fun nestedResultDoesNotSplitHistoryItemIntoInnerObjects() {
        val json = """[{"id":"job-1","animal_id":"pet-1","status":"COMPLETED","result":{"id":"result-1","structured_payload":{"summary":"x"}}},{"id":"job-2","animal_id":"pet-1","status":"QUEUED"}]"""
        assertEquals(2, topLevelObjects(json).size)
    }

    private fun topLevelObjects(value: String): List<String> {
        val result = mutableListOf<String>(); var depth = 0; var start = -1; var quoted = false; var escaped = false
        value.forEachIndexed { index, character ->
            if (quoted) { if (escaped) escaped = false else if (character == '\\') escaped = true else if (character == '"') quoted = false; return@forEachIndexed }
            if (character == '"') quoted = true else if (character == '{') { if (depth == 0) start = index; depth++ } else if (character == '}') { depth--; if (depth == 0) { result += value.substring(start, index + 1); start = -1 } }
        }
        return result
    }
}
