# ADR-044 — Measured-only trends are explicit

Default measurement queries exclude `AI_ESTIMATED` records. A caller can use
the source filter to request measured-only data, while any future estimate
inclusion must be explicit.
