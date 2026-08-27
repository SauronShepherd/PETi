# Cloud rollback runbook

Stop rollout, route traffic to the last known-good immutable revision, disable
new variable-cost operations if the incident involves AI, and preserve queued
work for reconciliation. Record revision digests and the rollback reason.
