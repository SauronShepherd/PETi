"""Verify the funding boundary without starting Gradle."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_BUILD = ROOT / "android" / "app" / "build.gradle.kts"
FUNDING_BUILD = ROOT / "android" / "features" / "funding" / "build.gradle.kts"
FUNDING_SRC = ROOT / "android" / "features" / "funding" / "src" / "main"


def main() -> int:
    app = APP_BUILD.read_text(encoding="utf-8")
    funding = FUNDING_BUILD.read_text(encoding="utf-8")
    if "play-services-ads" in app:
        raise SystemExit("Free build must not depend on Ads")
    if 'project(":features:funding")' not in app:
        raise SystemExit(":app must depend on :features:funding")
    if "play-services-ads" in funding:
        raise SystemExit("Free build must not include the Ads dependency")
    gateway = list(FUNDING_SRC.rglob("FundingModels.kt"))
    if not gateway or "UnavailableRewardedAdGateway" not in gateway[0].read_text(encoding="utf-8"):
        raise SystemExit("RewardedAdGateway implementation missing from funding module")
    print("ANDROID_FUNDING_MODULE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
