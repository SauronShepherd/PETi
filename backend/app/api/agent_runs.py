"""Dedicated agent API router boundary; mounted by deployments that expose agent v1."""
from fastapi import APIRouter, Depends, HTTPException, Request

from app.ai.preparation.core import MediaPreparationError, MediaPreparer
from app.auth.models import AuthenticatedPrincipal

from .dependencies import require_principal

router = APIRouter(prefix="/v1")


@router.post("/dogs/{dog_id}/agent-sessions", status_code=201)
async def create_agent_session(dog_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        request.app.state.pets.get(principal.user_id, dog_id) or (_ for _ in ()).throw(ValueError("DOG_NOT_FOUND"))
        return request.app.state.agents.create_session(principal.user_id, dog_id).__dict__
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc


@router.get("/dogs/{dog_id}/agent-sessions/{session_id}")
async def get_agent_session(dog_id: str, session_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        session = request.app.state.agents.get_session(principal.user_id, session_id)
        if session.pet_id != dog_id: raise ValueError("AGENT_SESSION_PET_MISMATCH")
        return session.__dict__
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc


@router.post("/dogs/{dog_id}/agent-runs", status_code=202)
async def create_dog_agent_run(dog_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        request.app.state.pets.get(principal.user_id, dog_id) or (_ for _ in ()).throw(ValueError("DOG_NOT_FOUND"))
        return request.app.state.agents.create_run(principal.user_id, body.get("goal", ""), dog_id, body.get("agent_type", "ORCHESTRATOR"), session_id=body.get("session_id")).public()
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc


@router.get("/agent-runs/{run_id}")
async def get_dog_agent_run(run_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.agents.get(principal.user_id, run_id).public()
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc


@router.post("/agent-runs/{run_id}/cancel")
async def cancel_dog_agent_run(run_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.agents.cancel(principal.user_id, run_id).public()
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc


@router.post("/agent-runs/{run_id}/execute")
async def execute_dog_agent_run(run_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    """Execute the bounded provider-backed plan for a queued run.

    Production callers normally invoke this through an authenticated Cloud
    Tasks worker; the endpoint remains useful for local and staging vertical
    slices and never accepts raw provider credentials.
    """
    try:
        run = request.app.state.agents.get(principal.user_id, run_id)
        if not run.pet_id:
            raise ValueError("AGENT_PET_REQUIRED")
        resolved_media = request.app.state.media.resolve_ai_media(
            principal.user_id, body.get("media_asset_ids", []), run.pet_id
        )
        media = MediaPreparer().prepare(resolved_media)
        return request.app.state.agent_execution.execute(
            principal.user_id, run_id, media, context=body.get("context")
        )
    except (ValueError, MediaPreparationError) as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/agent-runs/{run_id}/evidence")
async def get_agent_evidence(run_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return {"run_id": run_id, "evidence": [item.__dict__ for item in request.app.state.agents.get(principal.user_id, run_id).evidence]}
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc


@router.get("/agent-runs/{run_id}/provenance")
async def get_agent_provenance(run_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        run = request.app.state.agents.get(principal.user_id, run_id)
        return {"run_id": run.id, "policy_snapshot": run.policy_snapshot, "agent_type": run.agent_type}
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc


@router.post("/agent-runs/{run_id}/context-requests/{request_id}/responses")
async def respond_agent_context(run_id: str, request_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.agents.respond_context(principal.user_id, run_id, request_id, body.get("resource_refs", []))
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc


@router.post("/agent-runs/{run_id}/actions/{action_id}/approve")
async def approve_agent_action(run_id: str, action_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.agents.decide_action(principal.user_id, run_id, action_id, True)
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc


@router.post("/agent-runs/{run_id}/actions/{action_id}/reject")
async def reject_agent_action(run_id: str, action_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.agents.decide_action(principal.user_id, run_id, action_id, False)
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc


@router.get("/dogs/{dog_id}/observation-plans")
async def list_observation_plans(dog_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    request.app.state.pets.get(principal.user_id, dog_id) or (_ for _ in ()).throw(HTTPException(404, "DOG_NOT_FOUND"))
    return [x for x in getattr(request.app.state.agents, "observation_plans", {}).values() if x.owner_user_id == principal.user_id and x.pet_id == dog_id]
