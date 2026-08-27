import json
from importlib.util import module_from_spec, spec_from_file_location


def load_checker():
    spec = spec_from_file_location("check_production_config", "scripts/check_production_config.py")
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_config(root, flags):
    (root / "release").mkdir()
    (root / "release/PRODUCTION_CONFIG_SNAPSHOT.json").write_text(
        json.dumps({"contains_secrets": False, "environment": "PRODUCTION"}), encoding="utf-8"
    )
    (root / "release/PRODUCTION_FEATURE_FLAGS.json").write_text(json.dumps(flags), encoding="utf-8")


def test_production_config_accepts_empty_fail_closed_specialists(tmp_path, capsys):
    checker = load_checker()
    write_config(tmp_path, {"global_ai_enabled": False, "assistant": {"enabled": False}, "specialists": {}})
    checker.ROOT = tmp_path

    assert checker.main() == 0
    assert "PASS_SECRET_FREE_FAIL_CLOSED" in capsys.readouterr().out


def test_production_config_rejects_public_specialist(tmp_path, capsys):
    checker = load_checker()
    write_config(
        tmp_path,
        {
            "global_ai_enabled": False,
            "assistant": {"enabled": False},
            "specialists": {"DOG_INITIAL_SCAN": {"enabled": True, "public_enabled": True}},
        },
    )
    checker.ROOT = tmp_path

    assert checker.main() == 1
    assert "specialist must remain disabled" in capsys.readouterr().out
