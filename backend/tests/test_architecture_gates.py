from pathlib import Path


def test_android_build_files_have_no_local_ai_dependencies():
    root = Path(__file__).parents[2] / "android"
    for path in root.rglob("*"):
        if path.name not in {"build.gradle.kts", "build.gradle", "libs.versions.toml"}:
            continue
        text = path.read_text(encoding="utf-8").lower()
        assert not any(token in text for token in ("tflite", "litert", "tensorflow", "com.google.ai.", "generativeai"))
