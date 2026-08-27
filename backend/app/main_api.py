"""Compatibility import for deployments that refer to the API module directly."""

from app.api.v1 import router

__all__ = ["router"]
