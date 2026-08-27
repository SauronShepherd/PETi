from app.privacy.lifecycle import (
    DeletionResidualVerifier,
    MediaStorageResidualInventory,
    OwnerCollectionResidualInventory,
)


def test_residual_verifier_queries_independent_inventory_not_caller_counts():
    verifier = DeletionResidualVerifier({"gcs": lambda owner: 1, "firestore": lambda owner: 0})
    result = verifier.verify("u", {"gcs": 0, "firestore": 0})
    assert result["verified"] is False
    assert result["residuals"] == {"gcs": 1}


def test_residual_verifier_preserves_caller_counts_for_uninventoried_domains():
    verifier = DeletionResidualVerifier({"gcs": lambda owner: 0})
    result = verifier.verify("u", {"gcs": 0, "firestore": 2})
    assert result["verified"] is False
    assert result["residuals"] == {"firestore": 2}


def test_residual_verifier_accepts_zero_independent_inventory():
    verifier = DeletionResidualVerifier({"gcs": lambda owner: 0, "firestore": lambda owner: 0})
    assert verifier.verify("u", {"gcs": 99})["verified"] is True


def test_media_inventory_probes_canonical_storage_not_caller_counts():
    class Metadata:
        def list_owned(self, owner):
            return [
                {"storage_bucket": "b", "storage_object": "media/one"},
                {"storage_bucket": "b", "storage_object": "media/gone"},
            ]

    class Storage:
        def stat_object(self, bucket, name):
            return object() if name == "media/one" else None

    verifier = DeletionResidualVerifier(
        {"media_objects": MediaStorageResidualInventory(Metadata(), Storage())}
    )
    result = verifier.verify("u", {"media_objects": 0})
    assert result["residuals"] == {"media_objects": 1}
    assert result["verified"] is False


def test_owner_collection_inventory_counts_non_deleted_documents():
    class Store:
        def list_owned(self, collection, owner):
            assert collection == "measurements"
            return [{"owner_user_id": owner}, {"owner_user_id": owner, "deleted_at": "now"}]

    assert OwnerCollectionResidualInventory(Store(), "measurements")("u") == 1


def test_owner_collection_inventory_supports_dataclass_like_documents():
    class Item:
        def __init__(self, deleted_at=None):
            self.deleted_at = deleted_at

    class Store:
        def list_owned(self, collection, owner):
            return [Item(), Item("now")]

    assert OwnerCollectionResidualInventory(Store(), "records")("u") == 1
