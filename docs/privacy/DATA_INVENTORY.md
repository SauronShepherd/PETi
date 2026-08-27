# PETi Data Inventory

| Class | Examples | Owner deletion | Retention principle |
|---|---|---:|---|
| Canonical pet data | profile, measurements, care | yes | until owner deletion |
| Source documents/media | uploads, attachments | yes | explicit retention class |
| Derived artifacts | analyses, reports, search projections, memory | yes/invalidate | never outlive source |
| Collaboration | invitations, memberships, shares | yes/revoke | expiry and revocation |
| Conversation | threads, messages, citations | yes | separate from source records |
| Billing/audit | token fingerprints, ledger/audit IDs | bounded/legal | no clinical payload |

General logs must not contain raw health payload, provider transcripts or secrets.
