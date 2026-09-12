from __future__ import annotations

from pathlib import Path

from lib.rule_validation import validate_rule_line


ROOT = Path(__file__).resolve().parents[1]
CUSTOM_DIR = ROOT / "sources" / "custom"
DIST_DIR = ROOT / "dist"


def _iter_rule_files() -> list[Path]:
    files: list[Path] = []
    files.extend(sorted(CUSTOM_DIR.glob("*.txt")))
    for platform_dir in sorted(DIST_DIR.iterdir()):
        if not platform_dir.is_dir():
            continue
        files.extend(sorted(platform_dir.glob("*.list")))
    return files


def validate_file(path: Path) -> list[tuple[int, str, str]]:
    errors: list[tuple[int, str, str]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        error = validate_rule_line(raw_line)
        if error:
            errors.append((line_number, raw_line, error))
    return errors


def main() -> int:
    files = _iter_rule_files()
    total_files = 0
    total_errors = 0

    for path in files:
        total_files += 1
        errors = validate_file(path)
        if not errors:
            continue

        for line_number, raw_line, error in errors:
            total_errors += 1
            relative_path = path.relative_to(ROOT)
            print(f"ERROR {relative_path}:{line_number}: {error}")
            print(f"  {raw_line}")

    if total_errors:
        print(f"Validation failed: {total_errors} error(s) in {total_files} file(s)")
        return 1

    print(f"Validation passed: {total_files} file(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
