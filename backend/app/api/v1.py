# mypy: ignore-errors
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.agent_runtime.queue import AgentQueueError
from app.agents.contracts import RunState
from app.analysis.service import AnalysisError
from app.auth.models import AuthenticatedPrincipal
from app.credits.domain import OperationType
from app.credits.service import FundingError
from app.future.service import FutureDomainError
from app.media.domain import MediaPurpose, MediaType, RetentionClass
from app.media.service import MediaError
from app.phase6 import CareItem, SourceClass
from app.privacy.service import PrivacyError
from app.records.vault import RecordVaultError
from app.reports.service import ReportError
from app.specialists.service import SpecialistError

from .dependencies import require_principal

router = APIRouter(prefix="/v1")


def _local_phase6(request: Request):
    if request.app.state.settings.environment.value != "LOCAL":
        raise HTTPException(status_code=404, detail="Not found")
    return request.app.state.phase6


@router.post("/internal/local/notifications/dispatch")
def dispatch_local_notifications(request: Request):
    phase6 = _local_phase6(request)
    deliveries = phase6.dispatch_due(sender=phase6.local_fcm_sender)
    return {
        "deliveries": [p6_public(delivery) for delivery in deliveries],
        "inbox": phase6.local_fcm_inbox_snapshot(),
    }


@router.get("/internal/local/notifications/inbox")
def get_local_notification_inbox(request: Request):
    phase6 = _local_phase6(request)
    return {"inbox": phase6.local_fcm_inbox_snapshot()}


@router.post("/internal/local/maintenance")
def run_local_maintenance(request: Request):
    """Run the emulator equivalent of scheduled maintenance jobs.

    Production uses Cloud Scheduler/Tasks; LOCAL exposes the same operations
    so retention, expired grants, and notification delivery are testable.
    """
    _local_phase6(request)
    now = datetime.now(UTC)
    expired_media = request.app.state.retention.expire_due(now)
    abandoned_uploads = request.app.state.retention.expire_abandoned_uploads(now)
    expired_credits = request.app.state.credits.expire(now)
    deliveries = request.app.state.phase6.dispatch_due(
        now=now, sender=request.app.state.phase6.local_fcm_sender
    )
    return {
        "expired_media": expired_media,
        "abandoned_uploads": abandoned_uploads,
        "expired_credits": expired_credits,
        "notification_deliveries": [p6_public(item) for item in deliveries],
    }


@router.post("/internal/tasks/media-maintenance")
async def run_media_maintenance_task(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service_identity: str | None = Header(default=None, alias="X-Task-Service-Identity"),
    audience: str | None = Header(default=None, alias="X-Task-Audience"),
):
    """Authenticated scheduled sweep for retention and abandoned uploads."""
    try:
        authenticator = getattr(
            request.app.state,
            "maintenance_task_authenticator",
            request.app.state.task_authenticator,
        )
        if request.app.state.settings.environment.value == "LOCAL":
            authenticator.verify(service_identity, audience)
        else:
            authenticator.verify_bearer(authorization)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    now = datetime.now(UTC)
    return {
        "expired_media": request.app.state.retention.expire_due(now),
        "abandoned_uploads": request.app.state.retention.expire_abandoned_uploads(now),
    }


async def _verify_maintenance(request, authorization, service_identity, audience):
    authenticator = getattr(request.app.state, "maintenance_task_authenticator", request.app.state.task_authenticator)
    if request.app.state.settings.environment.value == "LOCAL":
        authenticator.verify(service_identity, audience)
    else:
        authenticator.verify_bearer(authorization)


@router.post("/internal/tasks/lab-rollup")
async def run_lab_rollup_task(request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service_identity: str | None = Header(default=None, alias="X-Task-Service-Identity"),
    audience: str | None = Header(default=None, alias="X-Task-Audience")):
    if not request.app.state.settings.lab_rollups_enabled:
        raise HTTPException(status_code=404, detail="LAB_ROLLUPS_NOT_ENABLED")
    try: await _verify_maintenance(request, authorization, service_identity, audience)
    except ValueError as exc: raise HTTPException(status_code=401, detail=str(exc)) from exc
    items = request.app.state.lab_operations.recompute_rollups()
    return {"status": "COMPLETED", "rollups_written": len(items)}


@router.post("/internal/tasks/lab-retention")
async def run_lab_retention_task(request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service_identity: str | None = Header(default=None, alias="X-Task-Service-Identity"),
    audience: str | None = Header(default=None, alias="X-Task-Audience")):
    if not request.app.state.settings.lab_enabled:
        raise HTTPException(status_code=404, detail="LAB_NOT_ENABLED")
    try: await _verify_maintenance(request, authorization, service_identity, audience)
    except ValueError as exc: raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {"status": "COMPLETED", **request.app.state.lab_operations.expire()}


@router.post("/internal/tasks/notifications")
async def dispatch_task_notifications(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service_identity: str | None = Header(default=None, alias="X-Task-Service-Identity"),
    audience: str | None = Header(default=None, alias="X-Task-Audience"),
):
    try:
        if request.app.state.settings.environment.value == "LOCAL":
            request.app.state.task_authenticator.verify(service_identity, audience)
            sender = request.app.state.phase6.local_fcm_sender
        else:
            request.app.state.task_authenticator.verify_bearer(authorization)
            sender = request.app.state.phase6_sender
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if sender is None:
        raise HTTPException(status_code=503, detail="NOTIFICATION_DELIVERY_UNAVAILABLE")
    deliveries = request.app.state.phase6.dispatch_due(sender=sender)
    return {"deliveries": [p6_public(delivery) for delivery in deliveries]}


@router.post("/internal/tasks/specialist")
async def complete_specialist_task(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service_identity: str | None = Header(default=None, alias="X-Task-Service-Identity"),
    audience: str | None = Header(default=None, alias="X-Task-Audience"),
):
    try:
        if request.app.state.settings.environment.value == "LOCAL":
            request.app.state.task_authenticator.verify(service_identity, audience)
        else:
            request.app.state.task_authenticator.verify_bearer(authorization)
    except SpecialistError as exc:
        specialist_error(exc)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    try:
        body = await request.json()
        analysis = request.app.state.specialists.complete_task(body["owner_user_id"], body["analysis_id"], body["result"], body.get("provider", "GEMINI"), body.get("provider_model", "cloud-specialist"))
        return {"status": "completed", "analysis_id": analysis.id}
    except SpecialistError as exc:
        specialist_error(exc)


@router.post("/internal/tasks/record-extraction")
async def complete_record_extraction_task(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    service_identity: str | None = Header(default=None, alias="X-Task-Service-Identity"),
    audience: str | None = Header(default=None, alias="X-Task-Audience"),
):
    """Persist a worker-validated DocumentExtractionV1 as candidates only."""
    try:
        if request.app.state.settings.environment.value == "LOCAL":
            request.app.state.task_authenticator.verify(service_identity, audience)
        else:
            request.app.state.task_authenticator.verify_bearer(authorization)
    except RecordVaultError as exc:
        record_error(exc)
    except (KeyError, TypeError) as exc:
        raise HTTPException(400, "RECORD_EXTRACTION_FAILED") from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    try:
        body = await request.json()
        document = request.app.state.records.extract(
            body["owner_user_id"], body["record_id"], body["extraction"], body.get("analysis_id")
        )
        return {"status": "review_required", "record_id": document.id}
    except RecordVaultError as exc:
        record_error(exc)
    except (KeyError, TypeError) as exc:
        raise HTTPException(400, "RECORD_EXTRACTION_FAILED") from exc


class MeasurementRequest(BaseModel):
    measurement_type: str
    original_value: str
    original_unit: str
    source_class: str = SourceClass.MEASURED
    measured_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=500)
    source_document_id: str | None = Field(default=None, max_length=200)


class CareRequest(BaseModel):
    category: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=120)
    due_at: datetime
    repeat_days: int | None = Field(default=None, ge=1, le=365)
    notes: str | None = Field(default=None, max_length=500)
    notification_enabled: bool = True
    timezone: str = "UTC"
    repeat_frequency: str = "ONCE"
    repeat_interval: int = Field(default=1, ge=1, le=365)
    day_of_month: int | None = Field(default=None, ge=1, le=31)


