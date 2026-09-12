from __future__ import annotations

import json
from pathlib import Path

from lib import pipeline
from lib.models import ProjectConfig, RepoConfig, RuleCategory, UpstreamSource
from lib.pipeline import export_platform, merge_group_rules
from lib.rules import read_rule_file


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("surge", "loon", "clash")


def test_exports_can_be_regenerated_from_local_sources(tmp_path, monkeypatch) -> None:
    # A complete fixture exercises merging without touching checked-in releases.
    for name, folder in (("DIST_DIR", "dist"), ("NORMALIZED_CACHE_DIR", "normalized"),
                         ("MERGED_CACHE_DIR", "merged"), ("CUSTOM_DIR", "custom")):
        (tmp_path / folder).mkdir()
        monkeypatch.setattr(pipeline, name, tmp_path / folder)
    (tmp_path / "custom/direct.txt").write_text("DOMAIN,shared.test\n")
    (tmp_path / "custom/proxy.txt").write_text("DOMAIN,proxy.test\n")
    (tmp_path / "normalized/direct__0010__surge__fixture_a.txt").write_text(
        "DOMAIN,upstream.test\nUSER-AGENT,Fixture*\n")
    (tmp_path / "normalized/proxy__0010__surge__fixture_b.txt").write_text(
        "DOMAIN,shared.test\nDOMAIN,other.test\n")
    config = ProjectConfig(RepoConfig("fixture", "fixture"),
        [RuleCategory(name, name, name, name + ".txt") for name in ("direct", "proxy")],
        [UpstreamSource("fixture_a", "direct", "surge", "https://example.test/a", priority=10),
         UpstreamSource("fixture_b", "proxy", "surge", "https://example.test/b", priority=10)])
    merged = merge_group_rules(config)
    assert "DOMAIN,shared.test" in merged["direct"]
    assert "DOMAIN,shared.test" not in merged["proxy"]

    for platform in PLATFORMS:
        counts = export_platform(config, platform)
        assert counts == {"direct": 2 if platform == "clash" else 3, "proxy": 2}
        exported = read_rule_file(pipeline.DIST_DIR / platform / "direct.list")
        assert ("USER-AGENT,Fixture*" in exported) == (platform != "clash")


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
