# PETi testing instructions

## Public demo

Open `https://peti-care.web.app/?demo=1`. This route is deliberately non-destructive and contains two synthetic pets with five images each. It demonstrates navigation, responsive layouts, pet selection and evidence browsing without requiring a judge account.

## Full authenticated flow

Use a disposable Firebase Authentication account provisioned privately for reviewers. Never commit credentials, service-account keys, API keys, Firebase ID tokens or signed upload URLs. Create a pet, upload synthetic evidence, start an agent run, wait for the terminal state, inspect the report, then delete the account and data.

## Verification commands

```powershell
npm run test:e2e
npx playwright test tests/e2e/visual-regression.spec.js
python -m ruff check backend
python -m pytest -q
```

The visual suite covers 15 routes at desktop, tablet and mobile sizes and stores committed Playwright baselines. The suite is non-destructive when pointed at the public demo URL.
