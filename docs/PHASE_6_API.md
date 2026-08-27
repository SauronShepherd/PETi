# PETi Phase 6 API contract

All customer routes require the authenticated PETi bearer token and enforce
owner-scoped pet access.

## Measurements

```text
GET    /v1/pets/{pet_id}/measurements
POST   /v1/pets/{pet_id}/measurements
GET    /v1/pets/{pet_id}/measurements/trend
GET    /v1/measurements/{measurement_id}
PATCH  /v1/measurements/{measurement_id}
DELETE /v1/measurements/{measurement_id}
```

Measurement creation requires `Idempotency-Key` and accepts `WEIGHT` or
`TEMPERATURE`, an original decimal value/unit, and one of `MEASURED`,
`DOCUMENTED`, or `OWNER_REPORTED`. `AI_ESTIMATED` is reserved and rejected for
client creation. List and trend queries exclude AI estimates by default and
support `source_class=MEASURED`.

## Care and occurrences

```text
GET    /v1/pets/{pet_id}/care
POST   /v1/pets/{pet_id}/care
GET    /v1/care/{care_id}
PATCH  /v1/care/{care_id}
DELETE /v1/care/{care_id}
GET    /v1/pets/{pet_id}/care-occurrences
POST   /v1/care-occurrences/{id}/complete
POST   /v1/care-occurrences/{id}/skip
POST   /v1/care-occurrences/{id}/reschedule
```

Care supports the Phase 6 categories, explicit timezone, once/daily/weekly/
monthly/custom recurrence, notification preference, and optional notes. Care
creation requires `Idempotency-Key`; occurrence actions may provide one for
retry-safe completion, skipping, and rescheduling. Care responses expose
`active`; deletion is soft and preserves historical occurrences.

## Timeline

```text
GET /v1/pets/{pet_id}/timeline
```

Supported query parameters are `before`, `after`, `item_type`, and `limit`.
Timeline items are projections over canonical measurements, Care completions,
and completed PETi Checks; they are not a second source of truth.

## Notification preferences and devices

```text
GET   /v1/me/notification-preferences
PATCH /v1/me/notification-preferences
POST  /v1/me/devices
DELETE /v1/me/devices/{device_id}
```

Notification permission affects delivery only; Care and occurrences remain
available when permission is denied.

## Delivery internals

```text
POST /v1/internal/tasks/notifications
```

This route requires task authentication. Non-LOCAL environments use the
Firebase Admin FCM sender. LOCAL uses the task-authenticated fake sender and
the local inbox endpoints:

```text
POST /v1/internal/local/notifications/dispatch
GET  /v1/internal/local/notifications/inbox
```

Payloads contain only an opaque `occurrence_id`; exact measurements, notes, AI
results, and other health narratives are excluded.
