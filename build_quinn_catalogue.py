from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = ROOT / "data" / "live-market"
MARKET = LIVE / "market"
TRADERS = LIVE / "traders"
ZONES = LIVE / "traderzones"
OUT = ROOT / "chernarus" / "traders" / "quinn" / "catalogue-data.js"

TRADER_FILE = TRADERS / "Clothing.json"
ZONE_FILE = ZONES / "Main_Clothing_Trader.json"

CATEGORY_LABELS = {
    "Backpacks": "Backpacks",
    "Armbands": "Armbands",
    "Boots_And_Shoes": "Boots & Shoes",
    "Eyewear": "Eyewear",
    "Masks": "Masks",
    "Helmets": "Helmets",
    "Bandanas": "Bandanas",
    "Caps": "Caps",
    "Coats_And_Jackets": "Coats & Jackets",
    "Pants_And_Shorts": "Pants & Shorts",
    "Hats_And_Hoods": "Hats & Hoods",
    "Blouses_And_Suits": "Blouses & Suits",
    "Shirts_And_TShirts": "Shirts & T-Shirts",
    "Holsters_And_Pouches": "Holsters & Pouches",
    "Vests": "Vests",
    "Belts": "Belts",
    "FOG_Gear_Lower_Tier": "FOG Gear",
    "Ghillies": "Ghillies",
    "Sweaters_And_Hoodies": "Sweaters & Hoodies",
    "Gloves": "Gloves",
    "Skirts_And_Dresses": "Skirts & Dresses",
    "MMG": "MMG Gear",
}

EXPLICIT_NAMES = {
    "platecarriervest": "Plate Carrier Vest",
    "highcapacityvest_olive": "High Capacity Vest - Olive",
    "pressvest_lightblue": "Press Vest - Light Blue",
    "smershvest": "Smersh Vest",
    "gasmask": "Gas Mask",
    "ballistichelmet_green": "Ballistic Helmet - Green",
    "ballistichelmet_woodland": "Ballistic Helmet - Woodland",
    "weaponholster": "Weapon Holster",
    "chestholster": "Chest Holster",
}

COLORS = {
    "black":"Black","white":"White","grey":"Grey","gray":"Grey","green":"Green","red":"Red","blue":"Blue",
    "lightblue":"Light Blue","darkblue":"Dark Blue","brown":"Brown","darkbrown":"Dark Brown","tan":"Tan","beige":"Beige",
    "khaki":"Khaki","haki":"Khaki","olive":"Olive","orange":"Orange","yellow":"Yellow","violet":"Violet","pink":"Pink",
    "winter":"Winter","woodland":"Woodland","camo":"Camo","multicam":"Multicam","alpine":"Alpine","ucp":"UCP","atacs":"A-TACS",
    "dubok":"Dubok","flora":"Flora","steppe":"Steppe","marpat":"MARPAT","nwu":"NWU","erdl":"ERDL","desert":"Desert",
}

