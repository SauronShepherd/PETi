from pathlib import Path


def test_ad_sdk_initialization_is_confined_to_funding_flow():
    android = Path("android/app/src/main/java/com/peti/app")
    main = (android / "MainActivity.kt").read_text()
    funding = Path(
        "android/features/funding/src/main/java/com/peti/app/funding/FundingModels.kt"
    ).read_text()
    assert "MobileAds" not in main
    assert "MobileAds.initialize" in funding