class NotificationPreferencesPatch(BaseModel):
    care_notifications_enabled: bool | None = None
    timezone: str | None = None
    quiet_hours: dict | None = None


class DeviceRegistrationRequest(BaseModel):
    installation_id: str = Field(min_length=1, max_length=200)
    fcm_token: str = Field(min_length=1, max_length=4096)
    platform: str = "WEB"
    app_version: str = ""
    notifications_permission_state: str = "UNKNOWN"


def p6_error(exc: ValueError):
    code = str(exc)
    status = 404 if code in {"PET_NOT_FOUND", "CARE_OCCURRENCE_NOT_FOUND"} else 400
    raise HTTPException(status, code) from exc


def p6_public(value):
    result = value
    from dataclasses import asdict

    payload = asdict(result)
    if isinstance(result, CareItem):
        payload["active"] = result.deleted_at is None
    return payload


def record_public(value):
    from dataclasses import asdict
    return asdict(value)


def record_error(exc: RecordVaultError):
    code = str(exc)
    status = 404 if code in {"PET_NOT_FOUND", "RECORD_NOT_FOUND", "CANDIDATE_FACT_NOT_FOUND", "DOCUMENTED_FACT_NOT_FOUND"} else 409 if code in {"RECORD_DELETE_DEPENDENCIES_EXIST", "CANDIDATE_FACT_ALREADY_REVIEWED"} else 400
    raise HTTPException(status, code) from exc


def specialist_error(exc: SpecialistError):
    code = str(exc)
    status = 404 if code.endswith("NOT_FOUND") or code == "SPECIALIST_PET_NOT_FOUND" else 409 if "ALREADY_REVIEWED" in code or "IDEMPOTENCY" in code else 402 if "FUNDING" in code else 422 if "MEDIA" in code or "SPECIES" in code or "REQUIRED" in code or "NOT_AVAILABLE" in code or "CAPTURE" in code else 400
    raise HTTPException(status, code) from exc


def specialist_public(value):
    from dataclasses import asdict
    return asdict(value)


def report_error(exc: ReportError):
    code = str(exc)
    raise HTTPException(404 if code.endswith("NOT_FOUND") else 400, code) from exc


def future_error(exc: FutureDomainError):
    raise HTTPException(404 if str(exc).endswith("NOT_FOUND") else 400, str(exc)) from exc


@router.post("/pets/{pet_id}/exports", status_code=202)
async def create_pet_export(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.export(principal.user_id, pet_id))
    except FutureDomainError as exc: future_error(exc)


@router.get("/exports/{export_id}")
async def get_pet_export(export_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.owned(principal.user_id, export_id, "EXPORT"))
    except FutureDomainError as exc: future_error(exc)


@router.delete("/exports/{export_id}")
async def delete_pet_export(export_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.delete(principal.user_id, export_id, "EXPORT"))
    except FutureDomainError as exc: future_error(exc)


@router.post("/exports/{export_id}/shares", status_code=201)
async def share_pet_export(export_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.share(principal.user_id, export_id, body))
    except FutureDomainError as exc: future_error(exc)


