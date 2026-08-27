# PETi external qualification execution checklist

This runbook is the operator handoff for gates that cannot be proven by source
control or local fakes. It must be executed against the frozen release
revision, with disposable non-production data first. Completing a checklist
item requires attaching its raw command output or test artifact to the release
evidence manifest.

## 1. Preflight and change control

1. Confirm the reviewed project, environment, region, budget, and operator
   identity.
2. Run the read-only preflight:

   ```powershell
   pwsh -NoProfile -File scripts/gcp-preflight.ps1 `
     -ProjectId <sandbox-project-id> -Environment DEV -Region europe-west1
   ```

3. Record the JSON output. It must show an active project, billing state,
   required APIs, and `mutation_performed: false`.
4. Review `docs/ZERO_COST_POLICY.md`. Do not deploy, seed, reset, or call a
   paid provider until the operator explicitly approves that action.

## 2. Sandbox product evidence

After explicit approval, execute the deployment and seed/reset runbooks using
only the disposable sandbox project. Capture:

- Terraform plan and apply output, including the exact revision IDs.
- Firebase-authenticated Android-to-API sign-in and account-switch results.
- Owner isolation across every owner-scoped domain.
- Media upload/finalize/read/delete results for small and resumable objects.
- Cloud Tasks OIDC delivery to the private worker, duplicate-delivery result,
  and retry/dead-letter behavior.
- PETi Check and each enabled specialist vertical slice with provider metadata,
  cost metadata, safety state, and persisted provenance.
- Account/pet deletion race results and independent residual-zero inventory.

The sandbox gate remains `PARTIAL` until the complete product matrix is
executed and linked. Health endpoints, synthetic maintenance tasks, and local
FakeAI runs are insufficient.

## 3. Provider and specialist certification

Run every `dev`, `held_out`, `red_team`, and `regression` manifest against the
exact frozen provider/model/prompt/schema/guardrail configuration. Preserve
request IDs, model/config IDs, usage/cost records, safety outcomes, and the
sanitized result artifact. Produce and review a release certificate for PETi
Check, Initial Scan, Dental Check, Feces Check, and Body Check. Keep each
public feature flag disabled until its certificate is signed.

## 4. Device, privacy, and operations evidence

Execute the physical-device matrix for sign-in, camera capture, Photo Picker,
SAF PDF, microphone, notifications, process death, reinstall, locale/DST,
large text, TalkBack, touch targets, and non-color state. Execute provider
outage, queue backlog, storage failure, billing failure, reward SSV failure,
kill-switch, rollback, load, and cost-stress drills. Attach raw results and
timestamps; emulator-only evidence does not satisfy this gate.

## 5. Production and Play release

Only after legal and security approval: provision isolated production
resources, create and protect the upload key, build and inspect the signed
AAB, publish the approved privacy/deletion URLs, complete the live Play Data
Safety and Health declarations, run internal-track testing, review the
pre-launch report, and record the submission outcome. Do not change any
`PENDING` release certificate or final go/no-go decision based on local or
sandbox evidence alone.

## Stop conditions

Stop immediately on an unexpected project, missing budget approval, leaked
secret/token, cross-user access, public worker reachability, unsafe provider
claim, residual data, unexplained cost, failed rollback, or evidence that is
not bound to the frozen release revision. Record the failure and leave the
release decision as `NO-GO` or `PENDING_EXTERNAL_*`.
