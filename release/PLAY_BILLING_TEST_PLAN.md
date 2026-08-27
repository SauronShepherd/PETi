# PETi — Google Play Billing test plan

This plan is archived for a future paid release. PETi's current hackathon
release is free and does not expose or execute Google Play Billing.

## What is preserved for a future release

- Package ID: `com.peti.app`
- Internal build package ID: `com.peti.app` (the internal variant must not
  use an application-ID suffix)
- Product IDs: `peti_premium_monthly`, `peti_premium_yearly`
- Android Billing Library: `7.1.1`
- Backend verification: Google Play `subscriptionsv2` lookup, fail-closed when
  credentials are absent.
- Local emulator: explicit `LOCAL_TEST` verification path; forged client
  markers are rejected outside LOCAL.

## Play Console sequence

1. Create/register the app with package `com.peti.app`.
2. Create the two subscription products and a base plan for each.
3. Create an **Internal testing** track and upload the signed AAB.
4. Add tester Google accounts to both the internal-test list and Play Console
   **Settings → License testing**.
5. Share the opt-in URL; install the app from Google Play on a device using the
   tester account.
6. Test `always approves`, `always declines`, cancellation, grace period,
   account hold, restore/query purchases, backend reconciliation and RTDN.
7. Record the purchase token hash, entitlement state, backend correlation ID,
   and Play Console evidence. Never commit raw purchase tokens.

Build command: `powershell -File scripts/build-internal.ps1`. The script fails
on any Gradle error and refuses to report success without an artifact.

Google's current guidance: license testers avoid real charges and can use test
payment instruments; internal-test releases are distributed by opt-in URL.
Play Billing Lab can accelerate subscription-renewal and failure scenarios.

## Required external inputs

- Play Console app access and verified developer account.
- Product/base-plan IDs and prices.
- Tester Google account email(s).
- Production package signing/upload key and Play App Signing enrollment.
- Android API base URL and Google Play service-account credentials for the
  staging backend.

The internal build defaults to the current sandbox API URL and can be pointed
at another environment with `PETI_INTERNAL_API_BASE_URL` or the matching
Gradle property. Confirm the value before uploading.

Until those inputs exist, local tests and the injected HTTP gateway emulator are
the authoritative non-production checks.
