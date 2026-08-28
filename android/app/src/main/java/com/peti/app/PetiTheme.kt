package com.peti.app

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val PetiTeal = Color(0xFF009E96)
private val PetiCoral = Color(0xFFFF725E)
private val PetiWarm = Color(0xFFFFFBF7)
private val PetiInk = Color(0xFF263238)

private val PetiLightColors = lightColorScheme(
    primary = PetiTeal,
    onPrimary = Color.White,
    secondary = PetiCoral,
    onSecondary = Color.White,
    tertiary = Color(0xFF7B61C9),
    background = PetiWarm,
    surface = Color.White,
    surfaceVariant = Color(0xFFEAF6F4),
    onBackground = PetiInk,
    onSurface = PetiInk,
)

@Composable
fun PetiTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = PetiLightColors,
        shapes = Shapes(
            small = androidx.compose.foundation.shape.RoundedCornerShape(14),
            medium = androidx.compose.foundation.shape.RoundedCornerShape(22),
            large = androidx.compose.foundation.shape.RoundedCornerShape(28),
        ),
        typography = Typography().let {
            it.copy(
                headlineLarge = it.headlineLarge.copy(color = PetiInk),
                titleLarge = it.titleLarge.copy(color = PetiInk),
            )
        },
        content = content,
    )
}
