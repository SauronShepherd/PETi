from types import SimpleNamespace

from app.collaboration.service import Membership
from app.privacy.service import PrivacyService


def test_collaboration_membership_export_and_deletion_cover_owner_and_caregiver():
    membership = Membership("owner-1", "caregiver-1", "pet-1", "CAREGIVER", id="membership-1")
    collaboration = SimpleNamespace(memberships={"membership-1": membership}, store=None)
    privacy = PrivacyService(
        pets=SimpleNamespace(list=lambda owner: []), media=SimpleNamespace(list_owned=lambda owner: []),
        phase6=SimpleNamespace(measurements={}, care={}), collaboration=collaboration,
    )
    caregiver_export = privacy.export("caregiver-1")
    assert caregiver_export["collaboration_memberships"][0]["member_user_id"] == "caregiver-1"
    privacy._perform_delete_account("caregiver-1", privacy.deletion_planner.plan("caregiver-1", "delete-1"))
    assert membership.status == "REVOKED"
