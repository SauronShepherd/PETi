# PETi State Contracts

State transitions are server-owned and idempotent. Tombstoned entities cannot be rehydrated by retries, queued work or stale clients. Public state enums are versioned before exposure to the web client.