@router.get("/shares")
async def list_shares(request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return [request.app.state.future.public(x) for x in request.app.state.future.list(principal.user_id, "SHARE")]


@router.delete("/shares/{share_id}")
async def delete_share(share_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.delete(principal.user_id, share_id, "SHARE"))
    except FutureDomainError as exc: future_error(exc)


@router.post("/imports", status_code=202)
async def create_import(body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return request.app.state.future.public(request.app.state.future.import_item(principal.user_id, body))


@router.get("/imports/{import_id}")
async def get_import(import_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.owned(principal.user_id, import_id, "IMPORT"))
    except FutureDomainError as exc: future_error(exc)


@router.post("/imports/{import_id}/confirm")
async def confirm_import(import_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return request.app.state.future.public(request.app.state.future.transition(principal.user_id, import_id, "IMPORT", "CONFIRMED"))
    except FutureDomainError as exc: future_error(exc)


@router.delete("/imports/{import_id}")
async def delete_import(import_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.delete(principal.user_id, import_id, "IMPORT"))
    except FutureDomainError as exc: future_error(exc)


@router.post("/search")
async def search_history(body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return {
            "query": body.get("query", ""),
            "results": request.app.state.search.search(
                principal.user_id,
                body.get("query", ""),
                body.get("pet_id"),
                body.get("entity_type"),
                body.get("source"),
                body.get("limit", 50),
            ),
        }
    except FutureDomainError as exc: future_error(exc)


@router.get("/pets/{pet_id}/memory")
async def pet_memory(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        if not request.app.state.pets.get(principal.user_id, pet_id):
            raise HTTPException(404, "PET_NOT_FOUND")
        from dataclasses import asdict
        return {
            "pet_id": pet_id,
            "items": request.app.state.future.search(principal.user_id, "", pet_id),
            "personal_memories": [asdict(item) for item in request.app.state.memory.list(principal.user_id, pet_id)],
        }
    except FutureDomainError as exc: future_error(exc)


@router.get("/saved-searches")
async def list_saved_searches(request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return [request.app.state.future.public(x) for x in request.app.state.future.list(principal.user_id, "SAVED_SEARCH")]


@router.post("/saved-searches", status_code=201)
async def create_saved_search(body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return request.app.state.future.public(request.app.state.future.create(principal.user_id, "SAVED_SEARCH", body.get("pet_id"), {"query": body.get("query", ""), "name": body.get("name", "Saved search")}))


@router.patch("/saved-searches/{search_id}")
async def patch_saved_search(search_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.update(principal.user_id, search_id, "SAVED_SEARCH", {k: body[k] for k in ("query", "name") if k in body}))
    except FutureDomainError as exc: future_error(exc)


@router.delete("/saved-searches/{search_id}")
async def delete_saved_search(search_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.delete(principal.user_id, search_id, "SAVED_SEARCH"))
    except FutureDomainError as exc: future_error(exc)


@router.get("/pets/{pet_id}/collections")
async def list_pet_collections(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: request.app.state.future.assert_pet(principal.user_id, pet_id); return [request.app.state.future.public(x) for x in request.app.state.future.list(principal.user_id, "COLLECTION", pet_id)]
    except FutureDomainError as exc: future_error(exc)


@router.post("/pets/{pet_id}/collections", status_code=201)
async def create_pet_collection(pet_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.create(principal.user_id, "COLLECTION", pet_id, {"name": body.get("name", "Collection"), "item_ids": body.get("item_ids", [])}))
    except FutureDomainError as exc: future_error(exc)


@router.patch("/collections/{collection_id}")
async def patch_collection(collection_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.update(principal.user_id, collection_id, "COLLECTION", {k: body[k] for k in ("name", "item_ids") if k in body}))
    except FutureDomainError as exc: future_error(exc)


@router.delete("/collections/{collection_id}")
async def delete_collection(collection_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.delete(principal.user_id, collection_id, "COLLECTION"))
    except FutureDomainError as exc: future_error(exc)


@router.post("/pets/{pet_id}/assistant/threads", status_code=201)
async def create_assistant_thread(pet_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.create(principal.user_id, "ASSISTANT_THREAD", pet_id, {"title": body.get("title", "Pet history"), "messages": []}))
    except FutureDomainError as exc: future_error(exc)


@router.get("/assistant/threads")
async def list_assistant_threads(request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return [request.app.state.future.public(x) for x in request.app.state.future.list(principal.user_id, "ASSISTANT_THREAD")]


@router.get("/assistant/threads/{thread_id}")
async def get_assistant_thread(thread_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.owned(principal.user_id, thread_id, "ASSISTANT_THREAD"))
    except FutureDomainError as exc: future_error(exc)


@router.post("/assistant/threads/{thread_id}/messages")
async def add_assistant_message(thread_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.assistant_message(principal.user_id, thread_id, body)
    except FutureDomainError as exc: future_error(exc)


@router.delete("/assistant/threads/{thread_id}")
async def delete_assistant_thread(thread_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.delete(principal.user_id, thread_id, "ASSISTANT_THREAD"))
    except FutureDomainError as exc: future_error(exc)


@router.get("/pets/{pet_id}/members")
async def list_pet_members(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: request.app.state.future.assert_pet(principal.user_id, pet_id); return [request.app.state.future.public(x) for x in request.app.state.future.list(principal.user_id, "MEMBERSHIP", pet_id)]
    except FutureDomainError as exc: future_error(exc)


@router.post("/pets/{pet_id}/invitations", status_code=201)
async def invite_caregiver(pet_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.create_invitation(principal.user_id, pet_id, body.get("invitee"), body.get("role", "CAREGIVER"), body.get("ttl_hours", 72))
    except FutureDomainError as exc: future_error(exc)


@router.delete("/pets/{pet_id}/invitations/{invitation_id}")
async def revoke_caregiver_invitation(pet_id: str, invitation_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.delete(principal.user_id, invitation_id, "INVITATION"))
    except FutureDomainError as exc: future_error(exc)


@router.post("/invitations/{token}/accept")
async def accept_invitation(token: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        item = request.app.state.future.consume_invitation(token, principal.user_id)
        return request.app.state.future.public(request.app.state.future.create(principal.user_id, "MEMBERSHIP", item.pet_id, {"role": item.payload.get("role", "CAREGIVER"), "invitation_id": item.id}))
    except FutureDomainError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/pets/{pet_id}/automation-rules")
async def list_automation_rules(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: request.app.state.future.assert_pet(principal.user_id, pet_id); return [request.app.state.future.public(x) for x in request.app.state.future.list(principal.user_id, "AUTOMATION_RULE", pet_id)]
    except FutureDomainError as exc: future_error(exc)


@router.post("/pets/{pet_id}/automation-rules", status_code=201)
async def create_automation_rule(pet_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    enabled = body.get("enabled", True)
    if not isinstance(enabled, bool):
        raise HTTPException(400, "AUTOMATION_ENABLED_FLAG_INVALID")
    try: return request.app.state.future.public(request.app.state.future.create(principal.user_id, "AUTOMATION_RULE", pet_id, {"trigger": body.get("trigger"), "action": body.get("action"), "enabled": enabled}))
    except FutureDomainError as exc: future_error(exc)


@router.get("/automation-rules/{rule_id}")
async def get_automation_rule(rule_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.owned(principal.user_id, rule_id, "AUTOMATION_RULE"))
    except FutureDomainError as exc: future_error(exc)


@router.patch("/automation-rules/{rule_id}")
async def patch_automation_rule(rule_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    if "enabled" in body and not isinstance(body["enabled"], bool):
        raise HTTPException(400, "AUTOMATION_ENABLED_FLAG_INVALID")
    try: return request.app.state.future.public(request.app.state.future.update(principal.user_id, rule_id, "AUTOMATION_RULE", {k: body[k] for k in ("trigger", "action", "enabled") if k in body}))
    except FutureDomainError as exc: future_error(exc)


@router.delete("/automation-rules/{rule_id}")
async def delete_automation_rule(rule_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.delete(principal.user_id, rule_id, "AUTOMATION_RULE"))
    except FutureDomainError as exc: future_error(exc)


@router.get("/pets/{pet_id}/automation-suggestions")
async def automation_suggestions(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: request.app.state.future.assert_pet(principal.user_id, pet_id); return [request.app.state.future.public(x) for x in request.app.state.future.list(principal.user_id, "AUTOMATION_SUGGESTION", pet_id)]
    except FutureDomainError as exc: future_error(exc)


@router.post("/automation-suggestions/{suggestion_id}/accept")
async def accept_automation_suggestion(suggestion_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.transition(principal.user_id, suggestion_id, "AUTOMATION_SUGGESTION", "ACCEPTED"))
    except FutureDomainError as exc: future_error(exc)


@router.post("/automation-suggestions/{suggestion_id}/reject")
async def reject_automation_suggestion(suggestion_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.transition(principal.user_id, suggestion_id, "AUTOMATION_SUGGESTION", "REJECTED"))
    except FutureDomainError as exc: future_error(exc)


@router.get("/care-templates")
async def list_care_templates(request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return [request.app.state.future.public(x) for x in request.app.state.future.list(principal.user_id, "CARE_TEMPLATE")]


@router.post("/pets/{pet_id}/care-templates", status_code=201)
async def create_care_template(pet_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.future.public(request.app.state.future.create(principal.user_id, "CARE_TEMPLATE", pet_id, body))
    except FutureDomainError as exc: future_error(exc)


@router.get("/pets/{pet_id}/reports")
async def list_weekly_reports(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return [request.app.state.reports.public(x) for x in request.app.state.reports.list(principal.user_id, pet_id)]
    except ReportError as exc:
        report_error(exc)


@router.get("/me/export")
async def export_account_data(request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return request.app.state.privacy.export(principal.user_id)


@router.delete("/me/account")
async def delete_account_data(request: Request, confirm: bool = False, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return request.app.state.privacy.delete_account(principal.user_id, confirm, idempotency_key)
    except PrivacyError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/me/account-deletion/{idempotency_key}")
async def account_deletion_status(idempotency_key: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return request.app.state.privacy.deletion_status(principal.user_id, idempotency_key)
    except PrivacyError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/reports/{report_id}")
async def get_weekly_report(report_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return request.app.state.reports.public(request.app.state.reports.get(principal.user_id, report_id))
    except ReportError as exc:
        report_error(exc)


@router.post("/internal/reports/weekly/generate")
async def generate_weekly_report(body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        animal_id = body["animal_id"]
        timezone = body.get("timezone", "UTC")
        week_key = body.get("week_key") or request.app.state.reports.key(
            animal_id, datetime.now(UTC), timezone
        ).week_key
        idempotency_key = body.get("idempotency_key") or f"weekly-report:{principal.user_id}:{animal_id}:{week_key}"
        dispatched = request.app.state.reports.dispatch_week(
            principal.user_id, animal_id, week_key, idempotency_key=idempotency_key
        )
        report = dispatched.get("report")
        return request.app.state.reports.public(report) if report is not None else dispatched
    except (ReportError, KeyError) as exc:
        report_error(ReportError(str(exc)))


@router.get("/support/code")
async def get_support_code(request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return request.app.state.operations.public(request.app.state.operations.support_code(principal.user_id))


@router.post("/support/cases", status_code=201)
async def create_support_case(body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return request.app.state.operations.public(request.app.state.operations.report_problem(principal.user_id, body))


@router.get("/pets/{pet_id}/capabilities")
async def pet_capabilities(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    request.app.state.pets.get(principal.user_id, pet_id) or (_ for _ in ()).throw(HTTPException(404, "PET_NOT_FOUND"))
    pet = request.app.state.pets.get(principal.user_id, pet_id)
    return request.app.state.capabilities.public(request.app.state.capabilities.resolve(getattr(pet, "species", "DOG")))


@router.post("/pets/{pet_id}/care-records", status_code=201)
async def create_advanced_care_record(pet_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        item = request.app.state.care_advanced.create(principal.user_id, pet_id, body.get("record_type", ""), body.get("payload", {}), body.get("source", "OWNER_ENTERED"))
        return {"id": item.id, "pet_id": item.pet_id, "record_type": item.record_type, "payload": item.payload, "source": item.source, "status": item.status}
    except ValueError as exc:
        raise HTTPException(404 if str(exc) == "PET_NOT_FOUND" else 409, str(exc)) from exc


@router.get("/pets/{pet_id}/care-records")
async def list_advanced_care_records(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return [x.__dict__ for x in request.app.state.care_advanced.list(principal.user_id, pet_id, request.query_params.get("record_type"))]
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc


@router.patch("/care-records/{record_id}")
async def update_advanced_care_record(record_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        item = request.app.state.care_advanced.update(principal.user_id, record_id, body.get("payload", {}))
        return {"id": item.id, "pet_id": item.pet_id, "record_type": item.record_type, "payload": item.payload, "source": item.source, "status": item.status}
    except ValueError as exc:
        raise HTTPException(409 if str(exc) != "CARE_RECORD_NOT_FOUND" else 404, str(exc)) from exc


@router.get("/pets/{pet_id}/longitudinal-bundle")
async def longitudinal_bundle(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return request.app.state.care_advanced.longitudinal_bundle(principal.user_id, pet_id)


@router.post("/pets/{pet_id}/portable-export")
async def portable_export(pet_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    include_raw_media = body.get("include_raw_media", False)
    if not isinstance(include_raw_media, bool):
        raise HTTPException(400, "EXPORT_RAW_MEDIA_FLAG_INVALID")
    try:
        return request.app.state.portability.export(principal.user_id, pet_id, include_raw_media)
    except ValueError as exc:
        if str(exc) == "PET_NOT_FOUND":
            raise HTTPException(404, "PET_NOT_FOUND") from exc
        raise HTTPException(409, str(exc)) from exc


@router.post("/pets/{pet_id}/shares", status_code=201)
async def create_portable_share(pet_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    if not request.app.state.pets.get(principal.user_id, pet_id):
        raise HTTPException(404, "PET_NOT_FOUND")
    try:
        ttl_hours = body.get("ttl_hours", 24)
        if isinstance(ttl_hours, bool) or not isinstance(ttl_hours, int):
            raise TypeError("SHARE_POLICY_INVALID")
        return request.app.state.portability.create_share(
            principal.user_id, pet_id, body.get("scope", "READ_ONLY"), ttl_hours
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(400, "SHARE_POLICY_INVALID") from exc


@router.post("/portable-imports", status_code=202)
async def preview_portable_import(body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return request.app.state.portability.import_preview(principal.user_id, body)


@router.post("/agent/runs", status_code=202)
async def create_agent_run(body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    pet_id = body.get("pet_id")
    if not pet_id:
        raise HTTPException(400, "PET_ID_REQUIRED_USE_CANONICAL_DOG_ROUTE")
    try:
        request.app.state.pets.get(principal.user_id, pet_id) or (_ for _ in ()).throw(ValueError("DOG_NOT_FOUND"))
        run = request.app.state.agents.create_run(principal.user_id, body.get("goal", ""), pet_id,
            body.get("agent_type", "ORCHESTRATOR"), session_id=body.get("session_id"),
            interaction_id=request.state.interaction_id, correlation_id=request.state.correlation_id,
            deployment_id=request.app.state.settings.deployment_revision)
        if request.app.state.settings.lab_enabled: request.app.state.lab_tracing.create_run(run)
        request.app.state.agent_queue.enqueue_agent(run_id=run.id, owner_user_id=principal.user_id,
            media_asset_ids=list(body.get("media_asset_ids", [])), context=body.get("context"))
        return run.public()
    except AgentQueueError as exc:
        if 'run' in locals():
            request.app.state.agents._set_state(run, RunState.WAITING); request.app.state.agents._persist_run(run)
        raise HTTPException(409, "AGENT_QUEUE_SUBMISSION_FAILED") from exc
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc


@router.get("/agent/runs/{run_id}")
async def get_agent_run(run_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.agents.get(principal.user_id, run_id).public()
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc


@router.post("/agent/runs/{run_id}/cancel")
async def cancel_agent_run(run_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.agents.cancel(principal.user_id, run_id).public()
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc


@router.post("/pets/{pet_id}/assistant/grounded-answer")
async def grounded_answer(pet_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.assistant.answer(principal.user_id, pet_id, body.get("question", ""))
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc


@router.post("/pets/{pet_id}/collaboration/memberships", status_code=201)
async def grant_collaboration_membership(pet_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        item = request.app.state.collaboration.grant(principal.user_id, pet_id, body.get("member_user_id", ""), body.get("role", "CAREGIVER"), body.get("ttl_hours"))
        return {"id": item.id, "pet_id": item.pet_id, "member_user_id": item.member_user_id, "role": item.role, "status": item.status, "expires_at": item.expires_at}
    except ValueError as exc: raise HTTPException(409, str(exc)) from exc


@router.post("/collaboration/memberships/{membership_id}/revoke")
async def revoke_collaboration_membership(membership_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try: return request.app.state.collaboration.revoke(principal.user_id, membership_id)
    except ValueError as exc: raise HTTPException(404, str(exc)) from exc


@router.get("/internal/ops/metrics")
async def operations_metrics(request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    if str(principal.role) != "ADMIN":
        raise HTTPException(403, "ADMIN_REQUIRED")
    return request.app.state.operations.metrics()


@router.get("/internal/ops/feature-flags")
async def feature_flags(request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    if str(principal.role) != "ADMIN":
        raise HTTPException(403, "ADMIN_REQUIRED")
    return dict(request.app.state.operations.flags)


@router.post("/internal/ops/feature-flags/ai-global-kill-switch")
async def set_ai_global_kill_switch(
    body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    if str(principal.role) != "ADMIN":
        raise HTTPException(403, "ADMIN_REQUIRED")
    if not isinstance(body.get("enabled"), bool):
        raise HTTPException(422, "AI_KILL_SWITCH_ENABLED_REQUIRED")
    enabled = request.app.state.operations.set_ai_global_kill_switch(
        body["enabled"], str(principal.role)
    )
    request.app.state.analysis.set_global_kill_switch(enabled)
    return {"ai_global_kill_switch": enabled, "ai_enabled": request.app.state.analysis.ai_enabled}


@router.post("/internal/ops/feature-flags/ai-scoped-kill-switch")
async def set_ai_scoped_kill_switch(
    body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    if str(principal.role) != "ADMIN":
        raise HTTPException(403, "ADMIN_REQUIRED")
    scope, key, enabled = body.get("scope"), body.get("key"), body.get("enabled")
    if scope not in {"provider", "model", "species"} or not isinstance(key, str) or not isinstance(enabled, bool):
        raise HTTPException(422, "AI_SCOPED_KILL_SWITCH_INVALID")
    try:
        result = request.app.state.analysis.set_runtime_kill_switch(scope, key, enabled)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    request.app.state.operations.set_scoped_flags(
        scope, dict(getattr(request.app.state.analysis, f"{scope}_kill_switches")), str(principal.role)
    )
    return {"scope": scope, "key": key, "enabled": result}


@router.post("/internal/ops/feature-flags/variable-cost-intake")
async def set_variable_cost_intake(
    body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    if str(principal.role) != "ADMIN":
        raise HTTPException(403, "ADMIN_REQUIRED")
    if not isinstance(body.get("enabled"), bool):
        raise HTTPException(422, "VARIABLE_COST_INTAKE_ENABLED_REQUIRED")
    enabled = request.app.state.operations.set_variable_cost_intake(body["enabled"], str(principal.role))
    return {"variable_cost_intake_enabled": enabled}


def _specialist_routes(analysis_type, singular, plural, candidate_prefix=None):
    @router.post(f"/pets/{{pet_id}}/{plural}", status_code=202, name=f"create_{singular}")
    async def create_specialist(pet_id: str, body: dict, request: Request, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), principal: AuthenticatedPrincipal = Depends(require_principal)):
        try:
            # Provider output and provenance are worker-owned. Never forward
            # client-controlled completion fields into the domain service.
            forbidden = {"result", "provider", "provider_model", "provider_config_version", "prompt_version", "schema_version", "guardrail_version", "safety_version", "evaluation_certificate_id"}
            if forbidden.intersection(body):
                raise SpecialistError("SPECIALIST_PROVIDER_OUTPUT_SERVER_ONLY")
            request_body = {key: value for key, value in body.items() if key not in forbidden}
            return specialist_public(request.app.state.specialists.create(principal.user_id, pet_id, analysis_type, request_body, idempotency_key, principal.billing_exempt))
        except SpecialistError as exc:
            specialist_error(exc)

    @router.get(f"/{plural}/{{analysis_id}}", name=f"get_{singular}")
    async def get_specialist(analysis_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
        try:
            return specialist_public(request.app.state.specialists.get(principal.user_id, analysis_id))
        except SpecialistError as exc:
            specialist_error(exc)

    @router.get(f"/pets/{{pet_id}}/{plural}", name=f"list_{singular}")
    async def list_specialist(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
        try:
            return [specialist_public(x) for x in request.app.state.specialists.list(principal.user_id, pet_id, analysis_type)]
        except SpecialistError as exc:
            specialist_error(exc)

_specialist_routes("DOG_DENTAL_CHECK", "dental_check", "dental-checks")
_specialist_routes("DOG_FECES_CHECK", "feces_check", "feces-checks")
_specialist_routes("DOG_BODY_CHECK", "body_check", "body-checks")


@router.delete("/dental-checks/{check_id}")
async def delete_dental_check(check_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return specialist_public(request.app.state.specialists.delete(principal.user_id, check_id))
    except SpecialistError as exc:
        specialist_error(exc)


@router.post("/pets/{pet_id}/initial-scans", status_code=202)
async def create_initial_scan(pet_id: str, body: dict, request: Request, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return specialist_public(request.app.state.specialists.create(principal.user_id, pet_id, "DOG_INITIAL_SCAN", body, idempotency_key, principal.billing_exempt))
    except SpecialistError as exc:
        specialist_error(exc)


@router.get("/initial-scans/{scan_id}")
async def get_initial_scan(scan_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return specialist_public(request.app.state.specialists.get(principal.user_id, scan_id))
    except SpecialistError as exc:
        specialist_error(exc)


@router.delete("/initial-scans/{scan_id}")
async def delete_initial_scan(scan_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return specialist_public(request.app.state.specialists.delete(principal.user_id, scan_id))
    except SpecialistError as exc:
        specialist_error(exc)


@router.get("/pets/{pet_id}/initial-scans")
async def list_initial_scans(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return [specialist_public(x) for x in request.app.state.specialists.list(principal.user_id, pet_id, "DOG_INITIAL_SCAN")]
    except SpecialistError as exc:
        specialist_error(exc)


@router.get("/initial-scans/{scan_id}/candidates")
async def list_initial_scan_candidates(scan_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return [specialist_public(x) for x in request.app.state.specialists.candidates_for(principal.user_id, scan_id)]
    except SpecialistError as exc:
        specialist_error(exc)


async def review_initial_scan_candidate(candidate_id: str, action: str, body: dict, request: Request, principal: AuthenticatedPrincipal):
    try:
        return specialist_public(request.app.state.specialists.review_initial_candidate(principal.user_id, candidate_id, action, body.get("value")))
    except SpecialistError as exc:
        specialist_error(exc)


@router.post("/initial-scan-candidates/{candidate_id}/confirm")
async def confirm_initial_scan_candidate(candidate_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return await review_initial_scan_candidate(candidate_id, "confirm", {}, request, principal)


@router.post("/initial-scan-candidates/{candidate_id}/correct")
async def correct_initial_scan_candidate(candidate_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return await review_initial_scan_candidate(candidate_id, "correct", body, request, principal)


@router.post("/initial-scan-candidates/{candidate_id}/reject")
async def reject_initial_scan_candidate(candidate_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return await review_initial_scan_candidate(candidate_id, "reject", {}, request, principal)


@router.post("/initial-scan-candidates/{candidate_id}/skip")
async def skip_initial_scan_candidate(candidate_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return await review_initial_scan_candidate(candidate_id, "skip", {}, request, principal)


@router.get("/body-checks/{check_id}/comparison")
async def body_check_comparison(check_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return request.app.state.specialists.comparison(principal.user_id, check_id)
    except SpecialistError as exc:
        specialist_error(exc)


@router.get("/feces-checks/{check_id}/comparison")
async def feces_check_comparison(check_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return request.app.state.specialists.comparison(principal.user_id, check_id)
    except SpecialistError as exc:
        specialist_error(exc)


@router.get("/pets/{pet_id}/records")
async def list_records(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return [record_public(x) for x in request.app.state.records.list(principal.user_id, pet_id)]
    except RecordVaultError as exc:
        record_error(exc)


@router.post("/pets/{pet_id}/records", status_code=201)
async def create_record(pet_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return record_public(request.app.state.records.create(principal.user_id, pet_id, body.get("source_media_id", ""), body))
    except RecordVaultError as exc:
        record_error(exc)


@router.get("/records/{record_id}")
async def get_record(record_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return record_public(request.app.state.records.get(principal.user_id, record_id))
    except RecordVaultError as exc:
        record_error(exc)


@router.patch("/records/{record_id}")
async def update_record(record_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return record_public(request.app.state.records.update(principal.user_id, record_id, body))
    except (RecordVaultError, ValueError) as exc:
        record_error(RecordVaultError(str(exc)))


@router.post("/records/{record_id}/access")
async def access_record(record_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return request.app.state.records.access(principal.user_id, record_id)
    except RecordVaultError as exc:
        record_error(exc)


@router.get("/records/{record_id}/deletion-preview")
async def record_deletion_preview(record_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return request.app.state.records.deletion_preview(principal.user_id, record_id)
    except RecordVaultError as exc:
        record_error(exc)


@router.delete("/records/{record_id}")
async def delete_record(record_id: str, request: Request, confirm_dependencies: bool = False, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return request.app.state.records.delete(principal.user_id, record_id, confirm_dependencies)
    except RecordVaultError as exc:
        record_error(exc)


@router.post("/records/{record_id}/extract", status_code=202)
async def extract_record(record_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        if body.get("fixture_text") is not None:
            _local_phase6(request)
            return record_public(request.app.state.records.extract_local_fixture(
                principal.user_id, record_id, body.get("fixture_text"), body.get("analysis_id")
            ))
        # Customer routes never accept provider output directly: that would
        # bypass Phase-2 funding and the authenticated private worker. The
        # worker may call the domain service after its own task authentication
        # and schema validation. LOCAL fixtures remain explicitly available.
        raise HTTPException(503, "RECORD_EXTRACTION_NOT_AVAILABLE")
    except RecordVaultError as exc:
        record_error(exc)


@router.get("/records/{record_id}/candidate-facts")
async def list_candidate_facts(record_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    try:
        return [record_public(x) for x in request.app.state.records.candidates_for(principal.user_id, record_id)]
    except RecordVaultError as exc:
        record_error(exc)


async def review_candidate(fact_id: str, action: str, body: dict, request: Request, principal: AuthenticatedPrincipal):
    try:
        candidate, fact = request.app.state.records.review(principal.user_id, fact_id, action, body)
        return {"candidate_fact": record_public(candidate), "documented_fact": record_public(fact) if fact else None}
    except RecordVaultError as exc:
        record_error(exc)


@router.post("/candidate-facts/{fact_id}/confirm")
async def confirm_candidate(fact_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return await review_candidate(fact_id, "CONFIRM", {}, request, principal)


@router.post("/candidate-facts/{fact_id}/correct")
async def correct_candidate(fact_id: str, body: dict, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return await review_candidate(fact_id, "CORRECT", body, request, principal)


@router.post("/candidate-facts/{fact_id}/reject")
async def reject_candidate(fact_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return await review_candidate(fact_id, "REJECT", {}, request, principal)


@router.get("/pets/{pet_id}/documented-facts")
async def list_documented_facts(pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    return [record_public(x) for x in request.app.state.records.facts_for(principal.user_id, pet_id)]


@router.get("/documented-facts/{fact_id}")
async def get_documented_fact(fact_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    item = request.app.state.records.facts.get(fact_id)
    if not item or item.owner_user_id != principal.user_id or item.deleted_at:
        raise HTTPException(404, "DOCUMENTED_FACT_NOT_FOUND")
    return record_public(item)


@router.get("/pets/{pet_id}/measurements")
async def list_measurements(
    pet_id: str,
    request: Request,
    source_class: str | None = None,
    include_ai_estimates: bool = False,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    if not request.app.state.pets.get(principal.user_id, pet_id):
        raise HTTPException(404, "PET_NOT_FOUND")
    items = [
        x
        for x in request.app.state.phase6.measurements.values()
        if x.owner_user_id == principal.user_id
        and x.animal_id == pet_id
        and not x.deleted_at
        and (source_class is None or x.source_class == source_class)
        and (include_ai_estimates or x.source_class != "AI_ESTIMATED")
    ]
    return [p6_public(x) for x in sorted(items, key=lambda x: (x.measured_at, x.id), reverse=True)]


@router.post("/pets/{pet_id}/measurements", status_code=201)
async def add_measurement(
    pet_id: str,
    body: MeasurementRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        data = body.model_dump()
        return p6_public(
            request.app.state.phase6.measurement(
                principal.user_id, pet_id, data, idempotency_key, request.app.state.pets
            )
        )
    except ValueError as exc:
        p6_error(exc)


@router.get("/pets/{pet_id}/measurements/trend")
async def measurement_trend(
    pet_id: str,
    request: Request,
    measurement_type: str | None = None,
    source_class: str | None = None,
    include_ai_estimates: bool = False,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    if not request.app.state.pets.get(principal.user_id, pet_id):
        raise HTTPException(404, "PET_NOT_FOUND")
    return request.app.state.phase6.measurement_trend(
        principal.user_id,
        pet_id,
        measurement_type,
        source_class,
        include_ai_estimates,
    )


@router.patch("/measurements/{measurement_id}")
async def patch_measurement(
    measurement_id: str,
    body: dict,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    item = request.app.state.phase6.measurements.get(measurement_id)
    if not item or item.owner_user_id != principal.user_id or item.deleted_at:
        raise HTTPException(404, "MEASUREMENT_NOT_FOUND")
    if "notes" in body:
        item.notes = body["notes"]
    request.app.state.phase6._persist("measurements", item)
    return p6_public(item)


@router.get("/pets/{pet_id}/care")
async def list_care(
    pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    if not request.app.state.pets.get(principal.user_id, pet_id):
        raise HTTPException(404, "PET_NOT_FOUND")
    items = [
        x
        for x in request.app.state.phase6.care.values()
        if x.owner_user_id == principal.user_id and x.animal_id == pet_id and not x.deleted_at
    ]
    return [p6_public(x) for x in sorted(items, key=lambda x: (x.due_at, x.id))]


@router.post("/pets/{pet_id}/care", status_code=201)
async def add_care(
    pet_id: str,
    body: CareRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        return p6_public(
            request.app.state.phase6.create_care(
                principal.user_id,
                pet_id,
                body.model_dump(),
                idempotency_key,
                request.app.state.pets,
            )
        )
    except ValueError as exc:
        p6_error(exc)


@router.patch("/care/{care_id}")
async def patch_care(
    care_id: str,
    body: dict,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        values = {}
        for field in ("category", "title", "notes", "repeat_days", "notification_enabled", "due_at", "timezone", "repeat_frequency", "repeat_interval", "day_of_month"):
            if field in body:
                value = body[field]
                if field == "due_at" and isinstance(value, str):
                    value = datetime.fromisoformat(value)
                values[field] = value
        return p6_public(request.app.state.phase6.update_care(principal.user_id, care_id, values))
    except ValueError as exc:
        p6_error(exc)


@router.get("/pets/{pet_id}/care-occurrences")
async def list_occurrences(
    pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    if not request.app.state.pets.get(principal.user_id, pet_id):
        raise HTTPException(404, "PET_NOT_FOUND")
    result = []
    for occurrence in request.app.state.phase6.occurrences.values():
        if occurrence.owner_user_id != principal.user_id or occurrence.animal_id != pet_id:
            continue
        item = p6_public(occurrence)
        item["status"] = request.app.state.phase6.occurrence_status(occurrence)
        result.append(item)
    return sorted(result, key=lambda item: (item["due_at"], item["id"]))


@router.post("/care-occurrences/{occurrence_id}/{action}")
async def care_action(
    occurrence_id: str,
    action: str,
    request: Request,
    body: dict | None = None,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    if action not in {"complete", "skip", "reschedule"}:
        raise HTTPException(404, "NOT_FOUND")
    try:
        due_at = (body or {}).get("due_at")
        if isinstance(due_at, str):
            due_at = datetime.fromisoformat(due_at)
        return p6_public(
            request.app.state.phase6.action(
                principal.user_id,
                occurrence_id,
                action,
                request.app.state.pets,
                due_at,
                idempotency_key,
            )
        )
    except ValueError as exc:
        p6_error(exc)


@router.get("/pets/{pet_id}/timeline")
async def timeline(
    pet_id: str,
    request: Request,
    before: datetime | None = None,
    after: datetime | None = None,
    item_type: str | None = None,
    limit: int = 50,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    if not request.app.state.pets.get(principal.user_id, pet_id):
        raise HTTPException(404, "PET_NOT_FOUND")
    check_items = []
    for job in request.app.state.analysis.list_owned_jobs(principal.user_id, pet_id):
        if job.analysis_type != "PETI_CHECK" or str(job.status) != "COMPLETED":
            continue
        result = request.app.state.analysis.get_owned_result(principal.user_id, job.id)
        if result is None:
            continue
        public_result = request.app.state.analysis.public_result(result)
        payload = public_result.get("structured_payload", {})
        check_items.append(
            {
                "id": "peti_check:" + job.id,
                "animal_id": pet_id,
                "occurred_at": job.completed_at or job.created_at,
                "recorded_at": job.completed_at or job.created_at,
                "item_type": "PETI_CHECK",
                "source_entity_type": "ANALYSIS_RESULT",
                "source_entity_id": result.id,
                "title": "PETi Check",
                "summary": payload.get("summary", "Completed PETi Check"),
                "provenance": "AI_ANALYSIS",
                "status": public_result.get("safety_state"),
            }
        )
    for fact in request.app.state.records.facts_for(principal.user_id, pet_id):
        check_items.append(
            {
                "id": "documented_fact:" + fact.id,
                "animal_id": pet_id,
                # Partial source dates remain strings (with date_precision);
                # use recording time only as the technical sort timestamp.
                "occurred_at": fact.event_date if isinstance(fact.event_date, datetime) else fact.created_at,
                "recorded_at": fact.created_at,
                "item_type": "DOCUMENTED_FACT",
                "source_entity_type": "DOCUMENTED_FACT",
                "source_entity_id": fact.id,
                "source_document_id": fact.source_document_id,
                "source_anchor": p6_public(fact.source_anchor) if fact.source_anchor else None,
                "title": "Documented " + fact.fact_type.replace("_", " ").title(),
                "summary": " ".join(x for x in (fact.value, fact.unit, fact.text_value) if x),
                "provenance": "DOCUMENTED",
            }
        )
    return [
        p6_public(x) if hasattr(x, "__dataclass_fields__") else x
        for x in request.app.state.phase6.timeline(
            principal.user_id,
            pet_id,
            checks=check_items,
            item_type=item_type,
            before=before,
            after=after,
            limit=limit,
        )
    ]


@router.get("/measurements/{measurement_id}")
async def get_measurement(
    measurement_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    item = request.app.state.phase6.measurements.get(measurement_id)
    if not item or item.owner_user_id != principal.user_id or item.deleted_at:
        raise HTTPException(404, "MEASUREMENT_NOT_FOUND")
    return p6_public(item)


@router.delete("/measurements/{measurement_id}", status_code=204)
async def delete_measurement(
    measurement_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    item = request.app.state.phase6.measurements.get(measurement_id)
    if not item or item.owner_user_id != principal.user_id or item.deleted_at:
        raise HTTPException(404, "MEASUREMENT_NOT_FOUND")
    item.deleted_at = request.app.state.phase6._now()
    request.app.state.phase6._persist("measurements", item)
    return Response(status_code=204)


@router.get("/care/{care_id}")
async def get_care(
    care_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    item = request.app.state.phase6.care.get(care_id)
    if not item or item.owner_user_id != principal.user_id or item.deleted_at:
        raise HTTPException(404, "CARE_NOT_FOUND")
    return p6_public(item)


@router.delete("/care/{care_id}", status_code=204)
async def delete_care(
    care_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    item = request.app.state.phase6.care.get(care_id)
    if not item or item.owner_user_id != principal.user_id or item.deleted_at:
        raise HTTPException(404, "CARE_NOT_FOUND")
    item.deleted_at = request.app.state.phase6._now()
    for occurrence in request.app.state.phase6.occurrences.values():
        if occurrence.care_id == care_id and occurrence.status == "ACTIVE":
            occurrence.status = "CANCELED"
            request.app.state.phase6._persist("care_occurrences", occurrence)
    request.app.state.phase6._persist("care_items", item)
    return Response(status_code=204)


@router.get("/me/notification-preferences")
async def get_notification_preferences(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    return p6_public(request.app.state.phase6.preferences(principal.user_id))


@router.patch("/me/notification-preferences")
async def patch_notification_preferences(
    body: NotificationPreferencesPatch,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        values = {key: value for key, value in body.model_dump().items() if value is not None}
        return p6_public(request.app.state.phase6.update_preferences(principal.user_id, values))
    except ValueError as exc:
        p6_error(exc)


@router.post("/me/devices", status_code=201)
async def register_device(
    body: DeviceRegistrationRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        return p6_public(
            request.app.state.phase6.register_device(principal.user_id, body.model_dump())
        )
    except ValueError as exc:
        p6_error(exc)


@router.delete("/me/devices/{device_id}", status_code=204)
async def deactivate_device(
    device_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    if not request.app.state.phase6.deactivate_device(principal.user_id, device_id):
        raise HTTPException(404, "NOTIFICATION_DEVICE_INVALID")
    return Response(status_code=204)


class FundingQuoteRequest(BaseModel):
    operation_type: OperationType


class ReservationRequest(BaseModel):
    operation_type: OperationType
    operation_request_id: str = Field(min_length=1)


class RewardIntentRequest(BaseModel):
    provider: str = "FAKE"


class MediaSessionRequest(BaseModel):
    animal_id: str | None = None
    media_type: MediaType
    purpose: MediaPurpose
    mime_type: str
    size_bytes: int | None = None
    retention_class: RetentionClass


class CreateAnalysisRequest(BaseModel):
    animal_id: str
    analysis_type: str = "PLATFORM_MULTIMODAL_SMOKE"
    media_asset_ids: list[str] = Field(min_length=1, max_length=5)
    user_context: str | None = Field(default=None, max_length=500)
    funding_reservation_id: str


def funding_error(exc: FundingError):
    status = 402 if str(exc) == "FUNDING_REQUIRED" else 409
    raise HTTPException(status, str(exc)) from exc


def analysis_error(exc: AnalysisError):
    code = str(exc)
    status = 404 if code in {"ANALYSIS_NOT_FOUND", "ANALYSIS_ANIMAL_NOT_FOUND"} else 409
    if code in {
        "ANALYSIS_MEDIA_NOT_READY",
        "ANALYSIS_MEDIA_NOT_OWNED",
        "ANALYSIS_FUNDING_INVALID",
        "ANALYSIS_TYPE_UNAVAILABLE_FOR_SPECIES",
        "ANALYSIS_PROVIDER_MEDIA_UNSUPPORTED",
        "ANALYSIS_PROVIDER_MEDIA_LIMIT",
        "PETI_CHECK_MEDIA_UNSUPPORTED",
    }:
        status = 422
    raise HTTPException(status, code) from exc


@router.post("/pets/{pet_id}/analyses", status_code=202)
async def create_analysis(
    pet_id: str,
    body: CreateAnalysisRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    if pet_id != body.animal_id:
        raise HTTPException(422, "ANALYSIS_ANIMAL_MISMATCH")
    try:
        job = request.app.state.analysis.create(
            principal.user_id,
            body.animal_id,
            body.analysis_type,
            body.media_asset_ids,
            body.user_context,
            body.funding_reservation_id,
            idempotency_key,
            request.state.correlation_id,
        )
        return request.app.state.analysis.public_job(job)
    except AnalysisError as exc:
        analysis_error(exc)


@router.get("/analyses/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    job = request.app.state.analysis.get_owned_job(principal.user_id, analysis_id)
    if not job:
        raise HTTPException(404, "ANALYSIS_NOT_FOUND")
    data = request.app.state.analysis.public_job(job)
    result = request.app.state.analysis.get_owned_result(principal.user_id, job.id)
    if result:
        data["result"] = request.app.state.analysis.public_result(result)
    return data


@router.delete("/analyses/{analysis_id}")
async def cancel_analysis(
    analysis_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        return request.app.state.analysis.public_job(
            request.app.state.analysis.cancel(principal.user_id, analysis_id)
        )
    except AnalysisError as exc:
        analysis_error(exc)


@router.get("/pets/{pet_id}/analyses")
async def list_analyses(
    pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    return [
        request.app.state.analysis.public_job(x)
        for x in request.app.state.analysis.list_owned_jobs(principal.user_id, pet_id)
    ]


@router.post("/pets/{pet_id}/checks", status_code=202)
async def create_peti_check(
    pet_id: str,
    body: CreateAnalysisRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    settings = getattr(request.app.state, "settings", None)
    if settings is not None and not (
        settings.peti_check_enabled or settings.environment.value == "LOCAL"
    ):
        raise HTTPException(503, "PETI_CHECK_NOT_AVAILABLE")
    if pet_id != body.animal_id:
        raise HTTPException(422, "PETI_CHECK_PET_MISMATCH")
    body.analysis_type = "PETI_CHECK"
    try:
        job = request.app.state.analysis.create(
            principal.user_id,
            pet_id,
            "PETI_CHECK",
            body.media_asset_ids,
            body.user_context,
            body.funding_reservation_id,
            idempotency_key,
            request.state.correlation_id,
        )
        request.app.state.analytics.record(
            "check_submitted", user_id=principal.user_id, check_id=job.id
        )
        return request.app.state.analysis.public_job(job)
    except AnalysisError as exc:
        code = str(exc).replace("ANALYSIS_", "PETI_CHECK_")
        if code == "PETI_CHECK_TYPE_UNAVAILABLE_FOR_SPECIES":
            code = "PETI_CHECK_NOT_AVAILABLE_FOR_SPECIES"
        raise HTTPException(422, code) from exc


@router.get("/pets/{pet_id}/checks")
async def list_peti_checks(
    pet_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    jobs = [
        x
        for x in request.app.state.analysis.list_owned_jobs(principal.user_id, pet_id)
        if x.analysis_type == "PETI_CHECK"
    ]
    jobs.sort(key=lambda x: x.created_at, reverse=True)
    output = []
    for job in jobs:
        item = request.app.state.analysis.public_job(job)
        result = request.app.state.analysis.get_owned_result(principal.user_id, job.id)
        if result:
            item["result"] = request.app.state.analysis.public_result(result)
        output.append(item)
    return output


@router.post("/internal/tasks/analysis")
async def run_analysis_task(
    request: Request,
    x_task_identity: str | None = Header(default=None, alias="X-Task-Identity"),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    try:
        if x_task_identity:
            request.app.state.task_authenticator.verify(
                x_task_identity, request.headers.get("X-Task-Audience")
            )
        else:
            request.app.state.task_authenticator.verify_bearer(authorization)
    except ValueError as exc:
        raise HTTPException(401, str(exc)) from exc
    body = await request.json()
    try:
        result = request.app.state.analysis.process(body["job_id"])
        return {
            "status": "completed",
            "job_id": body["job_id"],
            "result_id": result.id if result else None,
        }
    except AnalysisError as exc:
        analysis_error(exc)


@router.get("/credits")
async def credits(request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    request.app.state.credits.materialize_allowance(principal.user_id)
    grants = [
        g for g in request.app.state.credits.grants.values() if g.user_id == principal.user_id
    ]
    return {
        "available_credits": sum(g.remaining_amount - g.reserved_amount for g in grants),
        "reserved_credits": sum(g.reserved_amount for g in grants),
        "grants": [
            {
                "id": g.id,
                "source": g.source,
                "remaining_amount": g.remaining_amount,
                "expires_at": g.expires_at,
            }
            for g in grants
        ],
    }


@router.get("/credits/history")
async def credit_history(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    return [e.__dict__ for e in request.app.state.credits.ledger if e.user_id == principal.user_id]


@router.post("/funding/quote")
async def funding_quote(
    body: FundingQuoteRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    if principal.billing_exempt:
        return {
            "required_credits": 0,
            "currently_fundable": True,
            "available_credits": 0,
            "additional_credits_required": 0,
            "operation_type": body.operation_type,
        }
    try:
        quote = request.app.state.credits.quote(principal.user_id, body.operation_type)
        if body.operation_type == OperationType.PETI_CHECK and not quote["currently_fundable"]:
            request.app.state.analytics.record("check_funding_required", user_id=principal.user_id)
        return quote
    except FundingError as exc:
        funding_error(exc)


@router.post("/funding/reservations", status_code=201)
async def reserve_funding(
    body: ReservationRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    if not idempotency_key:
        raise HTTPException(400, "IDEMPOTENCY_KEY_REQUIRED")
    if principal.billing_exempt:
        return {"status": "RESERVED", "requested_amount": 0, "funding_source": "ADMIN_EXEMPT"}
    try:
        r = request.app.state.credits.reserve(
            principal.user_id, body.operation_type, body.operation_request_id, idempotency_key
        )
        return {
            "id": r.id,
            "status": r.status,
            "requested_amount": r.requested_amount,
            "allocation": [a.__dict__ for a in r.allocation],
        }
    except FundingError as exc:
        funding_error(exc)


@router.post("/funding/reservations/{reservation_id}/consume")
async def consume_funding(
    reservation_id: str,
    request: Request,
    execution_id: str = Header(..., alias="Execution-Id"),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        return request.app.state.credits.consume(reservation_id, execution_id).__dict__
    except FundingError as exc:
        funding_error(exc)


@router.post("/funding/reservations/{reservation_id}/release")
async def release_funding(
    reservation_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        return request.app.state.credits.release(reservation_id).__dict__
    except FundingError as exc:
        funding_error(exc)


@router.get("/internal/credits/audit")
async def credit_audit(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    if principal.role != "ADMIN":
        raise HTTPException(403, "FORBIDDEN")
    return request.app.state.credits.audit()


class PetCreate(BaseModel):
    display_name: str = Field(min_length=1)
    species: str = Field(min_length=1)


class PetPatch(BaseModel):
    display_name: str | None = Field(default=None, min_length=1)


def pet_dict(p):
    return {
        "id": p.id,
        "owner_user_id": p.owner_user_id,
        "species": p.species,
        "display_name": p.display_name,
        # A new pet has no completed profile or derived health data.
        "profile_complete": bool(getattr(p, "profile_field_provenance", {})),
        "active_state": p.active_state.value,
        "avatar_media_id": p.avatar_media_id,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "deleted_at": p.deleted_at,
    }


@router.get("/me")
async def me(request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)):
    user = request.app.state.users.get_or_create(principal.firebase_uid)
    return {
        "id": user.id,
        "role": user.role.value,
        "billing_exempt": user.billing_exempt,
        "ads_exempt": user.ads_exempt,
        "internal_persona_code": user.internal_persona_code,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


@router.get("/species")
async def species(request: Request):
    return [
        {
            "species_code": x.species_code,
            "display_name": x.display_name,
            "profile_enabled": x.profile_enabled,
            "public_enabled": x.public_enabled,
            "capability_pack_version": x.capability_pack_version,
        }
        for x in request.app.state.species.list_public_profile_species()
    ]


@router.get("/species/{species_code}/capabilities")
async def capabilities(species_code: str, request: Request):
    pack = request.app.state.species.get_capability_pack(species_code)
    if not pack:
        raise HTTPException(404, "SPECIES_NOT_FOUND")
    return {
        "species": pack.species,
        "version": pack.version,
        "profile_enabled": pack.profile_enabled,
        "supported_analysis_types": pack.supported_analysis_types,
        "enabled_analysis_types": pack.enabled_analysis_types,
        "taxonomy_versions": pack.taxonomy_versions,
        "safety_policy_version": pack.safety_policy_version,
        "evaluation_certificate_ids": pack.evaluation_certificate_ids,
        "public_enabled": pack.public_enabled,
    }


@router.get("/pets")
async def list_pets(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    return [pet_dict(p) for p in request.app.state.pets.list(principal.user_id)]


@router.post("/pets", status_code=201)
async def create_pet(
    body: PetCreate,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        return pet_dict(
            request.app.state.pets.create(
                principal.user_id, body.display_name, body.species, idempotency_key
            )
        )
    except ValueError as exc:
        raise HTTPException(409 if str(exc).startswith("IDEMPOTENCY") else 400, str(exc)) from exc


@router.get("/pets/{pet_id}")
async def get_pet(
    pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    pet = request.app.state.pets.get(principal.user_id, pet_id)
    if not pet:
        raise HTTPException(404, "PET_NOT_FOUND")
    return pet_dict(pet)


@router.patch("/pets/{pet_id}")
async def update_pet(
    pet_id: str,
    body: PetPatch,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        pet = request.app.state.pets.update(principal.user_id, pet_id, body.display_name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not pet:
        raise HTTPException(404, "PET_NOT_FOUND")
    return pet_dict(pet)


@router.delete("/pets/{pet_id}", status_code=204)
async def delete_pet(
    pet_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    if not request.app.state.pets.delete(principal.user_id, pet_id):
        raise HTTPException(404, "PET_NOT_FOUND")
    return Response(status_code=204)


@router.post("/ads/reward-intents", status_code=201)
async def create_reward_intent(
    body: RewardIntentRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    if principal.ads_exempt:
        raise HTTPException(409, "REWARDED_AD_NOT_REQUIRED")
    decision = request.app.state.abuse_guard.check_and_record(principal.user_id)
    if not decision.allowed:
        raise HTTPException(
            429, decision.code, headers={"Retry-After": str(decision.retry_after_seconds)}
        )
    intent = request.app.state.rewards.create_intent(principal.user_id, body.provider)
    return {
        "id": intent.id,
        "nonce": intent.nonce,
        "expected_credit_amount": intent.expected_credit_amount,
        "provider": intent.provider,
        "status": intent.status,
        "expires_at": intent.expires_at,
    }


@router.get("/ads/reward-intents/{intent_id}")
async def get_reward_intent(
    intent_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    intent = request.app.state.rewards.get_intent(principal.user_id, intent_id)
    if not intent:
        raise HTTPException(404, "REWARD_INTENT_NOT_FOUND")
    return intent.__dict__


@router.get("/ads/google/rewarded-ssv")
async def google_rewarded_ssv(
    request: Request,
):
    status, amount = request.app.state.rewards.verify_google_query(request.url.query)
    return {"verification_status": status, "reward_amount": amount}


def media_dict(asset):
    return {
        "id": asset.id,
        "owner_user_id": asset.owner_user_id,
        "animal_id": asset.animal_id,
        "media_type": asset.media_type,
        "purpose": asset.purpose,
        "mime_type": asset.mime_type_declared,
        "size_bytes": asset.size_bytes_verified or asset.size_bytes_declared,
        "status": asset.status,
        "retention_class": asset.retention_class,
        "created_at": asset.created_at,
        "finalized_at": asset.finalized_at,
    }


@router.post("/media/upload-sessions", status_code=201)
async def create_media_session(
    body: MediaSessionRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    if not idempotency_key:
        raise HTTPException(400, "IDEMPOTENCY_KEY_REQUIRED")
    try:
        asset, session = request.app.state.media.create_session(
            principal.user_id,
            body.animal_id,
            body.media_type,
            body.purpose,
            body.mime_type,
            body.size_bytes,
            body.retention_class,
            idempotency_key,
        )
        request.app.state.retention.apply_policy(asset)
        auth = request.app.state.media.storage.create_upload_authorization(
            asset.storage_bucket, asset.storage_object, asset.mime_type_declared
        )
        return {
            "media_asset": media_dict(asset),
            "upload_session_id": session.id,
            "strategy": session.strategy,
            "upload_authorization": auth,
        }
    except MediaError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/media")
async def list_media(
    request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    return [media_dict(a) for a in request.app.state.media.list_owned(principal.user_id)]


@router.get("/media/{media_id}")
async def get_media(
    media_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    asset = request.app.state.media.get_owned(principal.user_id, media_id)
    if not asset:
        raise HTTPException(404, "MEDIA_NOT_FOUND")
    return media_dict(asset)


@router.post("/media/{media_id}/finalize")
async def finalize_media(
    media_id: str,
    request: Request,
    session_id: str = Header(..., alias="Upload-Session-Id"),
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        return media_dict(request.app.state.media.finalize(principal.user_id, media_id, session_id))
    except MediaError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/media/{media_id}/access")
async def access_media(
    media_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    try:
        return request.app.state.media.access(principal.user_id, media_id)
    except MediaError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/media/{media_id}/upload-authorization")
async def refresh_media_authorization(
    media_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    asset = request.app.state.media.get_owned(principal.user_id, media_id)
    if not asset:
        raise HTTPException(404, "MEDIA_NOT_FOUND")
    return request.app.state.media.storage.create_upload_authorization(
        asset.storage_bucket, asset.storage_object, asset.mime_type_declared
    )


@router.patch("/media/{media_id}/retention")
async def change_media_retention(
    media_id: str,
    body: dict,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_principal),
):
    try:
        return media_dict(
            request.app.state.retention.change_class(
                principal.user_id, media_id, body.get("retention_class")
            )
        )
    except (MediaError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.delete("/media/{media_id}")
async def delete_media(
    media_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_principal)
):
    try:
        return media_dict(request.app.state.media.delete(principal.user_id, media_id))
    except MediaError as exc:
        raise HTTPException(404, str(exc)) from exc
