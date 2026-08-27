from app.config.settings import Environment


def test_local_is_the_only_environment_allowed_to_use_fake_queue():
    assert Environment.LOCAL.value == "LOCAL"
    assert Environment.PRODUCTION.value != "LOCAL"
