from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOGUE = ROOT / "chernarus" / "traders" / "quinn" / "catalogue-data.js"

# Exact vanilla/commonly-seen compact class stems. These are intentionally
# display-only; className remains untouched for search/debugging.
EXACT = {
    "ghilliebushrag": "Ghillie Bushrag",
    "ghilliehood": "Ghillie Hood",
    "ghilliesuit": "Ghillie Suit",
    "ghillietop": "Ghillie Top",
    "platecarriervest": "Plate Carrier Vest",
    "highcapacityvest": "High Capacity Vest",
    "pressvest": "Press Vest",
    "smershvest": "Smersh Vest",
    "chestholster": "Chest Holster",
    "weaponholster": "Weapon Holster",
    "ballistichelmet": "Ballistic Helmet",
    "tacticalhelmet": "Tactical Helmet",
    "assaulthelmet": "Assault Helmet",
    "motohelmet": "Motorcycle Helmet",
    "firefightershelmet": "Firefighter Helmet",
    "constructionhelmet": "Construction Helmet",
    "greathelm": "Great Helm",
    "norsehelm": "Norse Helm",
    "booniehat": "Boonie Hat",
    "buckethat": "Bucket Hat",
    "cowboyhat": "Cowboy Hat",
    "flatcap": "Flat Cap",
    "beaniehat": "Beanie",
    "militaryberet": "Military Beret",
    "balaclavamask": "Balaclava Mask",
    "balaclava3holes": "3-Hole Balaclava",
    "bandanamask": "Bandana Mask",
    "gasmask": "Gas Mask",
    "designerglasses": "Designer Glasses",
    "sportglasses": "Sport Glasses",
    "tacticalgoggles": "Tactical Goggles",
    "aviatorglasses": "Aviator Glasses",
    "assaultbackpack": "Assault Backpack",
    "courierbag": "Courier Bag",
    "slingbag": "Sling Bag",
    "drybag": "Dry Bag",
    "leathersack": "Leather Sack",
    "mountainbag": "Mountain Backpack",
    "huntingbag": "Hunting Backpack",
    "schoolroomslingbag": "School Sling Bag",
    "combatboots": "Combat Boots",
    "hikingboots": "Hiking Boots",
    "workingboots": "Work Boots",
    "joggingshoes": "Jogging Shoes",
    "leathershoes": "Leather Shoes",
    "dressshoes": "Dress Shoes",
    "sneakers": "Sneakers",
    "wellies": "Wellies",
    "tracksuitpants": "Tracksuit Pants",
    "jumpsuitpants": "Jumpsuit Pants",
    "cargopants": "Cargo Pants",
    "canvaspants": "Canvas Pants",
    "hunterpants": "Hunter Pants",
    "slackspants": "Slacks",
    "jeans": "Jeans",
    "raincoat": "Raincoat",
    "bomberjacket": "Bomber Jacket",
    "quiltedjacket": "Quilted Jacket",
    "woolcoat": "Wool Coat",
    "ridersjacket": "Rider Jacket",
    "huntingjacket": "Hunter Jacket",
    "fieldjacket": "Field Jacket",
    "ttskojacket": "TTsKO Jacket",
    "hoodie": "Hoodie",
    "shirt": "Shirt",
    "tshirt": "T-Shirt",
    "mansuit": "Men's Suit",
    "womansuit": "Women's Suit",
    "woolgloves": "Wool Gloves",
    "woolglovesfingerless": "Fingerless Wool Gloves",
    "paddedgloves": "Padded Gloves",
    "surgicalgloves": "Surgical Gloves",
}

COLOR = {
    "black": "Black", "white": "White", "grey": "Grey", "gray": "Grey",
    "green": "Green", "red": "Red", "blue": "Blue", "lightblue": "Light Blue",
    "skyblue": "Sky Blue", "darkblue": "Dark Blue", "brown": "Brown",
    "darkbrown": "Dark Brown", "tan": "Tan", "beige": "Beige", "khaki": "Khaki",
    "olive": "Olive", "orange": "Orange", "yellow": "Yellow", "violet": "Violet",
    "pink": "Pink", "natural": "Natural", "summer": "Summer", "autumn": "Autumn",
    "winter": "Winter", "woodland": "Woodland", "camo": "Camo",
}

PREFIXES = ("loftd_", "mmg_", "fog_", "expansion")

