# Phase 11 — Dog Body Check

Implemented:

- DOG-only Body Check with independent public/kill-switch flags.
- Standardized side, top, and optional front capture metadata and Android guidance.
- Server validation requires side-standing and top-standing capture steps when a body manifest is supplied.
- `BodyCheckResultV1` prompt/schema and bounded visual observation taxonomy.
- PETi-owned broad body-condition categories only; proprietary BCS, diagnosis, age, reproductive, pregnancy, and body-fat inference are excluded.
- AI weight estimation is disabled by default and, when explicitly enabled, is labeled `AI_ESTIMATED` with provenance and limitations.
- Measured/documented weight remains separate from AI estimates.
- Body comparison endpoint remains fail-closed through the shared specialist comparison boundary.
- Comparable body results receive bounded visual labels; incompatible capture remains `NOT_COMPARABLE`.
- Funding provenance records `AI_SPECIALIST_STANDARD`; prior results and comparisons are not re-funded or advertised.
