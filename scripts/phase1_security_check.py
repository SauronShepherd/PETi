import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
release = root / "android" / "app" / "build" / "outputs" / "apk" / "release" / "app-release.apk"
if release.exists():
    forbidden = ("local-test:", "service-account", "AI" + "za", "google-services.json", "firestore")
    with zipfile.ZipFile(release) as apk:
        names = "\n".join(apk.namelist()).lower()
        assert not any(marker.lower() in names for marker in forbidden), "forbidden release artifact marker"
        for entry in apk.namelist():
            if entry.endswith(('.dex', '.xml', '.properties')):
                data = apk.read(entry).decode('latin1', errors='ignore').lower()
                assert "local-test:" not in data, f"test auth marker in {entry}"
print("Phase 1 release security inspection passed")