# Longest first so compact classnames split around useful garment/equipment words.
COMPACT = [
    ("woolglovesfingerless", "Fingerless Wool Gloves"),
    ("assaultbackpack", "Assault Backpack"),
    ("carrierbackpack", "Carrier Backpack"),
    ("tacticalhelmet", "Tactical Helmet"),
    ("ballistichelmet", "Ballistic Helmet"),
    ("armoredhelmet", "Armored Helmet"),
    ("operatorshirt", "Operator Shirt"),
    ("tacticalshirt", "Tactical Shirt"),
    ("combatshirt", "Combat Shirt"),
    ("tacticalpants", "Tactical Pants"),
    ("combatpants", "Combat Pants"),
    ("ghilliebushrag", "Ghillie Bushrag"),
    ("ghilliehood", "Ghillie Hood"),
    ("ghilliesuit", "Ghillie Suit"),
    ("platecarrier", "Plate Carrier"),
    ("balaclavamask", "Balaclava Mask"),
    ("balaclava3holes", "3-Hole Balaclava"),
    ("booniehat", "Boonie Hat"),
    ("buckethat", "Bucket Hat"),
    ("cowboyhat", "Cowboy Hat"),
    ("beaniehat", "Beanie"),
    ("combatboots", "Combat Boots"),
    ("hikingboots", "Hiking Boots"),
    ("cargopants", "Cargo Pants"),
    ("woolgloves", "Wool Gloves"),
    ("facemask", "Face Mask"),
    ("backpack", "Backpack"),
    ("windbreaker", "Windbreaker"),
    ("jacket", "Jacket"), ("hoodie", "Hoodie"), ("shirt", "Shirt"),
    ("pants", "Pants"), ("shorts", "Shorts"), ("boots", "Boots"),
    ("shoes", "Shoes"), ("gloves", "Gloves"), ("helmet", "Helmet"),
    ("vest", "Vest"), ("pouch", "Pouch"), ("holster", "Holster"),
    ("sheath", "Sheath"), ("glasses", "Glasses"), ("goggles", "Goggles"),
    ("scarf", "Scarf"), ("cloak", "Cloak"), ("belt", "Belt"), ("bag", "Bag"),
]


def clean_piece(piece: str) -> str:
    low = piece.lower()
    if low in COLOR:
        return COLOR[low]
    if low in EXACT:
        return EXACT[low]

    for stem, label in COMPACT:
        if stem in low:
            before, after = low.split(stem, 1)
            out = []
            if before:
                out.append(COLOR.get(before, before.title()))
            out.append(label)
            if after:
                out.append(COLOR.get(after, after.upper() if len(after) <= 3 else after.title()))
            return " ".join(out)

    if low in {"mmg", "nvg", "jpc", "ucp", "nwu", "erdl", "gps"}:
        return low.upper()
    return piece.title()


def friendly(class_name: str) -> str:
    low = class_name.lower()
    text = low
    for prefix in PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break

    chunks = [c for c in re.split(r"[_-]+", text) if c]
    if not chunks:
        return class_name

    # Vanilla classnames generally use the final underscore token as the variant/color.
    base = chunks[0]
    if base in EXACT:
        name = EXACT[base]
        suffix = [clean_piece(c) for c in chunks[1:]]
        if suffix:
            return f"{name} - {' '.join(suffix)}"
        return name

    parts = [clean_piece(c) for c in chunks]
    name = " ".join(parts)
    replacements = {
        "T Shirt": "T-Shirt", "Nvg": "NVG", "Jpc": "JPC", "Ucp": "UCP",
        "Nwu": "NWU", "Erdl": "ERDL", "Atacs": "A-TACS", "Multicamblack": "Multicam Black",
        "Multicamtropic": "Multicam Tropic", "Dark Woodland": "Dark Woodland",
        "Grey Camo": "Grey Camo", "Red Rose": "Red Rose", "Blackw": "Black/Winter",
        "Camogr": "Camo Green", "Camowg": "Winter Camo", "Blu": "Blue", "Bl": "Black",
        "Krem": "Cream", "Salat": "Green", "Flektarnpixel": "Flecktarn Pixel",
    }
    for old, new in replacements.items():
        name = re.sub(rf"\b{re.escape(old)}\b", new, name, flags=re.I)
    return re.sub(r"\s+", " ", name).strip()


def main():
    if not CATALOGUE.exists():
        raise SystemExit(f"Missing {CATALOGUE}")
    text = CATALOGUE.read_text(encoding="utf-8")
    pattern = re.compile(r"name:'((?:\\'|[^'])*)',className:'((?:\\'|[^'])*)'")
    changed = 0

    def repl(match):
        nonlocal changed
        class_name = match.group(2).replace("\\'", "'")
        new_name = friendly(class_name).replace("'", "\\'")
        if new_name != match.group(1):
            changed += 1
        return f"name:'{new_name}',className:'{match.group(2)}'"

    updated = pattern.sub(repl, text)
    CATALOGUE.write_text(updated, encoding="utf-8")
    print(f"Polished {changed} Quinn clothing display names.")


if __name__ == "__main__":
    main()
