#!/usr/bin/env python3
"""Build a compact browser-side index of Expansion Market variant families."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MARKET_DIR = ROOT / "data" / "live-market" / "market"
OUTPUT = ROOT / "data" / "live-market" / "variant-groups.js"


def read_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def main() -> None:
    families: dict[str, dict[str, str]] = {}
    items: dict[str, str] = {}
    conflicts = 0

    for path in sorted(MARKET_DIR.glob("*.json"), key=lambda value: value.name.casefold()):
        payload = read_json(path)
        rows = payload if isinstance(payload, list) else payload.get("Items", [])
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            parent = str(row.get("ClassName") or row.get("className") or "").strip()
            variants = row.get("Variants") or row.get("variants") or []
            classes = [parent] + [str(value).strip() for value in variants if str(value).strip()]
            classes = list(dict.fromkeys(value for value in classes if value))
            if len(classes) < 2:
                continue

            family_key = f"{path.stem.casefold()}:{parent.casefold()}:{row_index}"
            families[family_key] = {"parent": parent.casefold()}
            for class_name in classes:
                item_key = class_name.casefold()
                existing = items.get(item_key)
                if existing and existing != family_key:
                    conflicts += 1
                    continue
                items[item_key] = family_key

    payload = {"families": families, "items": items}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "window.marketVariantGroups=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(f"Built {len(families):,} market families covering {len(items):,} item classes ({conflicts} conflicts kept first).")


if __name__ == "__main__":
    main()

