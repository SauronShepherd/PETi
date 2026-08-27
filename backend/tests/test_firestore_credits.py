from datetime import UTC, datetime, timedelta

from app.credits.firestore_service import FirestoreEconomicStore


class Snapshot:
    def __init__(self, identifier, data):
        self.id = identifier
        self.reference = identifier
        self._data = data
        self.exists = True

    def to_dict(self):
        return dict(self._data)


class Transaction:
    def __init__(self):
        self.writes = []
        self.created = []

    def _begin(self):
        return None

    def set(self, reference, data):
        self.writes.append((reference, data))

    def create(self, reference, data):
        self.created.append((reference, data))

    def commit(self):
        return None


class Client:
    def __init__(self, snapshots, reservation=None, grant=None):
        self.snapshots = snapshots
        self.reservation = reservation
        self.grant = grant
        self.tx = Transaction()

    def transaction(self):
        return self.tx

    def collection(self, name):
        return Collection(self, name)


class Collection:
    def __init__(self, client, name):
        self.client = client
        self.name = name

    def document(self, identifier):
        return Document(self.client, self.name, identifier)


class Document:
    def __init__(self, client, collection, identifier):
        self.client = client
        self.collection = collection
        self.id = identifier

    def get(self, transaction=None):
        if self.collection == "credit_reservations":
            return self.client.reservation
        return self.client.grant


def test_transactional_reservation_skips_malformed_grant_amounts(monkeypatch):
    malformed = Snapshot(
        "bad",
        {"remaining_amount": 1.5, "reserved_amount": 0},
    )
    valid = Snapshot(
        "good",
        {
            "remaining_amount": 2,
            "reserved_amount": 0,
            "source": "PROMOTIONAL",
            "created_at": datetime.now(UTC),
        },
    )
    client = Client([malformed, valid])
    monkeypatch.setattr(
        "app.credits.firestore_service._where",
        lambda query, field, value: type(
            "Query",
            (),
            {"stream": lambda self, transaction=None: client.snapshots
             if field == "user_id" and value == "u" else []},
        )(),
    )

    result = FirestoreEconomicStore(client).transactional_reservation(
        "u",
        "op-1",
        "idem-1",
        1,
        1,
        "AI_PHOTO_STANDARD",
        datetime.now(UTC) + timedelta(hours=1),
    )

    assert result["allocation"][0]["grant_id"] == "good"
    assert client.tx.writes[0][1]["reserved_amount"] == 1


def test_transactional_transition_rejects_malformed_grant_amounts():
    reservation = Snapshot(
        "reservation-1",
        {
            "user_id": "u",
            "status": "RESERVED",
            "allocation": [{"grant_id": "bad", "amount": 1, "funding_source": "PROMOTIONAL"}],
        },
    )
    grant = Snapshot("bad", {"remaining_amount": "invalid", "reserved_amount": 1})
    store = FirestoreEconomicStore(Client([], reservation=reservation, grant=grant))

    try:
        store.transactional_transition("reservation-1", "u", "consume", "request-1")
    except ValueError as exc:
        assert str(exc) == "LEDGER_INVARIANT_VIOLATION"
    else:
        raise AssertionError("malformed grant must fail closed")


def test_transactional_transition_rejects_negative_grant_amounts():
    reservation = Snapshot(
        "reservation-1",
        {
            "user_id": "u",
            "status": "RESERVED",
            "allocation": [{"grant_id": "bad", "amount": 1, "funding_source": "PROMOTIONAL"}],
        },
    )
    grant = Snapshot("bad", {"remaining_amount": 1, "reserved_amount": -1})
    store = FirestoreEconomicStore(Client([], reservation=reservation, grant=grant))

    try:
        store.transactional_transition("reservation-1", "u", "release", "request-1")
    except ValueError as exc:
        assert str(exc) == "LEDGER_INVARIANT_VIOLATION"
    else:
        raise AssertionError("negative grant amount must fail closed")


def test_transactional_reservation_rejects_malformed_required_amount(monkeypatch):
    store = FirestoreEconomicStore(Client([]))

    for required in (True, 1.5, "1", 0, -1):
        try:
            store.transactional_reservation("u", "op", "idem", required, 1, "AI_PHOTO_STANDARD", None)
        except ValueError as exc:
            assert str(exc) == "FUNDING_REQUIRED"
        else:
            raise AssertionError("malformed required amount must fail closed")


def test_transactional_transition_rejects_balance_underflow():
    reservation = Snapshot(
        "reservation-1",
        {
            "user_id": "u",
            "status": "RESERVED",
            "allocation": [{"grant_id": "grant-1", "amount": 2, "funding_source": "PROMOTIONAL"}],
        },
    )
    grant = Snapshot("grant-1", {"remaining_amount": 1, "reserved_amount": 1})
    store = FirestoreEconomicStore(Client([], reservation=reservation, grant=grant))

    try:
        store.transactional_transition("reservation-1", "u", "consume", "request-1")
    except ValueError as exc:
        assert str(exc) == "LEDGER_INVARIANT_VIOLATION"
    else:
        raise AssertionError("balance underflow must fail closed")


def test_transactional_transition_rejects_unknown_mode():
    store = FirestoreEconomicStore(Client([]))

    try:
        store.transactional_transition("reservation-1", "u", "refund", "request-1")
    except ValueError as exc:
        assert str(exc) == "CREDIT_TRANSITION_INVALID"
    else:
        raise AssertionError("unknown transition mode must fail closed")


def test_transactional_transition_rejects_malformed_allocation_shape():
    reservation = Snapshot(
        "reservation-1",
        {"user_id": "u", "status": "RESERVED", "allocation": [{"grant_id": "grant-1"}]},
    )
    store = FirestoreEconomicStore(Client([], reservation=reservation, grant=None))

    try:
        store.transactional_transition("reservation-1", "u", "release", "request-1")
    except ValueError as exc:
        assert str(exc) == "LEDGER_INVARIANT_VIOLATION"
    else:
        raise AssertionError("malformed allocation shape must fail closed")
