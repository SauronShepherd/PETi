from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.auth.models import AuthenticatedPrincipal
from app.lab.enums import FeedbackValue, LabPermission, TraceStatus
from app.lab.permissions import permissions_for, require_permission

from .dependencies import require_principal

router = APIRouter(prefix="/v1/internal/lab")


def _require(request: Request, principal: AuthenticatedPrincipal, permission: LabPermission):
    if not request.app.state.settings.lab_admin_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "LAB_ADMIN_NOT_ENABLED")
    try:
        require_permission(principal, permission, request.app.state.settings.environment.value)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc


def _audit_read(request: Request, principal: AuthenticatedPrincipal, action: str, target: str | None = None):
    request.app.state.lab_operations.audit(principal.user_id, action, "LAB", target,
        request.state.correlation_id)


@router.get("/access")
async def lab_access(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    environment = request.app.state.settings.environment.value
    permissions = permissions_for(principal, environment)
    return {
        "enabled": bool(request.app.state.settings.lab_admin_enabled),
        "can_view_lab": LabPermission.VIEW_AGGREGATES in permissions,
        "permissions": sorted(permission.value for permission in permissions),
        "environment": environment,
    }


@router.get("/overview")
async def lab_overview(
    request: Request, response: Response,
    principal: AuthenticatedPrincipal = Depends(require_principal)
):
    _require(request, principal, LabPermission.VIEW_AGGREGATES)
    payload = request.app.state.lab_queries.overview()
    response.headers["Cache-Control"] = "private, max-age=15"
    response.headers["ETag"] = f'W/"lab-{payload["run_count"]}-{payload["rollup_count"]}"'
    return payload


@router.get("/runs")
async def lab_runs(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, min_length=1, max_length=128),
    run_status: TraceStatus | None = Query(default=None, alias="status"),
    agent_id: str | None = Query(default=None, max_length=64),
    safety_state: str | None = Query(default=None, max_length=64),
    model_id: str | None = Query(default=None, min_length=1, max_length=128),
    feedback_value: FeedbackValue | None = Query(default=None),
    min_duration_ms: int | None = Query(default=None, ge=0, le=3_600_000),
    sort: str = Query(default="STARTED_DESC", pattern="^(STARTED_DESC|STARTED_ASC)$"),
    started_after: datetime | None = Query(default=None),
    started_before: datetime | None = Query(default=None),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    _require(request, principal, LabPermission.VIEW_TRACES)
    now = datetime.now(UTC)
    start = started_after or now - timedelta(days=1)
    end = started_before or now
    if start.tzinfo is None or end.tzinfo is None or start > end or end - start > timedelta(days=90) or end > now + timedelta(minutes=5):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "LAB_TIME_RANGE_INVALID")
    try:
        items, next_cursor = request.app.state.lab_queries.page_runs(limit=limit, cursor=cursor,
            status=run_status.value if run_status else None, agent_id=agent_id, safety_state=safety_state,
            model_id=model_id,
            feedback_value=feedback_value.value if feedback_value else None,
            min_duration_ms=min_duration_ms, sort=sort,
            started_after=start, started_before=end)
        return {"items": items, "next_cursor": next_cursor}
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.get("/runs/{run_id}")
async def lab_run_detail(
    run_id: str,
    request: Request,
    response: Response,
    include_content: bool = Query(default=False),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    _require(request, principal, LabPermission.VIEW_TRACES)
    response.headers["Cache-Control"] = "no-store"
    _audit_read(request, principal, "LAB_RUN_VIEWED", run_id)
    if include_content:
        _require(request, principal, LabPermission.VIEW_USER_CONTENT)
        _audit_read(request, principal, "LAB_RUN_CONTENT_VIEWED", run_id)
    try:
        return request.app.state.lab_queries.run_detail(run_id, include_content=include_content)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("/agents")
async def lab_agents(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    _require(request, principal, LabPermission.VIEW_AGGREGATES)
    return {"items": request.app.state.lab_queries.agents()}


@router.get("/models")
async def lab_models(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    _require(request, principal, LabPermission.VIEW_AGGREGATES)
    return {"items": request.app.state.lab_queries.models()}


@router.get("/feedback")
async def lab_feedback(
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    include_comment: bool = Query(default=False),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    _require(request, principal, LabPermission.VIEW_AGGREGATES)
    response.headers["Cache-Control"] = "no-store"
    if include_comment:
        _require(request, principal, LabPermission.VIEW_FEEDBACK_COMMENTS)
        _audit_read(request, principal, "LAB_FEEDBACK_COMMENT_VIEWED")
    return {"items": request.app.state.lab_queries.feedback(
        limit=limit, include_comment=include_comment), "next_cursor": None}


@router.get("/evidence/metrics")
async def lab_evidence_metrics(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    _require(request, principal, LabPermission.VIEW_AGGREGATES)
    return request.app.state.lab_queries.evidence_metrics()


@router.get("/safety/reviews")
async def lab_safety_reviews(
    request: Request, response: Response,
    principal: AuthenticatedPrincipal = Depends(require_principal)
):
    _require(request, principal, LabPermission.VIEW_TRACES)
    response.headers["Cache-Control"] = "no-store"
    return request.app.state.lab_queries.safety()


@router.get("/evaluations")
async def lab_evaluations(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    _require(request, principal, LabPermission.VIEW_AGGREGATES)
    return request.app.state.lab_queries.evaluations()


@router.get("/performance")
async def lab_performance(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    _require(request, principal, LabPermission.VIEW_AGGREGATES)
    return request.app.state.lab_queries.performance()


@router.get("/health")
async def lab_health(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    _require(request, principal, LabPermission.VIEW_AGGREGATES)
    return request.app.state.lab_queries.health()


@router.get("/audit")
async def lab_audit(
    request: Request, response: Response,
    principal: AuthenticatedPrincipal = Depends(require_principal)
):
    _require(request, principal, LabPermission.VIEW_AUDIT)
    response.headers["Cache-Control"] = "no-store"
    _audit_read(request, principal, "LAB_AUDIT_VIEWED")
    return {"items": request.app.state.lab_queries.audit(), "status": "OK"}
