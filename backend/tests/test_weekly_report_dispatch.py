from app.reports.service import WeeklyReportService


class Pets:
    def get(self, owner, pet_id):
        return {"id": pet_id, "owner_user_id": owner}


class Phase6:
    def __init__(self):
        self.measurements = {}

    def timeline(self, owner, pet_id, limit=100):
        return [{"source_entity_type": "CARE_OCCURRENCE", "source_entity_id": "care-1"}]


def test_dispatch_week_is_idempotent_and_reconciles_sources():
    service = WeeklyReportService(Pets(), Phase6())
    first = service.dispatch_week("user-1", "pet-1", "2026-08-24", idempotency_key="scheduler:2026-08-24")
    second = service.dispatch_week("user-1", "pet-1", "2026-08-24", idempotency_key="scheduler:2026-08-24")

    assert first["status"] == "DISPATCHED"
    assert second["status"] == "DUPLICATE_SUPPRESSED"
    report = first["report"]
    result = service.reconcile_sources("user-1", report.id, ["care-1", "missing"])
    assert result["missing_sources"] == ["missing"]
    assert result["complete"] is False


def test_dispatch_week_rejects_invalid_week_key():
    service = WeeklyReportService(Pets(), Phase6())
    try:
        service.dispatch_week("user-1", "pet-1", "not-a-week", idempotency_key="id-1")
    except ValueError as exc:
        assert str(exc) == "REPORT_WEEK_KEY_INVALID"
    else:
        raise AssertionError("invalid week key was accepted")


def test_http_weekly_scheduler_endpoint_uses_idempotent_dispatch():
    from app.main import app
    from fastapi.testclient import TestClient

    user = "weekly-http-user"
    headers = {"Authorization": f"Bearer local-test:{user}", "Idempotency-Key": "pet-weekly-http"}
    client = TestClient(app)
    pet = client.post("/v1/pets", headers=headers, json={"species": "DOG", "display_name": "Weekly pet"}).json()
    body = {"animal_id": pet["id"], "week_key": "2026-08-24", "idempotency_key": "weekly-http-1"}
    first = client.post("/v1/internal/reports/weekly/generate", headers=headers, json=body)
    second = client.post("/v1/internal/reports/weekly/generate", headers=headers, json=body)
    assert first.status_code == 200 and first.json()["week_key"] == "2026-08-24"
    assert second.status_code == 200 and second.json()["status"] == "DUPLICATE_SUPPRESSED"
