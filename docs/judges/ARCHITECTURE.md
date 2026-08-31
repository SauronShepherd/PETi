# Architecture

The judge-facing architecture has a web adapter, an authenticated API, durable
agent-run state, a bounded recipe/runtime, deterministic validators and safety,
and a canonical care/action boundary. Firestore-backed repositories and the
private worker are the production durability seams; memory adapters support
local deterministic verification.

The target recipe is `FECES_COMPARE_V1`: evidence intake, feces specialist,
same-dog longitudinal comparison, validated synthesis, and care planning. A
proposed action is only executed after an exact user approval and produces an
immutable action receipt. The public `?demo=1` surface is synthetic and is not
evidence of a backend execution.
