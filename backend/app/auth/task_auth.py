from dataclasses import dataclass


@dataclass(frozen=True)
class TaskIdentity:
    service_account: str
    audience: str


class TaskAuthenticationError(ValueError):
    pass


class TaskAuthenticator:
    def __init__(
        self,
        expected_service_account: str | None = None,
        expected_audience: str | None = None,
        local: bool = True,
        token_verifier=None,
    ):
        self.expected_service_account, self.expected_audience, self.local = (
            expected_service_account,
            expected_audience,
            local,
        )
        self.token_verifier = token_verifier or self._google_token_verifier

    @staticmethod
    def _google_token_verifier(token: str, audience: str) -> dict:
        from google.auth.transport import requests
        from google.oauth2 import id_token

        return id_token.verify_oauth2_token(token, requests.Request(), audience=audience)

    def verify_bearer(self, authorization: str | None) -> TaskIdentity:
        if (
            not isinstance(authorization, str)
            or not authorization.startswith("Bearer ")
            or not authorization[7:].strip()
        ):
            raise TaskAuthenticationError("TASK_AUTHENTICATION_REQUIRED")
        if not self.expected_audience:
            raise TaskAuthenticationError("TASK_AUDIENCE_REQUIRED")
        try:
            claims = self.token_verifier(authorization[7:], self.expected_audience)
        except Exception as exc:
            raise TaskAuthenticationError("TASK_SERVICE_IDENTITY_INVALID") from exc
        if not isinstance(claims, dict):
            raise TaskAuthenticationError("TASK_SERVICE_IDENTITY_INVALID")
        service_identity = claims.get("email") or claims.get("sub")
        if not isinstance(service_identity, str) or not service_identity.strip():
            raise TaskAuthenticationError("TASK_SERVICE_IDENTITY_INVALID")
        if self.expected_service_account and service_identity != self.expected_service_account:
            raise TaskAuthenticationError("TASK_SERVICE_IDENTITY_INVALID")
        return TaskIdentity(service_identity, self.expected_audience)

    def verify(self, service_identity: str | None, audience: str | None) -> TaskIdentity:
        if self.local:
            if service_identity == "floci-cloud-tasks" and (
                audience is None or isinstance(audience, str)
            ):
                return TaskIdentity(service_identity, audience or "local")
            raise TaskAuthenticationError("TASK_SERVICE_IDENTITY_INVALID")
        if not isinstance(service_identity, str) or not service_identity.strip():
            raise TaskAuthenticationError("TASK_AUTHENTICATION_REQUIRED")
        if not isinstance(audience, str) or not audience.strip():
            raise TaskAuthenticationError("TASK_AUTHENTICATION_REQUIRED")
        if self.expected_service_account and service_identity != self.expected_service_account:
            raise TaskAuthenticationError("TASK_SERVICE_IDENTITY_INVALID")
        if self.expected_audience and audience != self.expected_audience:
            raise TaskAuthenticationError("TASK_AUDIENCE_INVALID")
        return TaskIdentity(service_identity, audience)
