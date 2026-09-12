from __future__ import annotations

import ipaddress
import re

from .rules import COMMENT_PREFIXES, MODIFIER_TOKENS, POLICY_TOKENS, SUPPORTED_RULE_TYPES, strip_inline_comment


DOMAIN_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def _is_comment_or_blank(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith(COMMENT_PREFIXES)


def _validate_domain(target: str) -> str | None:
    if not target or target.startswith(".") or target.endswith(".") or ".." in target:
        return "invalid domain target"

    labels = target.split(".")
    for label in labels:
        if not DOMAIN_LABEL_RE.fullmatch(label):
            return "invalid domain target"
    return None


def _validate_domain_keyword(target: str) -> str | None:
    if not target or any(char.isspace() for char in target):
        return "invalid domain keyword target"
    return None


def _validate_ip_network(rule_type: str, target: str) -> str | None:
    try:
        network = ipaddress.ip_network(target, strict=False)
    except ValueError:
        return f"invalid {rule_type} target"

    if rule_type == "IP-CIDR" and network.version != 4:
        return "IP-CIDR must use an IPv4 network"
    if rule_type == "IP-CIDR6" and network.version != 6:
        return "IP-CIDR6 must use an IPv6 network"
    return None


def _validate_process_name(target: str) -> str | None:
    if not target:
        return "invalid process name target"
    return None


def _validate_user_agent(target: str) -> str | None:
    if not target:
        return "invalid user-agent target"
    return None


def _validate_extra_tokens(rule_type: str, extras: list[str]) -> str | None:
    for token in extras:
        upper = token.upper()
        if upper in POLICY_TOKENS:
            continue
        if upper in MODIFIER_TOKENS and rule_type in {"IP-CIDR", "IP-CIDR6"}:
            continue
        return f"unsupported extra token: {token}"
    return None


def validate_rule_line(raw_line: str) -> str | None:
    if _is_comment_or_blank(raw_line):
        return None

    stripped = strip_inline_comment(raw_line)
    if not stripped:
        return None

    parts = [part.strip() for part in stripped.split(",")]
    if len(parts) < 2:
        return "rule must contain at least rule type and target"
    if any(not part for part in parts[:2]):
        return "rule type and target must not be empty"

    rule_type = parts[0].upper()
    if rule_type not in SUPPORTED_RULE_TYPES:
        return f"unsupported rule type: {parts[0]}"

    target = parts[1]
    extras = [part for part in parts[2:] if part]

    validators = {
        "DOMAIN": _validate_domain,
        "DOMAIN-SUFFIX": _validate_domain,
        "DOMAIN-KEYWORD": _validate_domain_keyword,
        "IP-CIDR": lambda value: _validate_ip_network("IP-CIDR", value),
        "IP-CIDR6": lambda value: _validate_ip_network("IP-CIDR6", value),
        "PROCESS-NAME": _validate_process_name,
        "USER-AGENT": _validate_user_agent,
    }

    target_error = validators[rule_type](target)
    if target_error:
        return target_error

    return _validate_extra_tokens(rule_type, extras)


