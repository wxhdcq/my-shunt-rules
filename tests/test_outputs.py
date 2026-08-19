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