TERMS = [
    ("assaultbackpack", "Assault Backpack"), ("backpack", "Backpack"), ("carrierbackpack", "Carrier Backpack"),
    ("tacticalhelmet", "Tactical Helmet"), ("ballistichelmet", "Ballistic Helmet"), ("armoredhelmet", "Armored Helmet"),
    ("booniehat", "Boonie Hat"), ("buckethat", "Bucket Hat"), ("cowboyhat", "Cowboy Hat"), ("beaniehat", "Beanie"),
    ("balaclavamask", "Balaclava Mask"), ("balaclava3holes", "3-Hole Balaclava"), ("facemask", "Face Mask"),
    ("operatorshirt", "Operator Shirt"), ("combatshirt", "Combat Shirt"), ("tacticalshirt", "Tactical Shirt"),
    ("tshirt", "T-Shirt"), ("shirt", "Shirt"), ("jacket", "Jacket"), ("hoodie", "Hoodie"), ("coat", "Coat"),
    ("combatpants", "Combat Pants"), ("tacticalpants", "Tactical Pants"), ("cargopants", "Cargo Pants"),
    ("pants", "Pants"), ("shorts", "Shorts"), ("leggings", "Leggings"), ("dress", "Dress"), ("skirt", "Skirt"),
    ("combatboots", "Combat Boots"), ("hikingboots", "Hiking Boots"), ("boots", "Boots"), ("shoes", "Shoes"),
    ("woolglovesfingerless", "Fingerless Wool Gloves"), ("woolgloves", "Wool Gloves"), ("gloves", "Gloves"),
    ("plate", "Plate Carrier"), ("armor", "Armor"), ("vest", "Vest"), ("belt", "Belt"),
    ("magpouch", "Magazine Pouch"), ("ammo_pouch", "Ammo Pouch"), ("pouch", "Pouch"), ("holster", "Holster"),
    ("sheath", "Sheath"), ("camelback", "CamelBak"), ("headphones", "Headphones"), ("eyewear", "Eyewear"),
    ("glasses", "Glasses"), ("goggles", "Goggles"), ("scarf", "Scarf"), ("cloak", "Cloak"), ("bag", "Bag"),
]

PREFIXES = ("loftd_", "mmg_", "fog_", "expansion")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def js_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def split_compact(token: str) -> str:
    low = token.lower()
    if low in COLORS:
        return COLORS[low]
    for key, label in TERMS:
        if key in low:
            before, after = low.split(key, 1)
            parts = []
            if before:
                parts.append(COLORS.get(before, before.title()))
            parts.append(label)
            if after:
                parts.append(COLORS.get(after, after.upper() if len(after) <= 3 else after.title()))
            return " ".join(parts)
    return token.upper() if len(token) <= 3 and token.isalpha() else token.title()


def friendly_name(class_name: str) -> str:
    lower = class_name.lower()
    if lower in EXPLICIT_NAMES:
        return EXPLICIT_NAMES[lower]

    text = lower
    for prefix in PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break

    chunks = [c for c in re.split(r"[_-]+", text) if c]
    words = [split_compact(chunk) for chunk in chunks]
    name = " ".join(words)
    replacements = {
        "T Shirt": "T-Shirt", "Tshirt": "T-Shirt", "Nvg": "NVG", "Gps": "GPS", "Jpc": "JPC",
        "Mk Iii": "MK III", "Mk Iv": "MK IV", "Mk V": "MK V", "Mmps": "MMPS", "Gp Nvg": "GP NVG",
        "Blackw": "Black/Winter", "Camogr": "Camo Green", "Camowg": "Winter Camo", "Gr": "Green",
        "Blu": "Blue", "Bl": "Black", "Krem": "Cream", "Salat": "Green", "Flektarnpixel": "Flecktarn Pixel",
    }
    for old, new in replacements.items():
        name = re.sub(rf"\b{re.escape(old)}\b", new, name, flags=re.I)
    return re.sub(r"\s+", " ", name).strip()


def parse_permission(value: int):
    value = int(value)
    return {
        0: (True, False, True),
        1: (True, True, True),
        2: (False, True, True),
        3: (False, False, False),
    }.get(value, (False, False, False))


def category_label(stem: str) -> str:
    return CATEGORY_LABELS.get(stem, stem.replace("_", " "))


def build_market_index():
    index = {}
    for path in MARKET.glob("*.json"):
        data = read_json(path)
        for item in data.get("Items", []):
            parent = item.get("ClassName")
            if not parent:
                continue
            entry = {
                "source": path.stem,
                "price": float(item.get("MaxPriceThreshold", item.get("MinPriceThreshold", 0))),
                "sellPercent": item.get("SellPricePercent", -1),
            }
            for name in [parent] + list(item.get("Variants", []) or []):
                if name:
                    index.setdefault(name.lower(), entry)
    return index


