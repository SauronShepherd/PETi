import hashlib
from dataclasses import dataclass
from pathlib import Path

_ARTIFACT_ROOT = Path(__file__).parent


def _file_content(relative_path: str) -> str:
    path = _ARTIFACT_ROOT / relative_path
    return path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class VersionedArtifact:
    artifact_id: str
    version: str
    content: str
    sha256: str


class ImmutableRegistry:
    def __init__(self):
        self._items = {}
        self._active = {}

    def register(self, artifact_id, version, content):
        key = (artifact_id, version)
        digest = hashlib.sha256(content.encode()).hexdigest()
        existing = self._items.get(key)
        if existing and existing.sha256 != digest:
            raise ValueError("VERSIONED_ARTIFACT_IMMUTABLE")
        artifact = existing or VersionedArtifact(artifact_id, version, content, digest)
        self._items[key] = artifact
        return artifact

    def activate(self, artifact_id, version):
        if (artifact_id, version) not in self._items:
            raise KeyError(f"ARTIFACT_NOT_FOUND:{artifact_id}:{version}")
        self._active[artifact_id] = version

    def resolve(self, artifact_id):
        version = self._active.get(artifact_id)
        if not version:
            raise KeyError(f"ARTIFACT_NOT_ACTIVE:{artifact_id}")
        return self._items[(artifact_id, version)]


PROMPTS = ImmutableRegistry()
SCHEMAS = ImmutableRegistry()
PROMPTS.register(
    "platform_smoke",
    "1.0.0",
    _file_content("prompts/platform_smoke/v1.0.0.md"),
)
PROMPTS.register("peti_check", "1.0.0", _file_content("prompts/peti_check/v1.0.0.md"))
PROMPTS.register(
    "document_extraction",
    "1.0.0",
    _file_content("prompts/document_extraction/v1.0.0.md"),
)
for _specialist_artifact, _specialist_prompt in {
    "dog_initial_scan": _file_content("prompts/dog_initial_scan/v1.0.0.md"),
    "dog_dental_check": _file_content("prompts/dog_dental_check/v1.0.0.md"),
    "dog_feces_check": _file_content("prompts/dog_feces_check/v1.0.0.md"),
    "dog_body_check": _file_content("prompts/dog_body_check/v1.0.0.md"),
}.items():
    PROMPTS.register(_specialist_artifact, "1.0.0", _specialist_prompt)
SCHEMAS.register("platform_smoke", "1.0.0", _file_content("schemas/platform_smoke_v1.json"))
SCHEMAS.register("peti_check", "1.0.0", _file_content("schemas/peti_check_v1.json"))
for _schema_artifact in ("dog_feces_check", "dog_body_check", "dog_initial_scan", "dog_dental_check"):
    SCHEMAS.register(
        _schema_artifact,
        "1.0.0",
        _file_content(f"schemas/{_schema_artifact}_v1.json"),
    )
SCHEMAS.register(
    "document_extraction", "1.0.0", _file_content("schemas/document_extraction_v1.json")
)
PROMPTS.activate("platform_smoke", "1.0.0")
PROMPTS.activate("peti_check", "1.0.0")
PROMPTS.activate("document_extraction", "1.0.0")
for _specialist_artifact in ("dog_initial_scan", "dog_dental_check", "dog_feces_check", "dog_body_check"):
    PROMPTS.activate(_specialist_artifact, "1.0.0")
SCHEMAS.activate("platform_smoke", "1.0.0")
SCHEMAS.activate("peti_check", "1.0.0")
SCHEMAS.activate("document_extraction", "1.0.0")
for _specialist_artifact in ("dog_initial_scan", "dog_dental_check", "dog_feces_check", "dog_body_check"):
    SCHEMAS.activate(_specialist_artifact, "1.0.0")
