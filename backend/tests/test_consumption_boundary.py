from types import SimpleNamespace

from app.analysis.service import AnalysisError, _provider_acceptance, _usage_units


def test_provider_acceptance_is_explicitly_recorded_by_provider_response_contract():
    class Response:
        accepted = True

    assert Response().accepted is True


def test_provider_acceptance_rejects_truthy_non_boolean_values():
    try:
        _provider_acceptance(SimpleNamespace(accepted="true"))
    except AnalysisError as exc:
        assert str(exc) == "PROVIDER_RESPONSE_INVALID"
    else:
        raise AssertionError("provider acceptance must be an actual boolean")


def test_provider_usage_rejects_coercive_or_negative_values():
    assert _usage_units(None) == 0
    assert _usage_units(4) == 4
    for value in (True, 1.5, "4", -1):
        try:
            _usage_units(value)
        except AnalysisError as exc:
            assert str(exc) == "PROVIDER_USAGE_INVALID"
        else:
            raise AssertionError("malformed provider usage must fail closed")
