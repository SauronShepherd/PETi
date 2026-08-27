# ADR-030: Upload recovery and account isolation

Local upload tasks are keyed by canonical PETi user ID and local task ID. Retry classification distinguishes network failure, expired authorization, permanent validation, and cancellation. Sign-out clears the current account's pending tasks and never exposes them to the next account.
