package com.peti.app

import android.content.Context
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.onRoot
import androidx.test.core.app.ApplicationProvider
import androidx.test.platform.app.InstrumentationRegistry
import android.graphics.Bitmap
import java.io.FileOutputStream
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import java.io.File

/**
 * Deterministic functional navigation evidence. It uses semantics, never fixed coordinates,
 * and writes one screenshot after every meaningful public route/action.
 */
class FullNavigationEvidenceTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private val evidenceDir: File
        get() = File(
            ApplicationProvider.getApplicationContext<Context>().getExternalFilesDir(null),
            "peti-navigation-evidence",
        )

    @Before
    fun resetSession() {
        ApplicationProvider.getApplicationContext<Context>()
            .getSharedPreferences("peti_local_auth", Context.MODE_PRIVATE)
            .edit().clear().commit()
        evidenceDir.mkdirs()
        rule.activityRule.scenario.recreate()
        rule.waitForIdle()
    }

    @Test
    fun publicNavigationAndActionsProduceEvidence() {
        capture("01-access")
        rule.onNodeWithTag("signIn").performClick()
        rule.waitForIdle()
        capture("02-authenticated-empty")

        rule.onNodeWithTag("petName").performTextInput("Rocky")
        capture("03-pet-form-filled")
        rule.onNodeWithTag("createPet").performClick()
        rule.waitForIdle()
        capture("04-home")
        assertVisible("homeDashboard", "nav-HOME")

        rule.onNodeWithTag("homeDashboard").assertExists()
        capture("05-home-action-probe")

        // The bottom navigation is semantic and stable across phone/tablet dimensions.
        rule.onNodeWithTag("nav-SCAN").performClick()
        rule.waitForIdle()
        capture("06-analyze")
        assertVisible("nav-SCAN")
        rule.onNodeWithTag("petiCheckMedia").assertExists()
        rule.onNodeWithTag("petiCheckCamera").assertExists()
        rule.onNodeWithTag("petiCheckAudio").assertExists()
        capture("07-analyze-controls")

        rule.onNodeWithTag("nav-HISTORY").performClick()
        rule.waitForIdle()
        capture("08-history")
        assertVisible("nav-HISTORY")
        rule.onNodeWithTag("phase6TimelineHeading").assertExists()
        rule.onNodeWithTag("recordsPanel").assertExists()
        capture("09-history-timeline")

        rule.onNodeWithTag("nav-PROFILE").performClick()
        rule.waitForIdle()
        capture("10-profile")
        assertVisible("nav-PROFILE")
        rule.onNodeWithTag("futurePanel").assertExists()
        rule.onNodeWithTag("historySearch").assertExists()
        capture("11-profile-actions")
    }

    private fun capture(name: String) {
        rule.waitForIdle()
        rule.activity.runOnUiThread {
            val view = rule.activity.window.decorView
            view.isDrawingCacheEnabled = true
            view.buildDrawingCache(true)
            val bitmap = view.drawingCache ?: error("No se ha podido capturar la pantalla")
            FileOutputStream(File(evidenceDir, "$name.png")).use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
            view.destroyDrawingCache()
            view.isDrawingCacheEnabled = false
        }
    }

    private fun assertVisible(vararg tags: String) {
        val root = rule.onRoot().fetchSemanticsNode().boundsInRoot
        tags.forEach { tag ->
            val bounds = rule.onNodeWithTag(tag).fetchSemanticsNode().boundsInRoot
            check(bounds.width > 0f && bounds.height > 0f) { "Elemento sin tamaño: $tag" }
            check(bounds.left >= root.left && bounds.top >= root.top && bounds.right <= root.right && bounds.bottom <= root.bottom) {
                "Elemento fuera del viewport: $tag bounds=$bounds root=$root"
            }
        }
    }

    private fun assertLaidOut(vararg tags: String) {
        tags.forEach { tag ->
            val bounds = rule.onNodeWithTag(tag).fetchSemanticsNode().boundsInRoot
            check(bounds.width > 0f && bounds.height > 0f) { "Elemento sin layout: $tag" }
        }
    }
}
