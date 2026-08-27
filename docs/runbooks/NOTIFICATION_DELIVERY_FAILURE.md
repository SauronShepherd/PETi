# Notification delivery failure runbook

Separate canonical reminder state from delivery state. Retry transient FCM or
email failures with bounded backoff, deduplicate by delivery key, and do not
delete the underlying care occurrence when delivery fails.
