# ADR-043 — Conflicting measurements coexist

Measurements are append-oriented observations. PETi does not silently select
one conflicting value as truth; each record retains its timestamp, source
class, original unit, and canonical identity.
