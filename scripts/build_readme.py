from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lib.config import load_project_config
from lib.repository import RepositoryMeta, build_raw_url, load_repository_meta


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
UPSTREAM_CONFIG_PATH = ROOT / "sources" / "upstream.yaml"
README_PATH = ROOT / "README.md"
PLATFORM_ORDER = ("loon", "surge", "clash")


@dataclass(frozen=True)
class DistEntry:
    rule_name: str
    platform: str
    category: str
    relative_path: str
    raw_url: str


def collect_dist_entries() -> list[DistEntry]:
    project = load_project_config(UPSTREAM_CONFIG_PATH)
    category_titles = {category.name: category.title for category in project.categories}
    entries: list[DistEntry] = []

    for path in sorted(DIST_DIR.rglob("*.list")):
        relative_path = path.relative_to(ROOT).as_posix()
        entries.append(
            DistEntry(
                rule_name=category_titles.get(path.stem, path.stem),
                platform=path.parent.name,
                category=path.stem,
                relative_path=relative_path,
                raw_url=build_raw_url(relative_path),
            )
        )

    return sorted(
        entries,
        key=lambda item: (PLATFORM_ORDER.index(item.platform), item.rule_name.lower(), item.relative_path),
    )


def render_readme(repository: RepositoryMeta, entries: list[DistEntry]) -> str:
    lines = [
        f"# {repository.title}",
        "",
        repository.description,
        "",
        "本仓库从 `my-first-repo` 独立拆分，只维护分流规则，不包含代理节点、订阅或完整客户端配置。",
        "",
        "## 支持平台",
        "",
        "- Surge",
        "- Loon",
        "- Clash / Mihomo（classical rule-set）",
        "",
        "## 目录结构",
        "",
        "| 路径 | 说明 |",
        "| --- | --- |",
        "| `sources/upstream.yaml` | 上游规则源、分类和优先级 |",
        "| `sources/custom/` | 自定义补充规则，冲突时优先 |",
        "| `scripts/` | 抓取、清洗、合并、导出和校验脚本 |",
        "| `dist/` | 可直接引用的三端规则产物 |",
        "| `.github/workflows/` | 每日自动更新工作流 |",
        "",
        "## 使用",
        "",
        "```bash",
        "python -m pip install -r requirements.txt",
        "python build.py",
        "python scripts/validate.py",
        "pytest -q",
        "```",
        "",
        "构建过程会抓取已启用的上游规则，标准化并按自定义规则优先级去重，最后更新 `dist/`、发布清单和本 README。",
        "",
        "## 添加分类",
        "",
        "1. 在 `sources/upstream.yaml` 的 `categories` 中新增分类。",
        "2. 创建对应的 `sources/custom/<name>.txt`。",
        "3. 按需在 `sources` 中配置上游地址。",
        "4. 运行完整构建与校验。",
        "",
        "## 发布清单",
        "",
        f"- [manifest.json]({build_raw_url('dist/manifest.json')})",
        "",
        "## 按平台查看",
    ]

    for platform in PLATFORM_ORDER:
        platform_entries = [entry for entry in entries if entry.platform == platform]
        if not platform_entries:
            continue
        lines.extend(
            [
                "",
                f"### {platform}",
                "",
                "| 规则名 | 分类 | 文件路径 | raw 链接 |",
                "| --- | --- | --- | --- |",
            ]
        )
        for entry in platform_entries:
            lines.append(
                f"| {entry.rule_name} | {entry.category} | `{entry.relative_path}` | [raw]({entry.raw_url}) |"
            )

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    entries = collect_dist_entries()
    README_PATH.write_text(render_readme(load_repository_meta(), entries), encoding="utf-8")
    print(f"README.md rebuilt with {len(entries)} dist file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
