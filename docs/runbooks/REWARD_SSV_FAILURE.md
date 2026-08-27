# Reward SSV failure runbook

Reject malformed, expired, replayed, wrong-product, and wrong-user callbacks.
Keep the intent pending for retryable provider failures; do not grant credits
until signature and correlation checks succeed. Reconcile duplicate events by
the provider event identifier.
