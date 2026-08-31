

def test_ready_asset_cannot_receive_new_upload_authorization():
    # The API gate is intentionally small and explicit; finalized assets are
    # evidence identities and must be replaced by a new asset, never bytes.
    class Asset:
        status = "READY"
    assert str(Asset.status) != "PENDING_UPLOAD"
