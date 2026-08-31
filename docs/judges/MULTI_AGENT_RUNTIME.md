# Multi-agent runtime

The released compare path is a bounded recipe. `RunCoordinator`/execution
validates the recipe, dispatches role-specific invocations and validates each
structured result before the successor. Context is owner/pet scoped. Model
selection is server-side and versioned. Deterministic safety and claim
grounding remain authoritative over model output.
