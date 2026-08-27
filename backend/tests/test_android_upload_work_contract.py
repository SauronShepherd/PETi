from pathlib import Path


def test_upload_retries_use_unique_work_per_local_upload():
    source = Path("android/app/src/main/java/com/peti/app/media/MediaUploadCoordinator.kt").read_text()
    assert "enqueueUniqueWork" in source
    assert "ExistingWorkPolicy.KEEP" in source
    assert '"peti-upload-$localId"' in source
    assert ".enqueue(request)" not in source
