# Proof of action

Care mutations follow `ProposedAction -> exact payload-hash approval ->
CareActionExecutor -> idempotent Care mutation -> ActionReceipt`. Proposals
expire after 15 minutes. Rejected actions record a decision event but no
execution receipt. Re-delivery with the same key returns the same receipt.
