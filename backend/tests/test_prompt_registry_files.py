from pathlib import Path

from app.ai.registry import PROMPTS, SCHEMAS


def test_active_registry_artifacts_are_loaded_from_versioned_files():
    root = Path("backend/app/ai")
    expected = {
        "platform_smoke": ("prompts/platform_smoke/v1.0.0.md", "schemas/platform_smoke_v1.json"),
        "peti_check": ("prompts/peti_check/v1.0.0.md", "schemas/peti_check_v1.json"),
        "document_extraction": ("prompts/document_extraction/v1.0.0.md", "schemas/document_extraction_v1.json"),
        "dog_initial_scan": ("prompts/dog_initial_scan/v1.0.0.md", "schemas/dog_initial_scan_v1.json"),
        "dog_dental_check": ("prompts/dog_dental_check/v1.0.0.md", "schemas/dog_dental_check_v1.json"),
        "dog_feces_check": ("prompts/dog_feces_check/v1.0.0.md", "schemas/dog_feces_check_v1.json"),
        "dog_body_check": ("prompts/dog_body_check/v1.0.0.md", "schemas/dog_body_check_v1.json"),
    }
    for artifact_id, (prompt_path, schema_path) in expected.items():
        prompt = PROMPTS.resolve(artifact_id)
        schema = SCHEMAS.resolve(artifact_id)
        assert prompt.content == (root / prompt_path).read_text(encoding="utf-8")
        assert schema.content == (root / schema_path).read_text(encoding="utf-8")
