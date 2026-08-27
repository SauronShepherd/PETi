from app.future.service import FutureService


class Pets:
    @staticmethod
    def get(_owner, _pet_id):
        return object()


class UnavailableStore:
    @staticmethod
    def all(_collection):
        raise RuntimeError("temporary outage")


def test_future_hydration_does_not_crash_when_store_is_temporarily_unavailable():
    service = FutureService(Pets(), store=UnavailableStore())
    assert service.items == {}
