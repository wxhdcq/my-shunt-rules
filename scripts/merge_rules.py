from __future__ import annotations

from lib.pipeline import CUSTOM_RULE_PRIORITY, _merge_candidates_for_category, load_config, merge_group_rules


def main() -> int:
    config = load_config()
    merged = merge_group_rules(config)
    for category in config.categories:
        print(f"[{category.name}] merge order:")
        for priority, label, rules in _merge_candidates_for_category(config, category):
            priority_label = "custom" if priority == CUSTOM_RULE_PRIORITY else str(priority)
            print(f"  - priority={priority_label:<6} source={label:<32} rules={len(rules)}")
        print(f"Merged {category.name}: {len(merged[category.name])} final rule(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
