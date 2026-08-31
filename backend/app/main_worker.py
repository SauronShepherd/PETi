"""Private Cloud Run worker entry point.

Only the task callback and liveness endpoint are exposed by this service. The
public customer API is intentionally not mounted here.
"""

from fastapi import FastAPI, Header, HTTPException, Request

from .ai.preparation.core import MediaPreparer
from .main import app as api_app

app = FastAPI(title="PETi Analysis Worker", version="0.1.0")


@app.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok", "service": "peti-analysis-worker"}


@app.get("/health/ready")
async def ready() -> dict[str, str]:
    return {"status": "ok", "service": "peti-analysis-worker"}


@app.post("/internal/tasks/analysis")
async def run_analysis_task(
    request: Request,
    x_task_identity: str | None = Header(default=None, alias="X-Task-Identity"),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    try:
        if x_task_identity:
            api_app.state.task_authenticator.verify(
                x_task_identity, request.headers.get("X-Task-Audience")
            )
        else:
            api_app.state.task_authenticator.verify_bearer(authorization)
    except ValueError as exc:
        raise HTTPException(401, str(exc)) from exc
    body = await request.json()
    result = api_app.state.analysis.process(body["job_id"])
    return {
        "status": "completed",
        "job_id": body["job_id"],
        "result_id": result.id if result else None,
    }


@app.post("/internal/tasks/specialist")
async def run_specialist_task(
    request: Request,
    x_task_identity: str | None = Header(default=None, alias="X-Task-Identity"),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    try:
        if x_task_identity:
            api_app.state.task_authenticator.verify(x_task_identity, request.headers.get("X-Task-Audience"))
        else:
            api_app.state.task_authenticator.verify_bearer(authorization)
    except ValueError as exc:
        raise HTTPException(401, str(exc)) from exc
    body = await request.json()
    analysis = api_app.state.specialists.complete_task(
        body["owner_user_id"], body["analysis_id"], body["result"], body.get("provider", "GEMINI"), body.get("provider_model", "cloud-specialist")
    )
    return {"status": "completed", "analysis_id": analysis.id}


@app.post("/internal/tasks/specialist-gemini")
async def run_gemini_specialist_task(
    request: Request,
    x_task_identity: str | None = Header(default=None, alias="X-Task-Identity"),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    """Run specialist inference server-side, then reuse specialist validation."""
    try:
        if x_task_identity:
            api_app.state.task_authenticator.verify(
                x_task_identity, request.headers.get("X-Task-Audience")
            )
        else:
            api_app.state.task_authenticator.verify_bearer(authorization)
    except ValueError as exc:
        raise HTTPException(401, str(exc)) from exc
    body = await request.json()
    analysis_id = body["analysis_id"]
    specialist = api_app.state.specialists.get_by_id_internal(analysis_id)
    owner_user_id = specialist.owner_user_id
    analysis_type = specialist.analysis_type
    # Tasks carry only the durable asset identifiers. Resolve ownership,
    # lifecycle, MIME, storage and animal scope at execution time.
    resolved_media = api_app.state.media.resolve_ai_media(
        owner_user_id, specialist.media_asset_ids, specialist.animal_id
    )
    media = MediaPreparer().prepare(resolved_media)
    prompt = (
        f"You are the PETi {analysis_type} specialist. Return JSON observations only. "
        "Include evidence quality, uncertainty, limitations, provenance, and safety guidance. "
        "Never diagnose, prescribe, or claim disease is ruled out."
    )
    response = api_app.state.analysis.provider.analyze(media, prompt, body.get("context"))
    analysis = api_app.state.specialists.complete_task_internal(
        analysis_id, response.payload,
        response.provider, response.model,
    )
    return {
        "status": "completed",
        "analysis_id": analysis.id,
        "provider": response.provider,
        "model": response.model,
        "request_id": response.usage.provider_request_id,
    }


@app.post("/internal/tasks/agent")
async def run_agent_task(
    request: Request,
    x_task_identity: str | None = Header(default=None, alias="X-Task-Identity"),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    """Execute one owner-scoped agent run from a Cloud Tasks OIDC delivery."""
    try:
        if x_task_identity:
            api_app.state.task_authenticator.verify(
                x_task_identity, request.headers.get("X-Task-Audience")
            )
        else:
            api_app.state.task_authenticator.verify_bearer(authorization)
    except ValueError as exc:
        raise HTTPException(401, str(exc)) from exc
    body = await request.json()
    owner = body["owner_user_id"]
    run = api_app.state.agents.get(owner, body["run_id"])
    if not run.pet_id:
        raise HTTPException(409, "AGENT_PET_REQUIRED")
    resolved_media = api_app.state.media.resolve_ai_media(
        owner, body.get("media_asset_ids", []), run.pet_id
    )
    media = MediaPreparer().prepare(resolved_media)
    result = api_app.state.agent_execution.execute(
        owner, body["run_id"], media, context=body.get("context")
    )
    return {"status": "completed", "run_id": body["run_id"], "state": result["state"]}
