package com.peti.app.phase6

object CareDeepLink {
    private const val PREFIX = "peti://care/occurrence/"
    fun forOccurrence(occurrenceId: String): String = PREFIX + occurrenceId
    fun occurrenceId(uri: String?): String? {
        if (uri == null || !uri.startsWith(PREFIX)) return null
        val id = uri.removePrefix(PREFIX)
        return id.takeIf { it.isNotBlank() && it.all { character -> character.isLetterOrDigit() || character == '-' || character == '_' } }
    }
}
