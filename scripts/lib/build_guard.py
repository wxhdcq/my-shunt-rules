"""Build and test in isolation; only publish a complete, reviewed-size result."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .rules import normalize_rule_line


INPUT_PATHS = (
    "scripts", "sources", "config", "examples", "tests", "agents", ".github",
    "dist", "README.md", "SECURITY.md", "LICENSE", "requirements.txt", "build.py",
)
MAX_REMOVAL_FRACTION = 0.20


def published_snapshot(root: Path, source_paths: tuple[str, ...] = ()) -> dict[str, bytes]:
    paths = list((root / "dist").rglob("*"))
    paths += [root / "README.md", *(root / path for path in source_paths)]
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in paths if path.is_file()}


def _rule_count(data: bytes) -> int:
    return len({rule for line in data.decode("utf-8-sig").splitlines()
                if (rule := normalize_rule_line(line)) is not None})


def check_rule_changes(before: dict[str, bytes], after: dict[str, bytes], *,
                       allow_large_drop: bool = False) -> None:
    """The baseline is captured before fetching, never after overwriting dist."""
    for path, content in sorted(after.items()):
        if not path.endswith(".list"):
            continue
        count = _rule_count(content)
        if count == 0:
            raise RuntimeError(f"{path}: no effective rules; refusing publication")
        previous = _rule_count(before[path]) if path in before else 0
        removed = previous - count
        if previous and removed > previous * MAX_REMOVAL_FRACTION:
            message = f"{path}: {previous} -> {count} rules ({removed / previous:.1%} removed)"
            if not allow_large_drop:
                raise RuntimeError(message + "; inspect the change before using --allow-large-drop")
            print("[build] explicitly allowed large change: " + message)


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".publish-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def publish_snapshot(root: Path, before: dict[str, bytes], after: dict[str, bytes]) -> None:
    changed = [path for path in sorted(before.keys() | after.keys())
               if before.get(path) != after.get(path)]
    touched: list[str] = []
    try:
        for relative in changed:
            target = root / relative
            if relative in after:
                _write_atomic(target, after[relative])
            else:
                target.unlink(missing_ok=True)
            touched.append(relative)
    except BaseException as publication_error:
        rollback_errors = []
        for relative in reversed(touched):
            try:
                if relative in before:
                    _write_atomic(root / relative, before[relative])
                else:
                    (root / relative).unlink(missing_ok=True)
            except OSError:
                # Try all remaining paths even when one disk/path stays unwritable.
                rollback_errors.append(relative)
        if rollback_errors:
            raise RuntimeError("publication failed; rollback incomplete for: " +
                               ", ".join(rollback_errors)) from publication_error
        raise


def run_guarded_build(root: Path, steps: list[tuple[str, list[str]]], *,
                      source_paths: tuple[str, ...] = (), allow_large_drop: bool = False) -> int:
    before = published_snapshot(root, source_paths)
    environment = dict(os.environ, MYSHUNTRULES_STRICT_FETCH="1")
    try:
        with tempfile.TemporaryDirectory(prefix="myshuntrules-build-") as directory:
            stage = Path(directory)
            for relative in INPUT_PATHS:
                source = root / relative
                if source.is_dir():
                    shutil.copytree(source, stage / relative, ignore=shutil.ignore_patterns(
                        ".git", "__pycache__", ".pytest_cache", "cache", "private", ".venv"))
                elif source.is_file():
                    shutil.copy2(source, stage / relative)

            for name, command in steps:
                print(f"[build] start {name}", flush=True)
                result = subprocess.run(command, cwd=stage, env=environment)
                if result.returncode:
                    print(f"[build] failed {name}; published files are unchanged", flush=True)
                    return result.returncode

            # These inspect the NEW exports, rather than yesterday's files.
            checks = ["scripts/validate_rules.py", "scripts/validate.py"]
            if (stage / "scripts/validate_configs.py").exists():
                checks.append("scripts/validate_configs.py")
            for script in checks:
                subprocess.run([sys.executable, script], cwd=stage, env=environment, check=True)
            candidate = published_snapshot(stage, source_paths)
            check_rule_changes(before, candidate, allow_large_drop=allow_large_drop)
            subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=stage,
                           env=environment, check=True)
            if published_snapshot(stage, source_paths) != candidate:
                raise RuntimeError("tests changed publishable files; refusing publication")
            if published_snapshot(root, source_paths) != before:
                raise RuntimeError("published files changed during build; retry from the new baseline")
            publish_snapshot(root, before, candidate)
        print("[build] validated outputs published successfully")
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"[build] failed: {exc}")
        return 1
