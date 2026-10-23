from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE_ROOT = ROOT / "data" / "live-market"
MARKET_DIR = LIVE_ROOT / "market"
TRADER_FILE = LIVE_ROOT / "traders" / "BM_Zombie_Note_Trader.json"
ZONE_FILE = LIVE_ROOT / "traderzones" / "Blackmarket_ZN.json"
MARKET_SETTINGS_FILE = LIVE_ROOT / "market-settings.json"
OUT_FILE = ROOT / "chernarus" / "traders" / "black-market-zombie-note" / "catalogue-data.js"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def title_words(value: str) -> str:
    special = {"gps": "GPS", "nbc": "NBC", "fog": "FOG", "fsb": "FSB", "cod": "CoD", "mags": "Magazines"}
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value).replace("-", "_").split("_")
    return " ".join(special.get(word.lower(), word.capitalize()) for word in words if word)


def friendly_name(class_name: str) -> str:
    lower = class_name.lower()
    explicit = {
        "compass": "Compass",
        "gpsreceiver": "GPS Receiver",
        "orienteeringcompass": "Orienteering Compass",
        "lbs_sleepingpacked_new_camo": "Camo Sleeping Bag",
    }
    if lower in explicit:
        return explicit[lower]
    return title_words(class_name)


def category_label(stem: str, data: dict | None = None) -> str:
    if data:
        display = data.get("DisplayName")
        if display:
            return display
    labels = {
        "Gebs_Fishing_Gear": "Geb's Fishing Gear",
        "Mag_Loader": "Mag Loaders",
        "Custom_Flags": "Custom Flags",
        "FOG_Gear_Higher_Tier": "FOG Higher-Tier Gear",
    }
    return labels.get(stem, title_words(stem))


def permission(value: int) -> tuple[bool, bool, bool]:
    value = int(value)
    if value == 0:
        return True, False, True
    if value == 1:
        return True, True, True
    if value == 2:
        return False, True, True
    return False, False, False


def market_index() -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for path in sorted(MARKET_DIR.glob("*.json"), key=lambda p: p.name.lower()):
        data = read_json(path)
        for item in data.get("Items", []):
            parent = item.get("ClassName")
            if not parent:
                continue
            entry = {
                "className": parent,
                "basePrice": float(item.get("MaxPriceThreshold", item.get("MinPriceThreshold", 0))),
                "sellPercent": item.get("SellPricePercent", -1),
                "categoryStem": path.stem,
                "categoryData": data,
            }
            for name in [parent] + list(item.get("Variants", []) or []):
                if name:
                    index.setdefault(name.lower(), []).append(dict(entry, className=name))
    return index


def effective_sell_percent(market: dict, zone: dict, global_percent: float) -> float:
    try:
        item_percent = float(market.get("sellPercent", -1))
    except (TypeError, ValueError):
        item_percent = -1
    if item_percent >= 0:
        return item_percent
    try:
        zone_percent = float(zone.get("SellPricePercent", -1))
    except (TypeError, ValueError):
        zone_percent = -1
    return zone_percent if zone_percent >= 0 else global_percent


def add_row(rows: dict[str, dict], class_name: str, trader_sells: bool, trader_buys: bool, market: dict, zone: dict, global_sell: float, buy_percent: float, category: str) -> None:
    base_price = market["basePrice"]
    row = {
        "name": friendly_name(class_name),
        "className": class_name,
        "category": category,
        "traderSells": trader_sells,
        "traderBuys": trader_buys,
    }
    if trader_sells:
        row["buyPrice"] = round(base_price * (buy_percent / 100.0))
    if trader_buys:
        row["sellPrice"] = round(base_price * (effective_sell_percent(market, zone, global_sell) / 100.0))
    rows[class_name.lower()] = row


def main() -> None:
    trader = read_json(TRADER_FILE)
    zone = read_json(ZONE_FILE)
    settings = read_json(MARKET_SETTINGS_FILE) if MARKET_SETTINGS_FILE.exists() else {}
    global_sell = float(settings.get("SellPricePercent", 75))
    buy_percent = float(zone.get("BuyPricePercent", 100))
    index = market_index()
    rows: dict[str, dict] = {}
    missing_categories: list[str] = []
    missing_items: list[str] = []

    for declaration in trader.get("Categories", []):
        if ":" in declaration:
            stem, raw = declaration.rsplit(":", 1)
            perm = int(raw)
        else:
            stem, perm = declaration, 0
        trader_sells, trader_buys, visible = permission(perm)
        if not visible:
            continue
        path = MARKET_DIR / f"{stem}.json"
        if not path.exists():
            missing_categories.append(stem)
            continue
        data = read_json(path)
        label = category_label(stem, data)
        for item in data.get("Items", []):
            parent = item.get("ClassName")
            if not parent:
                continue
            for class_name in [parent] + list(item.get("Variants", []) or []):
                candidates = index.get(class_name.lower(), [])
                if candidates:
                    add_row(rows, class_name, trader_sells, trader_buys, candidates[0], zone, global_sell, buy_percent, label)

    for class_name, raw_permission in trader.get("Items", {}).items():
        trader_sells, trader_buys, visible = permission(raw_permission)
        if not visible:
            continue
        candidates = index.get(class_name.lower(), [])
        if not candidates:
            missing_items.append(class_name)
            continue
        market = candidates[0]
        label = category_label(market["categoryStem"], market.get("categoryData"))
        add_row(rows, class_name, trader_sells, trader_buys, market, zone, global_sell, buy_percent, label)

    ordered = sorted(rows.values(), key=lambda x: (x["category"].lower(), x["name"].lower(), x["className"].lower()))
    encoded = []
    for item in ordered:
        fields = [
            "name:%s" % json.dumps(item["name"], ensure_ascii=False),
            "className:%s" % json.dumps(item["className"], ensure_ascii=False),
            "category:%s" % json.dumps(item["category"], ensure_ascii=False),
            "traderSells:%s" % str(item["traderSells"]).lower(),
            "traderBuys:%s" % str(item["traderBuys"]).lower(),
        ]
        if "buyPrice" in item:
            fields.append(f"buyPrice:{item['buyPrice']}")
        if "sellPrice" in item:
            fields.append(f"sellPrice:{item['sellPrice']}")
        encoded.append("{" + ",".join(fields) + "}")

    output = "window.traderCatalogue={traderName:'Black Market Zombie Note Trader',currency:'ZOMBIE_NOTES',currencyLabel:'Zombie Notes',items:[\n" + ",\n".join(encoded) + "\n]};\n"
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(output, encoding="utf-8")
    print(f"Built Black Market Zombie Note catalogue: {len(ordered)} items")
    if missing_categories:
        print("WARNING missing categories: " + ", ".join(missing_categories))
    if missing_items:
        print("WARNING explicit items not found in Market JSON: " + ", ".join(missing_items))


if __name__ == "__main__":
    main()
