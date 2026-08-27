import pytest
from app.portability.service import PortabilityService


def test_export_manifest_has_deterministic_content_integrity_and_import_validates_it():
    service = PortabilityService(lambda owner, pet_id: {"records": [{"id": "r1", "title": "Visit"}]})
    package = service.export("owner-1", "pet-1")
    assert len(package["manifest"]["content_sha256"]) == 64
    assert service.import_preview("owner-1", package)["status"] == "PREVIEW_REQUIRED"

    package["sections"]["records"][0]["title"] = "Tampered"
    with pytest.raises(ValueError, match="IMPORT_INTEGRITY_INVALID"):
        service.import_preview("owner-1", package)


@pytest.mark.parametrize("raw_media", ["false", 1, None])
def test_import_rejects_non_boolean_raw_media_manifest(raw_media):
    service = PortabilityService(lambda owner, pet_id: {})
    package = {"manifest": {"schema": "PETI_PORTABLE_PACKAGE", "raw_media_included": raw_media}, "sections": {}}

    with pytest.raises(ValueError, match="IMPORT_INTEGRITY_INVALID"):
        service.import_preview("owner-1", package)


@pytest.mark.parametrize("package", [
    {"manifest": {"schema": "PETI_PORTABLE_PACKAGE"}, "pet_id": 1, "sections": {}},
    {"manifest": {"schema": "PETI_PORTABLE_PACKAGE"}, "pet_id": "pet-1", "sections": []},
])
def test_import_rejects_malformed_pet_package_shape(package):
    service = PortabilityService(lambda owner, pet_id: {})

    with pytest.raises(ValueError, match="IMPORT_INTEGRITY_INVALID"):
        service.import_preview("owner-1", package)
