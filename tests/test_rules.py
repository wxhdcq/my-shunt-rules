from __future__ import annotations

from lib.pipeline import _rule_conflict_key, _rule_sort_key
from lib.rules import normalize_rule_line, stable_unique


def test_stable_unique_preserves_first_seen_order() -> None:
    rules = [
        "DOMAIN,example.com",
        "DOMAIN-SUFFIX,example.org",
        "DOMAIN,example.com",
        "DOMAIN-KEYWORD,example",
    ]

    assert stable_unique(rules) == [
        "DOMAIN,example.com",
        "DOMAIN-SUFFIX,example.org",
        "DOMAIN-KEYWORD,example",
    ]


def test_rule_sort_key_keeps_deterministic_type_order() -> None:
    rules = [
        "IP-CIDR,1.1.1.0/24,no-resolve",
        "DOMAIN-KEYWORD,google",
        "DOMAIN,chat.openai.com",
        "DOMAIN-SUFFIX,youtube.com",
    ]

    assert sorted(rules, key=_rule_sort_key) == [
        "DOMAIN,chat.openai.com",
        "DOMAIN-SUFFIX,youtube.com",
        "DOMAIN-KEYWORD,google",
        "IP-CIDR,1.1.1.0/24,no-resolve",
    ]


def test_conflict_key_is_case_insensitive() -> None:
    assert _rule_conflict_key("DOMAIN,Example.COM") == _rule_conflict_key("domain,example.com")


def test_normalize_rule_line_removes_policy_tokens() -> None:
    assert normalize_rule_line("IP-CIDR,8.8.8.8/32,PROXY,no-resolve") == "IP-CIDR,8.8.8.8/32,no-resolve"
