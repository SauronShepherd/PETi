
from app.media.service import MediaError


def test_media_integrity_errors_are_stable():
    assert str(MediaError("MEDIA_AI_SOURCE_GENERATION_MISMATCH")) == "MEDIA_AI_SOURCE_GENERATION_MISMATCH"