def effective_sell_percent(item_percent, zone_percent):
    try:
        p = float(item_percent)
    except (TypeError, ValueError):
        p = -1
    if p >= 0:
        return p
    return float(zone_percent)


def main():
    trader = read_json(TRADER_FILE)
    zone = read_json(ZONE_FILE)
    market_index = build_market_index()
    buy_percent = float(zone.get("BuyPricePercent", 100))
    zone_sell_percent = float(zone.get("SellPricePercent", 75))
    rows = {}
    missing_categories = []
    missing_items = []

    for declaration in trader.get("Categories", []):
        if ":" in declaration:
            stem, raw = declaration.rsplit(":", 1)
            permission = int(raw)
        else:
            stem, permission = declaration, 0
        trader_sells, trader_buys, visible = parse_permission(permission)
        if not visible:
            continue
        path = MARKET / f"{stem}.json"
        if not path.exists():
            missing_categories.append(stem)
            continue
        label = category_label(stem)
        data = read_json(path)
        for item in data.get("Items", []):
            parent = item.get("ClassName")
            if not parent:
                continue
            base_price = float(item.get("MaxPriceThreshold", item.get("MinPriceThreshold", 0)))
            sell_percent = effective_sell_percent(item.get("SellPricePercent", -1), zone_sell_percent)
            for class_name in [parent] + list(item.get("Variants", []) or []):
                if not class_name:
                    continue
                row = {
                    "name": friendly_name(class_name), "className": class_name, "category": label,
                    "traderSells": trader_sells, "traderBuys": trader_buys,
                }
                if trader_sells:
                    row["buyPrice"] = round(base_price * buy_percent / 100.0)
                if trader_buys:
                    row["sellPrice"] = round(base_price * sell_percent / 100.0)
                rows[class_name.lower()] = row

    for class_name, permission in trader.get("Items", {}).items():
        trader_sells, trader_buys, visible = parse_permission(permission)
        key = class_name.lower()
        if not visible:
            rows.pop(key, None)
            continue
        market = market_index.get(key)
        if not market:
            missing_items.append(class_name)
            continue
        sell_percent = effective_sell_percent(market.get("sellPercent", -1), zone_sell_percent)
        row = {
            "name": friendly_name(class_name), "className": class_name,
            "category": category_label(market["source"]),
            "traderSells": trader_sells, "traderBuys": trader_buys,
        }
        if trader_sells:
            row["buyPrice"] = round(market["price"] * buy_percent / 100.0)
        if trader_buys:
            row["sellPrice"] = round(market["price"] * sell_percent / 100.0)
        rows[key] = row

    ordered = sorted(rows.values(), key=lambda x: (x["category"].lower(), x["name"].lower(), x["className"].lower()))
    lines = []
    for item in ordered:
        fields = [
            f"name:'{js_escape(item['name'])}'", f"className:'{js_escape(item['className'])}'",
            f"category:'{js_escape(item['category'])}'",
            f"traderSells:{str(item['traderSells']).lower()}", f"traderBuys:{str(item['traderBuys']).lower()}",
        ]
        if "buyPrice" in item:
            fields.append(f"buyPrice:{int(item['buyPrice'])}")
        if "sellPrice" in item:
            fields.append(f"sellPrice:{int(item['sellPrice'])}")
        lines.append("{" + ",".join(fields) + "}")

    OUT.write_text("window.traderCatalogue={traderName:'Quinn',currency:'USD',items:[\n" + ",\n".join(lines) + "\n]};\n", encoding="utf-8")
    print(f"Built Quinn: {len(ordered)} clothing/gear items from Clothing.json + Main_Clothing_Trader.json")
    if missing_categories:
        print("WARNING missing categories: " + ", ".join(missing_categories))
    if missing_items:
        print(f"WARNING {len(missing_items)} explicit items were not found in market JSON")


if __name__ == "__main__":
    main()
