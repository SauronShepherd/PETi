# Judge checklist

1. Run `python -m pytest -q` from the repository root.
2. Run `scripts/check.ps1`.
3. Run `npm run test:e2e` for the browser surface.
4. Inspect the Lab under `/?demo=1`.
5. For cloud review, use the judge Terraform profile and keep credentials out
   of logs and screenshots.
