# Media provider boundary

This document records the implemented source-of-truth boundary for AI media.
It is implementation evidence, not external certification.

## Resolution and identity

Public requests and Cloud Tasks carry only `media_asset_ids`. The backend
resolves them through `MediaService.resolve_ai_media(owner_user_id, ..., animal_id)`.
That boundary enforces ownership, animal scope, `READY` lifecycle, modality,
declared MIME, object existence and stored content type. It constructs the
provider descriptor from server-side bucket/object metadata; client-supplied
URIs, paths, signed URLs and content are rejected.

Production GCS is accessed through the existing `GcsObjectStorage` client. The
Cloud Run worker uses its dedicated worker service account with bucket-scoped
`roles/storage.objectViewer`; the bucket remains uniform-access and public
access prevention is enforced. No provider creates an independent GCS client.

## Transport forms

| Transport | Media form | Supported behavior |
|---|---|---|
| `VertexGenAITransport` | SDK `types.Part.from_uri(file_uri="gs://...", mime_type=...)` | Private GCS image/video/audio parts |
| `VertexGeminiTransport` | REST `fileData.fileUri` + `mimeType` | Private GCS image/video/audio parts; inline data is also explicit |
| `GeminiApiKeyTransport` | REST `inline_data` + `mime_type` | Inline data only; unsupported GCS sources fail explicitly |

The textual prompt and context are separate text parts and never substitute for
the multimedia part. Results persist media asset IDs and provenance metadata,
not bytes, base64, signed URLs or private object paths.

## Release status

Local implementation and regression tests cover this boundary. This document
does not mark any live GCS, authenticated product, provider certification,
physical-device, legal or production release gate as passed.
