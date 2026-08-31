# PETi judge entry point

Run `python -m pytest -q` from the repository root, then `scripts/check.ps1`.
The no-auth demo is available at `/?demo=1`; it uses synthetic Luna and Max
data. The judge Terraform profile is `infra/terraform/environments/judge`.

The live Gemini/Cloud path requires project credentials and is intentionally
separate from the deterministic local demo.
