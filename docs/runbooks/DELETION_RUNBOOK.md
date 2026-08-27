# Account and Pet Deletion Runbook

1. Confirm owner authorization and create an idempotent deletion request.
2. Tombstone the account/pet before cascading work; suppress new writes and task rehydration.
3. Delete canonical records, media, derived analyses, reports, search projections, memory, shares, notifications and conversations.
4. Retain only explicitly separated billing/audit metadata required by policy.
5. Reconcile partial failures with bounded retries and record payload-free completion evidence.

Provider deletion is promised only where the provider contract supports it.
