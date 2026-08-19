from __future__ import annotations

from pathlib import Path

from lib.config import load_project_config
from lib.repository import load_repository_meta


ROOT = Path(__file__).resolve().parents[1]


def test_upstream_config_reads_categories_and_sources() -> None:
    config = load_project_config(ROOT / "sources" / "upstream.yaml")
    category_names = {category.name for category in config.categories}

    assert {
        "ai",
        "apple-cn",
        "global",
        "direct",
        "reject",
        "hong-kong-banks",
        "us-banks",
        "us-financial-services",
    }.issubset(category_names)
    assert config.sources
    assert {source.category for source in config.sources}.issubset(category_names)


def test_repository_meta_uses_project_title() -> None:
    repository = load_repository_meta()

    assert repository.title == "MyShuntRules"
    assert repository.owner
    assert repository.name
    assert repository.branch
