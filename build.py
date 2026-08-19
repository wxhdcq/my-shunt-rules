from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable
# Keep the build order explicit here so local runs and GitHub Actions stay identical.
STEPS = [
    ("fetch_upstream", [PYTHON, "scripts/fetch_upstream.py"]),
    ("normalize_rules", [PYTHON, "scripts/normalize_rules.py"]),
    ("validate_rules", [PYTHON, "scripts/validate_rules.py"]),
    ("merge_rules", [PYTHON, "scripts/merge_rules.py"]),
    ("export_clash", [PYTHON, "scripts/export_clash.py"]),
    ("export_loon", [PYTHON, "scripts/export_loon.py"]),
    ("export_surge", [PYTHON, "scripts/export_surge.py"]),
    ("generate_manifest", [PYTHON, "scripts/generate_manifest.py"]),
    ("build_readme", [PYTHON, "scripts/build_readme.py"]),
]


def main() -> int:
    print(f"[build] root={ROOT}")
    print(f"[build] python={PYTHON}")

    for step_name, command in STEPS:
        # Run each step as an isolated process so a failure returns a clear non-zero exit code.
        print(f"[build] start {step_name}")
        completed = subprocess.run(command, cwd=ROOT)
        if completed.returncode != 0:
            print(f"[build] failed {step_name} (exit={completed.returncode})")
            return completed.returncode
        print(f"[build] done {step_name}")

    print("[build] completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
