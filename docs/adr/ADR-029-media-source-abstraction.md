# ADR-029: Media source abstraction

Photo Picker, SAF, and CameraX provide `MediaSource` instances to one upload coordinator. Feature screens do not implement upload, ownership, storage paths, or finalization independently.
