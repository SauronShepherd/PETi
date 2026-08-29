"""Inventory specialist evaluation manifests without claiming provider execution."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "eval" / "specialists"
OUT = ROOT / "release" / "evaluation"
REQUIRED_SPLITS = {"dev", "held_out", "red_team", "regression"}


def main() -> int:
    capabilities: dict[str, dict] = {}
    errors: list[str] = []
    for capability in sorted(path for path in EVAL.iterdir() if path.is_dir()):
        manifests = {}
        for split in sorted(REQUIRED_SPLITS):
            path = capability / f"{split}.json"
            if not path.exists():
                errors.append(f"missing {path.relative_to(ROOT)}")
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("suite") != capability.name or data.get("split") != split:
                errors.append(f"metadata mismatch {path.relative_to(ROOT)}")
            manifests[split] = {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "schema_version": data.get("schema_version", "UNSPECIFIED"),
            }
        capabilities[capability.name] = {"manifests": manifests, "execution": "PENDING_EXTERNAL_GEMINI"}
    report = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "MANIFESTS_VALID_EXTERNAL_EXECUTION_PENDING" if not errors else "MANIFESTS_INVALID",
        "provider_runs": "NOT_EXECUTED",
        "capabilities": capabilities,
        "errors": errors,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SPECIALIST_EVALUATION_INVENTORY.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for capability in capabilities:
        certificate = OUT / f"{capability.upper()}_RELEASE_CERTIFICATE.md"
        certificate.write_text(
            f"# {capability} release certificate\n\n"
            "## Status\n\n"
            "`PENDING_EXTERNAL_GEMINI`\n\n"
            "The source manifests are present and hashed in `SPECIALIST_EVALUATION_INVENTORY.json`.\n"
            "This certificate is not signed and does not assert provider, device, or production evidence.\n\n"
            "Required before release:\n\n"
            "- executed dev, held-out, red-team, and regression runs;\n"
            "- exact model/config/prompt/schema/guardrail identities;\n"
            "- safety and schema hard-gate metrics;\n"
            "- real DEV vertical slice and physical capture review.\n",
            encoding="utf-8",
        )
    print(json.dumps({"status": report["status"], "capabilities": len(capabilities), "errors": len(errors)}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
