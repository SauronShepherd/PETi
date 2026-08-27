# Upload key recovery runbook

This runbook applies only to the production Android upload key. Never place a
private key, keystore, password, or recovery code in the repository, CI logs,
issue tracker, or release manifest.

## If the local upload key is lost

1. Freeze production uploads and record the incident ID and last known version.
2. Confirm Play App Signing is enabled and identify the authorized account owner.
3. Generate a new upload certificate using the approved offline workstation.
4. Request an upload-key reset in Play Console using the new certificate.
5. Store the replacement private key in the organization-approved secret store
   with two-person access and a documented recovery contact.
6. Update the CI secret reference, verify the certificate fingerprint, and build
   a non-public artifact.
7. After Play accepts the new key, run the signed-artifact inspection and record
   the result in the frozen release evidence.

## Stop conditions

Do not publish if the certificate fingerprint is not confirmed by Play, if the
keystore password has been exposed, or if a replacement key cannot be stored
with auditable access. Key rotation does not authorize bypassing Play App
Signing or reviewer controls.
