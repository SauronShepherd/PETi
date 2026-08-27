# PETi release shrinker configuration.
# AndroidX, Compose, Firebase, and Hilt publish their own consumer rules.
# Keep the application entry point and reflective Firebase authentication types.
-keep class com.peti.app.MainActivity { *; }
-keep class com.google.firebase.auth.** { *; }
-dontwarn javax.annotation.**
