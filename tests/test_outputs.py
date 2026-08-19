from __future__ import annotations

import json
from pathlib import Path

from lib.pipeline import DIST_DIR, export_platform, load_config, merge_group_rules


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("surge", "loon", "clash")


def test_exports_can_be_regenerated_from_local_sources() -> None:
    config = load_config()
    merge_group_rules(config)

    for platform in PLATFORMS:
        counts = export_platform(config, platform)
        assert set(counts) == {category.name for category in config.categories}
        assert all((DIST_DIR / platform / f"{category.name}.list").exists() for category in config.categories)


def test_manifest_contains_required_fields() -> None:
    manifest_path = ROOT / "dist" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["project"] == "MyShuntRules"
    assert {"owner", "repo", "branch"}.issubset(manifest["repository"])
    assert manifest["repository"]["repo"] == "my-shunt-rules"
    assert manifest["rules"]
    assert "configs" not in manifest

    for item in manifest["rules"]:
        assert {"name", "category", "platform", "path", "raw_url"}.issubset(item)


def test_bank_rule_sources_have_expected_official_coverage() -> None:
    hk_rules = (ROOT / "sources" / "custom" / "hong-kong-banks.txt").read_text(encoding="utf-8")
    us_rules = (ROOT / "sources" / "custom" / "us-banks.txt").read_text(encoding="utf-8")
    finance_rules = (ROOT / "sources" / "custom" / "us-financial-services.txt").read_text(encoding="utf-8")

    assert hk_rules.count("DOMAIN-SUFFIX,") >= 35
    assert us_rules.count("DOMAIN-SUFFIX,") >= 3_500
    assert "DOMAIN-SUFFIX,hsbc.com.hk" in hk_rules
    assert "DOMAIN-SUFFIX,mox.com" in hk_rules
    assert "DOMAIN-SUFFIX,bankofamerica.com" in us_rules
    assert finance_rules.count("DOMAIN-SUFFIX,") >= 50
    assert "DOMAIN-SUFFIX,schwab.com" in finance_rules
    assert "DOMAIN-SUFFIX,fidelity.com" in finance_rules
    assert "DOMAIN-SUFFIX,revolut.com" in finance_rules
    assert "DOMAIN-SUFFIX,interactivebrokers.com" in finance_rules

    exported_finance_rules = (ROOT / "dist" / "surge" / "us-financial-services.list").read_text(
        encoding="utf-8"
    )
    assert "DOMAIN-SUFFIX,schwab.com" in exported_finance_rules
    assert "DOMAIN-SUFFIX,fidelity.com" in exported_finance_rules
    assert "DOMAIN-SUFFIX,revolut.com" in exported_finance_rules
