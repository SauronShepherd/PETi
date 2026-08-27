# ADR-191 — WEBP and audio capture are explicit capability decisions

## Decision

WEBP is not accepted as a production media format until both the Android
viewer and every extraction/preparation path have been validated. The current
allowlist remains conservative and does not advertise WEBP support by default.

The Phase 3 audio capture foundation is deferred. The backend audio media
contract remains available for future cloud processing, but Android does not
claim microphone capture is shipped until a physical-device implementation,
permission UX, temporary-file cleanup, upload recovery, and accessibility
review are complete.

## Consequences

The absence of WEBP/audio capture is an explicit unsupported/deferred state,
not a half-enabled feature. Release manifests must keep those capabilities
disabled until their evidence gates are attached.
