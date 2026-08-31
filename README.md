# PETi — Evidence-first multi-agent pet care

PETi is a responsive, evidence-first pet-care application. It organizes pet profiles and observations, analyzes submitted media with a bounded multi-agent workflow, preserves provenance, and escalates uncertainty instead of presenting a diagnosis.

The experience is designed as a free, private product focused on wellbeing. Results are informational and do not replace evaluation by a veterinary professional.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e backend[dev]
./scripts/check
./scripts/run-backend
```

On Windows use `scripts\\bootstrap.cmd`, `scripts\\check.cmd` and `scripts\\run-backend.ps1`.

The backend exposes `GET /health/live` and `GET /health/ready`. Local verification does not require production credentials or paid cloud services.

## Verification

```text
python -m ruff check backend
python -m pytest -q
```

For the web client, see [`web/README.md`](web/README.md). The main release gate verifies both backend and client.

The application uses Firebase for identity and notifications in a real environment. Sensitive credentials and configuration are supplied externally and must not be stored in this repository.

## Documentation

- [Architecture](docs/HACKATHON_ARCHITECTURE.md)
- [Demo script](docs/HACKATHON_DEMO_SCRIPT.md)
- [Testing instructions](docs/HACKATHON_TESTING_INSTRUCTIONS.md)
- [Privacy and security](docs/ARCHITECTURE_INVARIANTS.md)
- [Release materials](release/)
