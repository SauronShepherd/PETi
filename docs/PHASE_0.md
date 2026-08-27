# Phase 0

Phase 0 establishes the executable repository, cloud-only boundaries, typed configuration, health API, deterministic ports, contracts, security checks, and CI. It intentionally does not implement customer features, Gemini integration, advertising, billing, or local AI.

The root acceptance command is `scripts/check.ps1` on Windows or `./scripts/check` on Unix-like environments. Emulator execution is exposed separately by `scripts/run-android-tests.ps1` because an emulator is not guaranteed to exist on every developer workstation.
