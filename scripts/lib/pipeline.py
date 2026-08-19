from __future__ import annotations

from collections import Counter
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from .config import load_project_config
from .models import ProjectConfig, RuleCategory, UpstreamSource
from .rules import read_rule_file, stable_unique, write_rule_file


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "sources" / "upstream.yaml"
CUSTOM_DIR = ROOT / "sources" / "custom"
CACHE_ROOT = ROOT / "sources" / "cache"
RAW_CACHE_DIR = CACHE_ROOT / "raw"
NORMALIZED_CACHE_DIR = CACHE_ROOT / "normalized"
MERGED_CACHE_DIR = CACHE_ROOT / "merged"
DIST_DIR = ROOT / "dist"
CUSTOM_RULE_PRIORITY = -1
DEFAULT_HTTP_HEADERS = {
    "User-Agent": "MyShuntRules/1.0",
    "Accept": "text/plain,text/*;q=0.9,*/*;q=0.8",
}
RULE_TYPE_ORDER = {
    "DOMAIN": 10,
    "DOMAIN-SUFFIX": 20,
    "DOMAIN-KEYWORD": 30,
    "PROCESS-NAME": 40,
    "USER-AGENT": 50,
    "IP-CIDR": 60,
    "IP-CIDR6": 70,
}
PLATFORM_LABELS = {
    "clash": "Clash/Mihomo",
    "loon": "Loon",
    "surge": "Surge",
}
PLATFORM_UNSUPPORTED_RULE_TYPES = {
    "clash": {"USER-AGENT"},
    "loon": set(),
    "surge": set(),
}
PLATFORM_NOTES = {
    "clash": [
        "# Format: classical rule-set for Mihomo/Clash.Meta compatible clients",
        "# Note: PROCESS-NAME rules require Mihomo/Clash.Meta support",
    ],
    "loon": ["# Format: Loon rule list"],
    "surge": ["# Format: Surge rule list"],
}


def load_config() -> ProjectConfig:
    return load_project_config(CONFIG_PATH)


def _remove_stale_files(directory: Path, expected_names: set[str]) -> None:
    if not directory.exists():
        return

    for pattern in ("*.list", "*.txt"):
        for path in directory.glob(pattern):
            if path.name not in expected_names:
                path.unlink()


def fetch_upstream_sources(
    config: ProjectConfig,
    *,
    strict: bool = False,
) -> list[tuple[UpstreamSource, int]]:
    RAW_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    results: list[tuple[UpstreamSource, int]] = []
    enabled_sources = [source for source in config.sources if source.enabled]

    for source in enabled_sources:
        try:
            request = Request(source.url, headers=DEFAULT_HTTP_HEADERS)
            with urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8", errors="ignore")
        except URLError as exc:
            print(f"Warning: failed to fetch {source.name}: {exc}")
            continue

        raw_path = RAW_CACHE_DIR / f"{source.name}.txt"
        raw_path.write_text(body, encoding="utf-8")
        results.append((source, len(stable_unique(read_rule_file(raw_path)))))

    # CI uses strict mode so a completely failed refresh cannot silently fall back to old cache.
    if strict and enabled_sources and not results:
        raise RuntimeError("strict fetch mode: all enabled upstream sources failed to fetch")

    return results


def normalize_upstream_sources(config: ProjectConfig) -> list[tuple[UpstreamSource, int]]:
    NORMALIZED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    expected_names = {
        f"{source.category}__{source.priority:04d}__{source.platform}__{source.name}.txt"
        for source in config.sources
        if source.enabled
    }
    _remove_stale_files(NORMALIZED_CACHE_DIR, expected_names)

    results: list[tuple[UpstreamSource, int]] = []
    for source in sorted(config.sources, key=lambda item: (item.category, item.priority, item.name)):
        if not source.enabled:
            continue

        raw_path = RAW_CACHE_DIR / f"{source.name}.txt"
        normalized_path = NORMALIZED_CACHE_DIR / (
            f"{source.category}__{source.priority:04d}__{source.platform}__{source.name}.txt"
        )

        if not raw_path.exists():
            if normalized_path.exists():
                normalized_path.unlink()
            print(f"Warning: skip normalize for {source.name} because raw cache is missing")
            continue

        rules = stable_unique(read_rule_file(raw_path))
        write_rule_file(normalized_path, rules)
        results.append((source, len(rules)))

    return results


def _merge_candidates_for_category(config: ProjectConfig, category: RuleCategory) -> list[tuple[int, str, list[str]]]:
    candidates: list[tuple[int, str, list[str]]] = []

    custom_path = CUSTOM_DIR / category.source_file
    if not custom_path.exists():
        raise FileNotFoundError(f"Missing custom rule source for `{category.name}`: {custom_path}")

    custom_rules = read_rule_file(custom_path)
    if custom_rules:
        candidates.append((CUSTOM_RULE_PRIORITY, f"custom:{category.source_file}", custom_rules))

    for source in sorted(config.sources, key=lambda item: (item.priority, item.name)):
        if not source.enabled or source.category != category.name:
            continue
        normalized_path = NORMALIZED_CACHE_DIR / (
            f"{source.category}__{source.priority:04d}__{source.platform}__{source.name}.txt"
        )
        if not normalized_path.exists():
            print(f"Warning: skip merge for {source.name} because normalized cache is missing")
            continue
        candidates.append((source.priority, f"{source.platform}:{source.name}", read_rule_file(normalized_path)))

    return candidates


