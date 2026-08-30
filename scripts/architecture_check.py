"""Static architecture checks for the web and cloud-only release."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
assert (ROOT / "web").is_dir()
assert (ROOT / "backend").is_dir()
assert (ROOT / "infra" / "terraform").is_dir()
print("ARCHITECTURE_CHECK=PASS web_backend_cloud")
