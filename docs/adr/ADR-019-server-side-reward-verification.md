# ADR-019: Server-side reward verification

Android ad callbacks are UX signals only. The backend creates reward intents, validates the nonce-bound callback, rejects expired/replayed transactions, and creates the authoritative credit grant.
