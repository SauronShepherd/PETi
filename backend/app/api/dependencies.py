from fastapi import Header, HTTPException, Request

from app.auth.models import AuthenticatedPrincipal


async def require_principal(
    request: Request, authorization: str | None = Header(default=None)
) -> AuthenticatedPrincipal:
    if (
        not authorization
        or not authorization.startswith("Bearer ")
        or not authorization[7:].strip()
    ):
        raise HTTPException(status_code=401, detail="AUTH_MISSING_TOKEN")
    try:
        identity = await request.app.state.identity_verifier.verify_bearer_token(
            authorization[7:].strip()
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=401, detail="AUTH_INVALID_TOKEN") from exc
    user = request.app.state.users.get_or_create(identity.firebase_uid)
    return AuthenticatedPrincipal(
        identity.firebase_uid,
        user.id,
        user.role.value,
        user.billing_exempt,
        user.ads_exempt,
        user.internal_persona_code,
    )
