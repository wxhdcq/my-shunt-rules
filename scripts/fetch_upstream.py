from __future__ import annotations

import os
import sys

from lib.pipeline import fetch_upstream_sources, load_config


def main() -> int:
    config = load_config()
    # Publishing requires every enabled source to download and validate successfully.
    strict = "--strict" in sys.argv or os.environ.get("MYSHUNTRULES_STRICT_FETCH") == "1"

    try:
        results = fetch_upstream_sources(config, strict=strict)
    except RuntimeError as exc:
        print(f"Fetch failed: {exc}")
        return 1

    for source, count in results:
        print(
            f"Fetched {source.name} -> "
            f"category={source.category}, platform={source.platform}, priority={source.priority} "
            f"({count} raw rules)"
        )
    strict_label = " (strict mode)" if strict else ""
    print(f"Fetched {len(results)} enabled upstream source(s){strict_label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
