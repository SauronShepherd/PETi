# Phase 7 Record Vault API

All endpoints require the authenticated owner and enforce pet/document
ownership server-side.

```text
GET    /v1/pets/{pet_id}/records
POST   /v1/pets/{pet_id}/records
GET    /v1/records/{record_id}
PATCH  /v1/records/{record_id}
DELETE /v1/records/{record_id}?confirm_dependencies=true
POST   /v1/records/{record_id}/access
POST   /v1/records/{record_id}/extract
GET    /v1/records/{record_id}/candidate-facts
POST   /v1/candidate-facts/{id}/confirm
POST   /v1/candidate-facts/{id}/correct
POST   /v1/candidate-facts/{id}/reject
GET    /v1/pets/{pet_id}/documented-facts
GET    /v1/documented-facts/{id}
GET    /v1/records/{record_id}/deletion-preview
```

`POST /v1/records/{record_id}/extract` accepts the validated candidate payload
at the provider/worker boundary. It does not create a `DocumentedFact`.
Confirm or Correct creates one; Reject does not.
