package com.peti.app

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import org.junit.Rule
import org.junit.Test

class Phase1PetFlowTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    @Test fun localUserCanCreateAndSeePet() {
        rule.onNodeWithTag("signIn").performClick()
        rule.onNodeWithTag("petName").performTextInput("Milo")
        rule.onNodeWithTag("createPet").performClick()
        rule.onAllNodesWithText("Milo", substring = true).assertCountEquals(2)
    }
}