def _rule_conflict_key(rule: str) -> str:
    parts = [part.strip() for part in rule.split(",") if part.strip()]
    if len(parts) < 2:
        return rule.strip().lower()

    rule_type = parts[0].upper()
    target = parts[1].lower()
    modifiers = [part.lower() for part in parts[2:]]
    return ",".join([rule_type, target, *modifiers])


def merge_group_rules(config: ProjectConfig) -> dict[str, list[str]]:
    """Merge custom and upstream rules while keeping custom decisions authoritative."""
    MERGED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _remove_stale_files(MERGED_CACHE_DIR, {f"{category.name}.txt" for category in config.categories})

    merged: dict[str, list[str]] = {category.name: [] for category in config.categories}
    ownership: dict[str, tuple[str, str]] = {}

    # Phase 1: custom rules claim ownership first.
    for category in config.categories:
        custom_path = CUSTOM_DIR / category.source_file
        if not custom_path.exists():
            raise FileNotFoundError(f"Missing custom rule source for `{category.name}`: {custom_path}")

        for rule in read_rule_file(custom_path):
            key = _rule_conflict_key(rule)
            if key not in ownership:
                ownership[key] = (category.name, "custom")
                merged[category.name].append(rule)

    # Phase 2: upstream sources can only fill gaps that custom rules did not already decide.
    for category in config.categories:
        for priority, label, rules in _merge_candidates_for_category(config, category):
            if priority == CUSTOM_RULE_PRIORITY:
                continue
            for rule in rules:
                key = _rule_conflict_key(rule)
                if key in ownership:
                    continue
                ownership[key] = (category.name, label)
                merged[category.name].append(rule)

    for category in config.categories:
        merged_rules = stable_unique(merged[category.name])
        write_rule_file(MERGED_CACHE_DIR / f"{category.name}.txt", merged_rules)
        merged[category.name] = merged_rules

    return merged


def load_merged_rules(config: ProjectConfig) -> dict[str, list[str]]:
    return {
        category.name: read_rule_file(MERGED_CACHE_DIR / f"{category.name}.txt")
        for category in config.categories
    }


def _split_rule(rule: str) -> list[str]:
    return [part.strip() for part in rule.split(",") if part.strip()]


def _rule_sort_key(rule: str) -> tuple[object, ...]:
    parts = _split_rule(rule)
    if len(parts) < 2:
        return (999, rule.lower(), "", rule)

    rule_type = parts[0].upper()
    target = parts[1].lower()
    extras = tuple(part.lower() for part in parts[2:])
    return (RULE_TYPE_ORDER.get(rule_type, 999), target, extras, rule.lower())


def _format_rule_for_platform(platform: str, rule: str) -> tuple[str | None, str | None]:
    parts = _split_rule(rule)
    if len(parts) < 2:
        return None, "MALFORMED"

    rule_type = parts[0].upper()
    if rule_type in PLATFORM_UNSUPPORTED_RULE_TYPES.get(platform, set()):
        return None, rule_type

    target = parts[1]
    extras = [part.lower() for part in parts[2:]]
    return ",".join([rule_type, target, *extras]), None


def export_platform(config: ProjectConfig, platform: str) -> dict[str, int]:
    """Write sorted platform-specific rule lists from the merged cache."""
    merged = load_merged_rules(config)
    output_dir = DIST_DIR / platform
    output_dir.mkdir(parents=True, exist_ok=True)
    _remove_stale_files(output_dir, {f"{category.name}.list" for category in config.categories})
    counts: dict[str, int] = {}

    for category in config.categories:
        exported_rules: list[str] = []
        skipped = Counter()

        for rule in sorted(merged.get(category.name, []), key=_rule_sort_key):
            formatted_rule, skipped_type = _format_rule_for_platform(platform, rule)
            if formatted_rule is None:
                skipped[skipped_type or "UNKNOWN"] += 1
                continue
            exported_rules.append(formatted_rule)

        header = [
            f"# {category.title}",
            f"# {category.description}",
            f"# Generated for {PLATFORM_LABELS.get(platform, platform)} from MyShuntRules",
            *PLATFORM_NOTES.get(platform, []),
        ]
        for rule_type, skipped_count in sorted(skipped.items()):
            header.append(f"# Skipped unsupported {rule_type}: {skipped_count}")
        header.append("")

        write_rule_file(output_dir / f"{category.name}.list", exported_rules, header=header)
        counts[category.name] = len(exported_rules)

    return counts
