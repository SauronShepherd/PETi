from app.auth.models import AuthenticatedPrincipal

from .enums import LabPermission

ADMIN_READ_PERMISSIONS = frozenset(
    {
        LabPermission.VIEW_AGGREGATES,
        LabPermission.VIEW_TRACES,
        LabPermission.VIEW_USER_CONTENT,
        LabPermission.VIEW_FEEDBACK_COMMENTS,
        LabPermission.REVIEW_CASES,
        LabPermission.VIEW_AUDIT,
    }
)


def permissions_for(principal: AuthenticatedPrincipal, environment: str) -> frozenset[LabPermission]:
    if principal.role == "ADMIN":
        return ADMIN_READ_PERMISSIONS
    if principal.role == "INTERNAL_TEST" and environment != "PRODUCTION":
        return frozenset({LabPermission.VIEW_AGGREGATES, LabPermission.VIEW_TRACES})
    return frozenset()


def require_permission(
    principal: AuthenticatedPrincipal, permission: LabPermission, environment: str
) -> None:
    if permission not in permissions_for(principal, environment):
        raise PermissionError("LAB_PERMISSION_REQUIRED")

