from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepoConfig:
    owner: str
    name: str
    branch: str = "main"


@dataclass(frozen=True)
class RuleCategory:
    name: str
    title: str
    description: str
    source_file: str


@dataclass(frozen=True)
class UpstreamSource:
    name: str
    category: str
    platform: str
    url: str
    enabled: bool = True
    priority: int = 100


@dataclass(frozen=True)
class ProjectConfig:
    repo: RepoConfig
    categories: list[RuleCategory]
    sources: list[UpstreamSource]
