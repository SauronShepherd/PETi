# ADR-059 — Backend-authoritative Premium entitlement

Google Play purchase tokens are unique and must be verified before entitlement.
Pending, grace, hold, cancellation, expiry, and revoke states are reconciled
server-side; Android cannot grant Premium from a local boolean.
