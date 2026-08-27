# AI cost budget runbook

1. Confirm `variable_cost_intake_enabled` and the daily/monthly budget metrics.
2. If the critical threshold is exceeded, disable new cost-bearing operations.
3. Preserve existing results, exports, deletion, and ordinary metadata writes.
4. Record the incident, environment, policy version, and operator in the audit log.
5. Re-enable only after the budget window and provider cost attribution reconcile.
