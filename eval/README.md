# Evaluation

Deterministic contract and architecture checks belong in the repository test suite. Real Gemini evaluation is intentionally deferred and must never run in normal CI.

An approved `PETI_REAL_EVAL_COMMAND` must accept `--split` and print one JSON
object containing `case_results`, matching `metrics`, and exactly these six
boolean `critical_gates`: `dangerous_under_triage`, `diagnosis_language`,
`fabricated_measurement`, `medication_guidance`, `false_reassurance`, and
`schema_pass`. The runner persists those gates unchanged; it never promotes a
missing or malformed gate.
