# Play Submission Checklist

Status: `NO_GO_EXTERNAL_EVIDENCE_PENDING`

## Repository checks

- [ ] Privacy and account-deletion URLs are published over public HTTPS.
- [x] Data Safety, Health Apps, Permissions and signing worksheets exist.
- [ ] Legal/privacy review is approved and dated.
- [ ] Signed AAB package is `com.peti.app` and passes artifact inspection.
- [x] Target SDK and debug/release separation are checked locally.
- [ ] Accessibility and localization review is complete on a physical device.
- [ ] Production Firebase/GCP configuration and rollback package are verified.

## Play Console checks

- [ ] Play App Signing enrollment complete.
- [x] Billing is out of scope for this free release; no subscription, base plan,
  license testers or RTDN purchase lifecycle is required.
- [ ] Data Safety and Health declarations submitted.
- [ ] Reviewer instructions and test credentials supplied through Play Console.
- [ ] Store listing, privacy URL and account deletion URL pass review.

## Prepared test procedure

Billing is intentionally not part of the current free-app submission. The
backend billing boundary remains fail-closed and dormant for future phases.

See [`PLAY_BILLING_TEST_PLAN.md`](PLAY_BILLING_TEST_PLAN.md). Google documents
that license testers use non-charging test payment instruments and that an
internal-test release is installed through an opt-in URL:

- <https://developer.android.com/google/play/billing/test>
- <https://support.google.com/googleplay/android-developer/answer/6062777>
- <https://support.google.com/googleplay/android-developer/answer/9845334>

No item marked pending may be inferred from source presence; each requires a
linked external evidence artifact before a GO decision.
