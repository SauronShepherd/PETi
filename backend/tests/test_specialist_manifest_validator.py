from scripts.validate_specialist_manifests import main


def test_specialist_manifest_validator_passes_checked_in_matrix():
    assert main() == 0
