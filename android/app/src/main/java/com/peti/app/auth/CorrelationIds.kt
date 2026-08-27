package com.peti.app.auth

import java.util.UUID

object CorrelationIds {
    fun next(): String = UUID.randomUUID().toString()
}
