# PETi State Contracts

State transitions are server-owned and idempotent. Tombstoned entities cannot be rehydrated by retries, queued work or stale clients. Public state enums must be versioned before they are exposed to Android.
