from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_public_experience.py"

print()
print("Phase 9B Artemis II Public Web Validation")
print("=" * 72)
print("Delegating to the final public-experience validator.")
print()

result = subprocess.run(
    [sys.executable, str(VALIDATOR)],
    cwd=ROOT,
    check=False,
)

if result.returncode != 0:
    raise SystemExit("PHASE 9B VALIDATION FAILED")

print()
print("PHASE 9B VALIDATION PASSED")
