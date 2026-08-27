from app.advertising.fake_verifier import FakeRewardVerifier


def test_fake_reward_verifier_accepts_only_issued_tokens():
    verifier = FakeRewardVerifier()
    assert not verifier.verify("client-forged")
    assert verifier.issue("fixture-token") == "fixture-token"
    assert verifier.verify("fixture-token")
    assert not verifier.verify("fixture-token-other")
