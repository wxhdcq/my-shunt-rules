from __future__ import annotations

from lib.pipeline import export_platform, load_config


PLATFORM = "clash"
PLATFORM_LABEL = "Clash/Mihomo"


def main() -> int:
    counts = export_platform(load_config(), PLATFORM)
    for group_name, count in counts.items():
        print(f"Exported {PLATFORM_LABEL} {group_name}: {count} rule(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
