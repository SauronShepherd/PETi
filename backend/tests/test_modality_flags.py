from app.media.domain import MediaType


def test_peti_check_modality_defaults_are_fail_closed_for_video_audio():
    from app.analysis.service import AnalysisService

    # The service default policy enables only still images.
    service = AnalysisService.__new__(AnalysisService)
    service.modality_flags = {MediaType.IMAGE: True, MediaType.VIDEO: False, MediaType.AUDIO: False}
    assert service.modality_flags[MediaType.VIDEO] is False
    assert service.modality_flags[MediaType.AUDIO] is False


def test_string_modality_configuration_is_normalized_to_media_types():
    from app.analysis.service import AnalysisService

    service = AnalysisService.__new__(AnalysisService)
    service.__init__(None, None, None, modality_flags={"IMAGE": False, "VIDEO": True})
    assert service.modality_flags[MediaType.IMAGE] is False
    assert service.modality_flags[MediaType.VIDEO] is True
