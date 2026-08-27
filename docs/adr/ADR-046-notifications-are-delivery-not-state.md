# ADR-046 — Notifications are delivery, not canonical state

Notification permission, dismissal, delivery failure, and deduplication do not
delete or complete a Care occurrence. The backend remains the source of truth;
FCM carries only minimal opaque occurrence routing data.
