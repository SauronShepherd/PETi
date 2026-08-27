import pytest
from app.search.service import SearchService


def test_search_normalizes_filters_and_bounds_limit():
    service = SearchService(lambda owner, pet_id: [
        {"id": "r1", "type": "RECORD", "pet_id": pet_id, "title": "Annual Vet Visit", "source": "CANONICAL"},
        {"id": "r2", "type": "MEASUREMENT", "pet_id": pet_id, "title": "Weight", "source": "CANONICAL"},
    ])

    results = service.search("owner-1", "  ANNUAL   vet ", "pet-1", entity_type="RECORD", limit="1")

    assert [item["id"] for item in results] == ["r1"]
    assert results[0]["query_hash"]


def test_search_invalid_limit_fails_safe_and_empty_query_is_not_broad_read():
    service = SearchService(lambda owner, pet_id: [{"id": "r1", "title": "record"}])

    assert service.search("owner-1", "record", limit="invalid")
    assert service.search("owner-1", "   ") == []


@pytest.mark.parametrize("limit", [True, False, 2.5])
def test_search_rejects_coercive_limit_types_with_safe_default(limit):
    service = SearchService(lambda owner, pet_id: [
        {"id": str(index), "title": "record", "type": "RECORD"}
        for index in range(60)
    ])

    assert len(service.search("owner-1", "record", limit=limit)) == 50


def test_search_skips_malformed_source_rows():
    service = SearchService(lambda owner, pet_id: [None, "malformed", {"id": "r1", "title": "record"}])

    results = service.search("owner-1", "record")

    assert [item["id"] for item in results] == ["r1"]


def test_search_fails_closed_when_source_provider_is_unavailable():
    def unavailable(owner, pet_id):
        raise RuntimeError("store unavailable")

    service = SearchService(unavailable)

    assert service.search("owner-1", "record") == []
