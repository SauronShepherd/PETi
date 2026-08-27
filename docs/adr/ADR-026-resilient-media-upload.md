# ADR-026: Resilient media upload

Android owns local upload-task state and retries through a single logical media ID/session. Process and network interruptions must not create duplicate logical assets.
