# ADR-058 — Weekly Reports are derived immutable artifacts

Reports use server-defined week keys and source references. Generation is
idempotent per owner, pet, week, and report version. Report narration cannot
create or overwrite canonical health facts.
