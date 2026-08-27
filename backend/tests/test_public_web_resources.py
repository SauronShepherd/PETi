import json
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_firebase_hosting_publishes_release_web_resources():
    config = json.loads((ROOT / "firebase.json").read_text(encoding="utf-8"))
    hosting = config["hosting"]
    assert hosting["public"] == "release/prod/web"
    for name in ("index.html", "privacy.html", "delete-account.html"):
        page = ROOT / hosting["public"] / name
        assert page.is_file()
        assert page.read_text(encoding="utf-8").lower().count("<html") == 1
