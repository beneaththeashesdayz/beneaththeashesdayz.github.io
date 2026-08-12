from __future__ import annotations

import json
from pathlib import Path

PATH = Path("data/live-market/traders/Clothing.json")


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    categories = data.get("Categories", [])
    changed = []
    updated = []

    for entry in categories:
        # Expansion trader mode defaults to 0 when no suffix is present.
        # For Quinn, all ordinary/vanilla category entries should be mode 1
        # (trader sells to players AND buys from players). Explicit modes such
        # as FOG/MMG :2 remain untouched.
        if isinstance(entry, str) and ":" not in entry:
            new_entry = entry + ":1"
            updated.append(new_entry)
            changed.append((entry, new_entry))
        else:
            updated.append(entry)

    data["Categories"] = updated
    PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Updated {len(changed)} clothing categories to mode :1")
    for old, new in changed:
        print(f"  {old} -> {new}")


if __name__ == "__main__":
    main()
