# ADR-045 — Care occurrences are canonical reminder instances

Care items define schedules; occurrences represent individual due instances.
Completion and skip preserve historical occurrences, recurring completion
creates a deterministic next occurrence, and deleting Care soft-cancels future
active occurrences.
