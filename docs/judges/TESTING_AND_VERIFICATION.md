# Testing and verification

From the repository root, install the documented dependencies and run the
backend unit/integration suite, Ruff, web checks, browser checks, architecture
invariants, and release gates. The exact commands are maintained in
`scripts/check.ps1`, `scripts/check.cmd`, and `release/JUDGE_CHECKLIST.md`.

Cloud ADK, Cloud Tasks, private-worker, and deployed action claims require
current external evidence in `release/evidence/`; local tests alone do not
prove those claims. Never commit credentials, tokens, signed URLs, or private
media paths.
