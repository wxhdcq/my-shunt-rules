from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import yaml


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_CONFIG_PATH = ROOT / "config" / "repository.yaml"


@dataclass(frozen=True)
class RepositoryMeta:
    owner: str
    name: str
    branch: str
    title: str
    description: str


def load_repository_meta() -> RepositoryMeta:
    """Load repository metadata used to build stable raw and import links."""
    with REPOSITORY_CONFIG_PATH.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        raise ValueError(f"Repository config must be a mapping: {REPOSITORY_CONFIG_PATH}")

    owner = str(raw.get("owner", "")).strip()
    name = str(raw.get("name", "")).strip()
    if not owner or not name:
        raise ValueError("Repository config must include `owner` and `name`")

    return RepositoryMeta(
        owner=owner,
        name=name,
        branch=str(raw.get("branch", "main")).strip() or "main",
        title=str(raw.get("title", name)).strip() or name,
        description=str(raw.get("description", "")).strip(),
    )


def build_raw_url(relative_path: str) -> str:
    repository = load_repository_meta()
    return (
        f"https://raw.githubusercontent.com/"
        f"{repository.owner}/{repository.name}/{repository.branch}/{relative_path}"
    )


def build_import_url(platform: str, relative_path: str) -> str:
    raw_url = build_raw_url(relative_path)
    encoded = quote(raw_url, safe="")

    if platform == "loon":
        return f"loon://import?url={encoded}"
    if platform == "surge":
        return f"surge:///install-config?url={encoded}"
    if platform in {"clash", "mihomo"}:
        return f"clash://install-config?url={encoded}"

    raise ValueError(f"Unsupported import platform: {platform}")
