from __future__ import annotations

from pathlib import Path


SUPPORTED_RULE_TYPES = (
    "DOMAIN-SUFFIX",
    "DOMAIN",
    "DOMAIN-KEYWORD",
    "IP-CIDR",
    "IP-CIDR6",
    "PROCESS-NAME",
    "USER-AGENT",
)

COMMENT_PREFIXES = ("#", "//", ";")
POLICY_TOKENS = {
    "DIRECT",
    "PROXY",
    "REJECT",
    "REJECT-DROP",
    "REJECT-TINYGIF",
    "REJECT-IMG",
    "REJECT-DICT",
}
MODIFIER_TOKENS = {"NO-RESOLVE"}


def strip_inline_comment(line: str) -> str:
    result = line
    for marker in COMMENT_PREFIXES:
        if marker in result:
            result = result.split(marker, 1)[0]
    return result.strip()


def normalize_rule_line(line: str) -> str | None:
    stripped = strip_inline_comment(line)
    if not stripped:
        return None

    parts = [part.strip() for part in stripped.split(",") if part.strip()]
    if len(parts) < 2:
        return None

    rule_type = parts[0].upper()
    if rule_type not in SUPPORTED_RULE_TYPES:
        return None

    normalized = [rule_type, parts[1]]
    modifiers: list[str] = []
    for token in parts[2:]:
        upper = token.upper()
        if upper in POLICY_TOKENS:
            continue
        if upper in MODIFIER_TOKENS and rule_type in {"IP-CIDR", "IP-CIDR6"}:
            modifiers.append(upper.lower())

    normalized.extend(modifiers)
    return ",".join(normalized)


def read_rule_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    rules: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        normalized = normalize_rule_line(raw_line)
        if normalized:
            rules.append(normalized)
    return rules


def stable_unique(rules: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for rule in rules:
        if rule in seen:
            continue
        seen.add(rule)
        deduped.append(rule)
    return deduped


def write_rule_file(path: Path, rules: list[str], header: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if header:
        lines.extend(header)
    lines.extend(rules)
    text = "\n".join(lines).rstrip()
    path.write_text(text + "\n", encoding="utf-8")
