from __future__ import annotations

import argparse
from pathlib import Path

from lib.pipeline import load_config, normalize_upstream_sources
from lib.rules import read_rule_file, stable_unique, write_rule_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize rule files.")
    parser.add_argument("input", type=Path, nargs="?", help="Path to the source rule file")
    parser.add_argument("output", type=Path, nargs="?", help="Path to the normalized output file")
    args = parser.parse_args()

    if args.input and args.output:
        rules = stable_unique(read_rule_file(args.input))
        write_rule_file(args.output, rules)
        print(f"Normalized {len(rules)} rule(s) -> {args.output}")
        return 0

    if args.input or args.output:
        parser.error("input and output must be provided together")

    config = load_config()
    results = normalize_upstream_sources(config)
    for source, count in results:
        print(
            f"Normalized {source.name} -> "
            f"category={source.category}, platform={source.platform}, priority={source.priority} "
            f"({count} rules)"
        )
    print(f"Normalized {len(results)} enabled upstream source(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
