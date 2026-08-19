from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from lib.config import load_project_config


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
README_PATH = ROOT / "README.md"
SECURITY_PATH = ROOT / "SECURITY.md"
MANIFEST_PATH = DIST_DIR / "manifest.json"
UPSTREAM_CONFIG_PATH = ROOT / "sources" / "upstream.yaml"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "update-rules.yml"
PLATFORMS = ("surge", "loon", "clash")
TEXT_SUFFIXES = {
    "",
    ".conf",
    ".gitignore",
    ".json",
    ".list",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_DIR_NAMES = {".git", ".pytest_cache", "__pycache__"}
SENSITIVE_CONTEXT_DIRS = {"sources", "dist"}
BIDI_CONTROL_RE = re.compile(r"[\u202a-\u202e\u2066-\u2069]")
SECRET_QUERY_RE = re.compile(
    r"https?://[^\s\"'<>)]*[?&](?:token|token2|sign|nonce|uuid|password|passwd)=",
    re.IGNORECASE,
)
ASSIGNED_SECRET_RE = re.compile(
    r"\b(?:password|passwd|token|uuid)\s*[:=]\s*(?!YOUR_[A-Z0-9_]+_HERE\b|<[^>]+>|\s*$)\S+",
    re.IGNORECASE,
)
ASSIGNED_SECRET_LINE_RE = re.compile(
    r"^\s*(?:password|passwd|token|uuid)\s*[:=]\s*(?!YOUR_[A-Z0-9_]+_HERE\b|<[^>]+>|\s*$)\S+",
    re.IGNORECASE,
)
SERVER_FIELD_RE = re.compile(
    r"^\s*server\s*:\s*(?!YOUR_PROXY_SERVER_HERE\b|<[^>]+>|\s*$)\S+",
    re.IGNORECASE,
)
SURGE_POLICY_PATH_RE = re.compile(r"\bpolicy-path\s*=\s*https?://", re.IGNORECASE)
MITM_SECRET_RE = re.compile(
    r"\b(?:ca-p12|ca-passphrase)\s*=\s*(?!YOUR_[A-Z0-9_]+_HERE\b|<[^>]+>|\s*$)\S+",
    re.IGNORECASE,
)


class ValidationReport:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def add(self, message: str) -> None:
        self.errors.append(message)

    def fail_for_line(self, path: Path, line_number: int, reason: str) -> None:
        relative = path.relative_to(ROOT)
        self.add(f"{relative}:{line_number}: {reason} (content suppressed)")


def _read_json(path: Path, report: ValidationReport) -> dict[str, Any] | None:
    if not path.exists():
        report.add(f"{path.relative_to(ROOT)}: missing file")
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.add(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return None

    if not isinstance(data, dict):
        report.add(f"{path.relative_to(ROOT)}: root must be a JSON object")
        return None
    return data


def _is_nonempty_text(path: Path) -> bool:
    return path.exists() and bool(path.read_text(encoding="utf-8").strip())


def check_dist_outputs(report: ValidationReport) -> None:
    config = load_project_config(UPSTREAM_CONFIG_PATH)

    for platform in PLATFORMS:
        platform_dir = DIST_DIR / platform
        if not platform_dir.exists():
            report.add(f"dist/{platform}: missing platform output directory")
            continue

        for category in config.categories:
            path = platform_dir / f"{category.name}.list"
            if not path.exists():
                report.add(f"{path.relative_to(ROOT)}: missing rule output")
            elif not _is_nonempty_text(path):
                report.add(f"{path.relative_to(ROOT)}: rule output is empty")

def check_manifest(report: ValidationReport) -> None:
    data = _read_json(MANIFEST_PATH, report)
    if data is None:
        return

    if data.get("project") != "MyShuntRules":
        report.add("dist/manifest.json: `project` must be MyShuntRules")

    repository = data.get("repository")
    if not isinstance(repository, dict):
        report.add("dist/manifest.json: `repository` must be an object")
    else:
        for key in ("owner", "repo", "branch"):
            if not isinstance(repository.get(key), str) or not repository[key].strip():
                report.add(f"dist/manifest.json: missing repository.{key}")

    if "configs" in data:
        report.add("dist/manifest.json: extracted rules repository must not publish client configs")

    items = data.get("rules")
    if not isinstance(items, list) or not items:
        report.add("dist/manifest.json: `rules` must be a non-empty list")
        return

    required_keys = {"name", "category", "platform", "path", "raw_url"}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            report.add(f"dist/manifest.json: rules[{index}] must be an object")
            continue
        for key in sorted(required_keys):
            if not isinstance(item.get(key), str) or not item[key].strip():
                report.add(f"dist/manifest.json: rules[{index}] missing `{key}`")
        relative_path = item.get("path")
        if isinstance(relative_path, str) and not (ROOT / relative_path).exists():
            report.add(f"dist/manifest.json: referenced path does not exist: {relative_path}")


def check_readme_dist_links(report: ValidationReport) -> None:
    if not README_PATH.exists():
        report.add("README.md: missing file")
        return

    text = README_PATH.read_text(encoding="utf-8")
    for relative_path in sorted(set(re.findall(r"dist/[A-Za-z0-9._/\-+]+", text))):
        if not (ROOT / relative_path).exists():
            report.add(f"README.md: referenced dist path does not exist: {relative_path}")


def check_workflow_yaml(report: ValidationReport) -> None:
    if not WORKFLOW_PATH.exists():
        report.add(".github/workflows/update-rules.yml: missing workflow")
        return

    try:
        data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        report.add(f".github/workflows/update-rules.yml: invalid YAML: {exc}")
        return

    if not isinstance(data, dict):
        report.add(".github/workflows/update-rules.yml: root must be a mapping")
        return

    if "on" not in data:
        report.add(".github/workflows/update-rules.yml: missing `on` trigger")
    if data.get("permissions", {}).get("contents") != "write":
        report.add(".github/workflows/update-rules.yml: permissions.contents must be write")

    jobs = data.get("jobs")
    if not isinstance(jobs, dict) or "build" not in jobs:
        report.add(".github/workflows/update-rules.yml: missing build job")


def check_security_document(report: ValidationReport) -> None:
    if not SECURITY_PATH.exists():
        report.add("SECURITY.md: missing security document")
    elif not _is_nonempty_text(SECURITY_PATH):
        report.add("SECURITY.md: file is empty")


def _iter_text_files() -> list[Path]:
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        relative = path.relative_to(ROOT)
        if relative.parts[:2] == ("sources", "cache"):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            paths.append(path)
    return sorted(paths)


def _is_sensitive_context(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return bool(relative.parts and relative.parts[0] in SENSITIVE_CONTEXT_DIRS)


def check_sensitive_patterns(report: ValidationReport) -> None:
    """Scan publishable text files without printing any matched secret-like content."""
    for path in _iter_text_files():
        in_loon_remote_proxy = False
        in_mihomo_proxy_providers = False
        sensitive_context = _is_sensitive_context(path)

        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()

            if BIDI_CONTROL_RE.search(line):
                report.fail_for_line(path, line_number, "hidden bidirectional Unicode control character")

            if SECRET_QUERY_RE.search(line):
                report.fail_for_line(path, line_number, "URL contains credential-like query parameters")

            if (sensitive_context and ASSIGNED_SECRET_RE.search(line)) or ASSIGNED_SECRET_LINE_RE.search(line):
                report.fail_for_line(path, line_number, "credential-like assignment is not a placeholder")

            if SERVER_FIELD_RE.search(line):
                report.fail_for_line(path, line_number, "proxy server field is not a placeholder")

            if MITM_SECRET_RE.search(line):
                report.fail_for_line(path, line_number, "MITM credential field is not empty or placeholder")

            if stripped.startswith("[") and stripped.endswith("]"):
                in_loon_remote_proxy = stripped.lower() == "[remote proxy]"

            if path.suffix.lower() in {".yaml", ".yml"}:
                if re.match(r"^[A-Za-z0-9_-]+:\s*$", line):
                    in_mihomo_proxy_providers = stripped == "proxy-providers:"
                elif stripped in {"proxy-groups:", "rule-providers:", "rules:"}:
                    in_mihomo_proxy_providers = False

            if sensitive_context and in_loon_remote_proxy and "http" in line.lower():
                report.fail_for_line(path, line_number, "remote proxy subscription URL must be a placeholder")

            if sensitive_context and SURGE_POLICY_PATH_RE.search(line):
                report.fail_for_line(path, line_number, "Surge policy-path must be a placeholder")

            if sensitive_context and in_mihomo_proxy_providers and re.search(r"^\s{4}url\s*:\s*https?://", line, re.I):
                report.fail_for_line(path, line_number, "Mihomo proxy-provider URL must be a placeholder")


def main() -> int:
    report = ValidationReport()
    check_dist_outputs(report)
    check_manifest(report)
    check_readme_dist_links(report)
    check_workflow_yaml(report)
    check_security_document(report)
    check_sensitive_patterns(report)

    if report.errors:
        print("Validation failed:")
        for error in report.errors:
            print(f"- {error}")
        return 1

    print("Validation passed: rule outputs, manifest, README links, workflow, and safety patterns checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
