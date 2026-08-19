from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import ProjectConfig, RepoConfig, RuleCategory, UpstreamSource


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file does not exist: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {path}")
    return data


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Config section `{key}` must be a mapping")
    return value


def _require_list(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Config section `{key}` must be a list")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError(f"Every item in `{key}` must be a mapping")
    return value


def _require_text(item: dict[str, Any], key: str, section: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"`{section}` item is missing text field `{key}`")
    return value.strip()


def _require_int(item: dict[str, Any], key: str, section: str, default: int) -> int:
    value = item.get(key, default)
    if not isinstance(value, int):
        raise ValueError(f"`{section}` field `{key}` must be an integer")
    return value


def load_project_config(config_path: Path) -> ProjectConfig:
    """Load and validate the rule source configuration before any build step runs."""
    raw = _load_yaml(config_path)
    repo_map = _require_mapping(raw, "repo")
    category_maps = _require_list(raw, "categories")
    source_maps = _require_list(raw, "sources")

    repo = RepoConfig(
        owner=_require_text(repo_map, "owner", "repo"),
        name=_require_text(repo_map, "name", "repo"),
        branch=str(repo_map.get("branch", "main")).strip() or "main",
    )

    categories = [
        RuleCategory(
            name=_require_text(item, "name", "categories"),
            title=_require_text(item, "title", "categories"),
            description=_require_text(item, "description", "categories"),
            source_file=_require_text(item, "source_file", "categories"),
        )
        for item in category_maps
    ]

    sources = [
        UpstreamSource(
            name=_require_text(item, "name", "sources"),
            category=_require_text(item, "category", "sources"),
            platform=_require_text(item, "platform", "sources"),
            url=_require_text(item, "url", "sources"),
            enabled=bool(item.get("enabled", True)),
            priority=_require_int(item, "priority", "sources", 100),
        )
        for item in source_maps
    ]

    category_names = {category.name for category in categories}
    unknown_categories = sorted({source.category for source in sources} - category_names)
    if unknown_categories:
        raise ValueError(f"Sources reference unknown categories: {', '.join(unknown_categories)}")

    return ProjectConfig(repo=repo, categories=categories, sources=sources)
