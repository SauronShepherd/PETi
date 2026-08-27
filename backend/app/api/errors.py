from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse


@dataclass
class PetiError(Exception):
    code: str
    message: str
    retryable: bool = False
    status_code: int = 400
    correlation_id: str | None = None


async def error_handler(request: Request, exc: PetiError) -> JSONResponse:
    correlation_id = exc.correlation_id or getattr(request.state, "correlation_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "correlation_id": correlation_id or "unknown",
            "retryable": exc.retryable,
        },
    )
