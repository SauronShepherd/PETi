# ADR-025: Finalize verifies storage

An upload becomes `READY` only after the backend inspects the private object, verifies content type, size, and checksum policy, and records canonical metadata.
