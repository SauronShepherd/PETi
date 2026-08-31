# PETi web client

Responsive PETi client connected to the authenticated Cloud API. Firebase Web Auth
supports email/password and Google sign-in. Runtime configuration is
provided through `window.PETI_CONFIG`; secrets must never be committed.

## Local run

From PowerShell:

```powershell
.\scripts\start-web.ps1
```

Or:

```powershell
python -m http.server 4173 --bind 0.0.0.0 -d web
```

Open `http://localhost:4173/?demo=1` for the safe visual demo. The hosted demo
is https://peti-care.web.app/?demo=1 and includes two synthetic pets with five
evidence images per pet. It does not perform destructive backend writes.

The Veterinary AI Lab demo is available from the **Admin** entry in demo mode.
Every metric and trace in that view is labelled as synthetic replay data. The
real Lab endpoints require an authenticated, server-authorized operator role.

For real authentication, provide `apiBaseUrl` and `firebaseConfig` at runtime.

Without Firebase configuration, the non-demo route remains sign-in protected.

## Validation

```powershell
npm run test:e2e
npx playwright test tests/e2e/visual-regression.spec.js
```
