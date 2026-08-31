from __future__ import annotations

from uuid import uuid4

from .contracts import HumanReview

ALLOWED_SAFETY_CATEGORIES = frozenset({"DANGEROUS_ADVICE", "FALSE_REASSURANCE", "DIAGNOSIS_LANGUAGE", "MEDICATION_GUIDANCE", "FABRICATED_INFORMATION", "OTHER"})


def create_review(report) -> HumanReview:
    return HumanReview(str(uuid4()), report.id, report.run_id, report.response_id, report.severity)
