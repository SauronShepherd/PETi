package com.peti.app

import androidx.compose.ui.test.assertHasClickAction
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ApplicationProvider
import android.content.Context
import org.junit.Before
import org.junit.Rule
import org.junit.Test

/** Local semantics regression checks; TalkBack/device audit remains external. */
class AccessibilityRegressionTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()

    @Before fun resetLocalSession() {
        ApplicationProvider.getApplicationContext<Context>()
            .getSharedPreferences("peti_local_auth", Context.MODE_PRIVATE)
            .edit().clear().commit()
        rule.activityRule.scenario.recreate()
        rule.waitForIdle()
    }

    @Test fun signedOutPrimaryActionIsOperable() {
        rule.onNodeWithTag("signIn").assertHasClickAction()
        rule.onNodeWithTag("email").assertExists()
        rule.onNodeWithTag("password").assertExists()
    }

    @Test fun petCreationControlsExposeEditableAndClickActions() {
        rule.onNodeWithTag("signIn").performClick()
        rule.onNodeWithTag("petName").performTextInput("Accessibility pet")
        rule.onNodeWithTag("createPet").assertHasClickAction()
    }
}
