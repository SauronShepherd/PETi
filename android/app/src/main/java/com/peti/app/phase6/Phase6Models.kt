package com.peti.app.phase6

import java.math.BigDecimal
import java.math.RoundingMode

enum class MeasurementType { WEIGHT, TEMPERATURE }
enum class MeasurementSource { MEASURED, DOCUMENTED, OWNER_REPORTED, AI_ESTIMATED }

data class MeasurementRecord(
    val id: String,
    val animalId: String,
    val measurementType: MeasurementType,
    val sourceClass: MeasurementSource,
    val originalValue: String,
    val originalUnit: String,
    val normalizedValue: String,
    val normalizedUnit: String,
    val measuredAt: String,
)

data class TimelineItem(
    val id: String,
    val animalId: String,
    val occurredAt: String,
    val itemType: String,
    val title: String,
    val summary: String,
    val provenance: String,
    val sourceEntityId: String,
)

data class CareItem(
    val id: String,
    val animalId: String,
    val category: String,
    val title: String,
    val dueAt: String,
    val repeatDays: Int?,
    val notificationEnabled: Boolean,
)

object MeasurementConversions {
    private fun rounded(value: BigDecimal) = value.setScale(3, RoundingMode.HALF_UP).stripTrailingZeros().toPlainString()

    fun convert(value: String, unit: String): Pair<String, String> {
        val number = value.replace(',', '.').toBigDecimalOrNull() ?: error("MEASUREMENT_VALUE_INVALID")
        return when (unit) {
            "lb" -> rounded(number.multiply("0.45359237".toBigDecimal())) to "kg"
            "kg" -> rounded(number.multiply("2.2046226218".toBigDecimal())) to "lb"
            "F", "°F" -> rounded((number - 32.toBigDecimal()).multiply("5".toBigDecimal()).divide("9".toBigDecimal(), 8, RoundingMode.HALF_UP)) to "°C"
            "C", "°C" -> rounded(number.multiply("9".toBigDecimal()).divide("5".toBigDecimal(), 8, RoundingMode.HALF_UP) + 32.toBigDecimal()) to "°F"
            else -> error("MEASUREMENT_UNIT_UNSUPPORTED")
        }
    }
}
