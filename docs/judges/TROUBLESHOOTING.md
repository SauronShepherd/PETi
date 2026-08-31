# Troubleshooting

- If the preview is shown, confirm `?demo=1`; it is synthetic by design.
- If an authenticated run cannot start, check backend feature flags and owner,
  dog, and media authorization before checking provider credentials.
- If a run is partial or failed, inspect the persisted run DTO and provenance;
  do not infer completion from browser timers.
- If cloud evidence is absent, report the missing external gate instead of
  presenting local fixtures as deployed proof.
