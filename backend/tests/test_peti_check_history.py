from datetime import UTC, datetime, timedelta

from app.analysis.domain import AnalysisJob


def test_history_is_pet_scoped_and_newest_first():
    jobs = [
        AnalysisJob(
            "old",
            "u",
            "pet",
            "DOG",
            "PETI_CHECK",
            ["m"],
            "k1",
            "r1",
            "f1",
            created_at=datetime.now(UTC) - timedelta(days=1),
        ),
        AnalysisJob("new", "u", "pet", "DOG", "PETI_CHECK", ["m"], "k2", "r2", "f2"),
        AnalysisJob("other", "u", "other-pet", "DOG", "PETI_CHECK", ["m"], "k3", "r3", "f3"),
    ]
    visible = sorted(
        [x for x in jobs if x.owner_user_id == "u" and x.animal_id == "pet"],
        key=lambda x: x.created_at,
        reverse=True,
    )
    assert [x.id for x in visible] == ["new", "old"]
