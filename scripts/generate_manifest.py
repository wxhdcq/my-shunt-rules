from __future__ import annotations

import json
from pathlib import Path

from lib.config import load_project_config
from lib.repository import build_raw_url, load_repository_meta


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
CONFIG_PATH = ROOT / "sources" / "upstream.yaml"


def main() -> int:
    project = load_project_config(CONFIG_PATH)
    repository = load_repository_meta()
    category_titles = {category.name: category.title for category in project.categories}

    rules: list[dict[str, str]] = []
    for path in sorted(DIST_DIR.rglob("*.list")):
        relative_path = path.relative_to(ROOT).as_posix()
        rules.append(
            {
                "name": category_titles.get(path.stem, path.stem),
                "category": path.stem,
                "platform": path.parent.name,
                "path": relative_path,
                "raw_url": build_raw_url(relative_path),
            }
        )

    manifest = {
        "project": repository.title,
        "repository": {
            "owner": repository.owner,
            "repo": repository.name,
            "branch": repository.branch,
        },
        "rules": rules,
    }
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated dist/manifest.json with {len(rules)} rule file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
