from pathlib import Path


def test_free_build_contains_no_ad_sdk_initialization():
    android = Path("android/app/src/main/java/com/peti/app")
    main = (android / "MainActivity.kt").read_text()
    funding = Path(
        "android/features/funding/src/main/java/com/peti/app/funding/FundingModels.kt"
    ).read_text()
    assert "MobileAds" not in main
    assert "MobileAds" not in funding
    assert "com.google.android.gms.ads" not in funding
