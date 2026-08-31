from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.auth.models import AuthenticatedPrincipal
from app.lab.enums import FeedbackReason, FeedbackValue, ReviewSeverity

from .dependencies import require_principal

router = APIRouter(prefix="/v1")


class FeedbackUpsertRequest(BaseModel):
    value: FeedbackValue
    reasons: list[FeedbackReason] = Field(default_factory=list, max_length=5)
    comment: str | None = Field(default=None, max_length=1000)
    locale: str | None = Field(default=None, max_length=16)

    @field_validator("reasons")
    @classmethod
    def unique_reasons(cls, reasons: list[FeedbackReason]) -> list[FeedbackReason]:
        if len(set(reasons)) != len(reasons):
            raise ValueError("duplicate feedback reasons")
        return reasons


class SafetyReportRequest(BaseModel):
    category: str = Field(max_length=64)
    severity: ReviewSeverity
    description: str | None = Field(default=None, max_length=1000)


class OutcomeRequest(BaseModel):
    response_id: str | None = Field(default=None, max_length=128)
    outcome: str = Field(max_length=64)


def _ensure_enabled(request: Request) -> None:
    if not request.app.state.settings.lab_feedback_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "LAB_FEEDBACK_NOT_ENABLED")


def _map_error(exc: ValueError) -> HTTPException:
    code = str(exc)
    if code in {"LAB_RESPONSE_NOT_FOUND", "LAB_FEEDBACK_NOT_FOUND"}:
        return HTTPException(status.HTTP_404_NOT_FOUND, code)
    return HTTPException(status.HTTP_409_CONFLICT, code)


def _rate_limit(request: Request, principal: AuthenticatedPrincipal) -> None:
    decision = request.app.state.lab_feedback_abuse_guard.check_and_record(f"lab-feedback:{principal.user_id}")
    if not decision.allowed:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "LAB_FEEDBACK_RATE_LIMITED",
            headers={"Retry-After": str(decision.retry_after_seconds)})


@router.put("/agent-runs/{run_id}/responses/{response_id}/feedback")
async def upsert_response_feedback(
    run_id: str,
    response_id: str,
    body: FeedbackUpsertRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    _ensure_enabled(request)
    _rate_limit(request, principal)
    try:
        response = request.app.state.lab_repository.get_response(response_id)
        if not response or response.run_id != run_id:
            raise ValueError("LAB_RESPONSE_NOT_FOUND")
        item = request.app.state.lab_feedback.upsert(
            principal.user_id,
            response_id,
            value=body.value,
            reasons=body.reasons,
            comment=body.comment,
            locale=body.locale,
        )
        return item.public()
    except ValueError as exc:
        raise _map_error(exc) from exc


@router.get("/agent-runs/{run_id}/responses/{response_id}/feedback")
async def get_response_feedback(
    run_id: str,
    response_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    _ensure_enabled(request)
    response = request.app.state.lab_repository.get_response(response_id)
    if not response or response.run_id != run_id or response.owner_user_id != principal.user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "LAB_RESPONSE_NOT_FOUND")
    item = request.app.state.lab_feedback.get(principal.user_id, response_id)
    return item.public() if item and not item.removed_at else None


@router.delete("/agent-runs/{run_id}/responses/{response_id}/feedback")
async def delete_response_feedback(
    run_id: str,
    response_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    _ensure_enabled(request)
    _rate_limit(request, principal)
    try:
        response = request.app.state.lab_repository.get_response(response_id)
        if not response or response.run_id != run_id:
            raise ValueError("LAB_RESPONSE_NOT_FOUND")
        return request.app.state.lab_feedback.remove(principal.user_id, response_id).public()
    except ValueError as exc:
        raise _map_error(exc) from exc


@router.post("/agent-runs/{run_id}/responses/{response_id}/safety-report", status_code=201)
async def create_safety_report(run_id: str, response_id: str, body: SafetyReportRequest,
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    _ensure_enabled(request)
    _rate_limit(request, principal)
    response = request.app.state.lab_repository.get_response(response_id)
    if not response or response.run_id != run_id or response.owner_user_id != principal.user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "LAB_RESPONSE_NOT_FOUND")
    try:
        request.app.state.lab_operations.audit(principal.user_id, "SAFETY_REPORT_REQUESTED", "RESPONSE",
            response_id, request.state.correlation_id)
        item = request.app.state.lab_operations.safety_report(principal.user_id, response,
            category=body.category, severity=body.severity, description=body.description)
        return item.public()
    except ValueError as exc: raise _map_error(exc) from exc


@router.post("/agent-runs/{run_id}/outcomes", status_code=201)
async def create_outcome(run_id: str, body: OutcomeRequest, request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal)):
    _ensure_enabled(request)
    _rate_limit(request, principal)
    response = request.app.state.lab_repository.get_response(body.response_id) if body.response_id else next(
        (x for x in request.app.state.lab_repository.list_responses() if x.run_id == run_id), None)
    if not response or response.run_id != run_id or response.owner_user_id != principal.user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "LAB_RESPONSE_NOT_FOUND")
    try: return request.app.state.lab_operations.outcome(principal.user_id, response, body.outcome).public()
    except ValueError as exc: raise _map_error(exc) from exc
