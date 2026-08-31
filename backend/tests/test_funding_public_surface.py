from app.api.v1 import router


def test_credit_consume_and_release_are_not_customer_routes():
    paths = {route.path for route in router.routes}
    assert "/v1/funding/reservations/{reservation_id}/consume" not in paths
    assert "/v1/funding/reservations/{reservation_id}/release" not in paths
