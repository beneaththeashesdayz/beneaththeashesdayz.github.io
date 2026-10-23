from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOGUE = ROOT / "chernarus" / "traders" / "quinn" / "catalogue-data.js"

# Final display-only cleanup for common DayZ/Expansion clothing acronyms and
# compact stems that generic title-casing cannot infer reliably.
ACRONYMS = {
    "bdu": "BDU",
    "cdf": "CDF",
    "usmc": "USMC",
    "ukass": "UK Assault",
    "nbc": "NBC",
    "alice": "ALICE",
    "ttsko": "TTsKO",
    "nvg": "NVG",
    "jpc": "JPC",
    "mmg": "MMG",
    "ucp": "UCP",
    "nwu": "NWU",
    "erdl": "ERDL",
    "gps": "GPS",
}

EXACT_BASES = {
    "bdujacket": "BDU Jacket",
    "bdupants": "BDU Pants",
    "alicebag": "ALICE Backpack",
    "attack2bag": "Attack 2 Backpack",
    "furcourierbag": "Fur Courier Bag",
    "furimprovisedbag": "Fur Improvised Backpack",
    "drysackbag": "Dry Sack Bag",
    "taloonbag": "Taloon Backpack",
    "armypouch": "Army Pouch",
    "ttskojacket": "TTsKO Jacket",
    "ttskopants": "TTsKO Pants",
    "ukassvest": "UK Assault Vest",
    "nbchood": "NBC Hood",
    "nbcjacket": "NBC Jacket",
    "nbcpants": "NBC Pants",
    "nbcboots": "NBC Boots",
    "nbcgloves": "NBC Gloves",
}

COLORS = {
    "black": "Black", "white": "White", "green": "Green", "blue": "Blue",
    "red": "Red", "brown": "Brown", "grey": "Grey", "gray": "Grey",
    "olive": "Olive", "tan": "Tan", "beige": "Beige", "khaki": "Khaki",
    "winter": "Winter", "woodland": "Woodland", "camo": "Camo",
    "lightblue": "Light Blue", "darkblue": "Dark Blue", "skyblue": "Sky Blue",
    "orange": "Orange", "yellow": "Yellow", "violet": "Violet", "pink": "Pink",
    "ttsko": "TTsKO", "medical": "Medical", "yeger": "Yeger",
}


def pretty_suffix(parts: list[str]) -> str:
    out = []
    for p in parts:
        low = p.lower()
        out.append(COLORS.get(low, ACRONYMS.get(low, p.title())))
    return " ".join(out)


def improved_name(class_name: str, current_name: str) -> str:
    low = class_name.lower()
    for prefix in ("loftd_", "mmg_", "fog_", "expansion"):
        if low.startswith(prefix):
            low = low[len(prefix):]
            break

    chunks = [c for c in re.split(r"[_-]+", low) if c]
    if not chunks:
        return current_name

    base = chunks[0]
    if base in EXACT_BASES:
        label = EXACT_BASES[base]
        suffix = pretty_suffix(chunks[1:])
        return f"{label} - {suffix}" if suffix else label

    # Fix standalone acronym words in otherwise-good names produced by the
    # main formatter (e.g. Bdu -> BDU, Cdf -> CDF).
    name = current_name
    for raw, pretty in ACRONYMS.items():
        name = re.sub(rf"\b{re.escape(raw)}\b", pretty, name, flags=re.I)
    return name


def main():
    if not CATALOGUE.exists():
        raise SystemExit(f"Missing {CATALOGUE}")

    text = CATALOGUE.read_text(encoding="utf-8")
    pattern = re.compile(r"name:'((?:\\'|[^'])*)',className:'((?:\\'|[^'])*)'")
    changed = 0

    def repl(match):
        nonlocal changed
        old_name = match.group(1).replace("\\'", "'")
        class_name = match.group(2).replace("\\'", "'")
        new_name = improved_name(class_name, old_name)
        if new_name != old_name:
            changed += 1
        return f"name:'{new_name.replace(chr(39), chr(92)+chr(39))}',className:'{match.group(2)}'"

    CATALOGUE.write_text(pattern.sub(repl, text), encoding="utf-8")
    print(f"Applied {changed} Quinn acronym/compact-name fixes.")


if __name__ == "__main__":
    main()
