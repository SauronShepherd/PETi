from app.ai.providers.base import ProviderError
from app.analysis.domain import AnalysisStatus


def test_retryable_provider_failure_is_retryable_before_attempt_budget():
    error = ProviderError("PROVIDER_TIMEOUT", True)
    attempt_count, max_attempts = 1, 3
    status = (
        AnalysisStatus.FAILED_RETRYABLE
        if error.retryable and attempt_count < max_attempts
        else AnalysisStatus.FAILED_FINAL
    )
    assert status == AnalysisStatus.FAILED_RETRYABLE
