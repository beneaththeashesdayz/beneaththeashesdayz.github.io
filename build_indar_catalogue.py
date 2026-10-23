from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = ROOT / "data" / "live-market"
MARKET = LIVE / "market"
TRADER = LIVE / "traders" / "Weapons.json"
ZONE = LIVE / "traderzones" / "Main_Weapons_Trader.json"
SETTINGS = LIVE / "market-settings.json"
OUT = ROOT / "chernarus" / "traders" / "indar" / "catalogue-data.js"

LABELS = {
    "Melee_Weapons": "Vanilla Melee Weapons",
    "Knifes": "Vanilla Knives",
    "MYDF_Weapons": "My DF Weapons",
    "MYDF_Melee": "My DF Melee Weapons",
}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def permission(value):
    value = int(value)
    return {0: (True, False), 1: (True, True), 2: (False, True), 3: (False, False)}.get(value, (False, False))


def friendly(class_name):
    text = class_name
    for prefix in ("My_DF_Weapons_", "my_df_weapons_"):
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):]
            break
    text = re.sub(r"[_-]+", " ", text)
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    special = {"Dmr":"DMR", "Smg":"SMG", "Lmg":"LMG", "Ak":"AK", "Akm":"AKM", "Sks":"SKS", "Svd":"SVD", "Aug":"AUG", "Uzi":"Uzi", "Mp":"MP", "M4a1":"M4A1", "M16a4":"M16A4", "Sr25":"SR-25", "Sv98":"SV-98", "R93":"R93", "P90":"P90", "Pp19":"PP-19", "Qbz191":"QBZ-191", "Qbz95":"QBZ-95", "Scarh":"SCAR-H", "Sg553":"SG553", "Ak12":"AK-12", "Aks74u":"AKS-74U", "M1911":"M1911"}
    words=[]
    for w in text.split():
        cap=w.capitalize()
        words.append(special.get(cap, cap))
    return " ".join(words)


def js(value):
    return value.replace("\\", "\\\\").replace("'", "\\'")


def main():
    trader = load(TRADER)
    zone = load(ZONE)
    settings = load(SETTINGS) if SETTINGS.exists() else {}
    global_sell = float(settings.get("SellPricePercent", 75))
    buy_pct = float(zone.get("BuyPricePercent", 100))

    market_index = {}
    category_items = {}
    for path in MARKET.glob("*.json"):
        data = load(path)
        category_items[path.stem] = data.get("Items", [])
        for item in data.get("Items", []):
            names = [item.get("ClassName")] + list(item.get("Variants", []) or [])
            for name in names:
                if name:
                    market_index[name.lower()] = (path.stem, item)

    rows = {}
    for declaration in trader.get("Categories", []):
        stem, raw = declaration.rsplit(":", 1) if ":" in declaration else (declaration, "0")
        sells, buys = permission(raw)
        for item in category_items.get(stem, []):
            names = [item.get("ClassName")] + list(item.get("Variants", []) or [])
            base = float(item.get("MaxPriceThreshold", item.get("MinPriceThreshold", 0)))
            sell_pct = float(item.get("SellPricePercent", -1))
            if sell_pct < 0:
                sell_pct = float(zone.get("SellPricePercent", -1))
            if sell_pct < 0:
                sell_pct = global_sell
            for name in names:
                if not name:
                    continue
                row = {"name": friendly(name), "className": name, "category": LABELS.get(stem, stem.replace("_", " ")), "traderSells": sells, "traderBuys": buys}
                if sells: row["buyPrice"] = round(base * buy_pct / 100)
                if buys: row["sellPrice"] = round(base * sell_pct / 100)
                rows[name.lower()] = row

    for name, raw in trader.get("Items", {}).items():
        sells, buys = permission(raw)
        if not sells and not buys:
            rows.pop(name.lower(), None)
            continue
        found = market_index.get(name.lower())
        if not found:
            continue
        stem, item = found
        base = float(item.get("MaxPriceThreshold", item.get("MinPriceThreshold", 0)))
        sell_pct = float(item.get("SellPricePercent", -1))
        if sell_pct < 0: sell_pct = float(zone.get("SellPricePercent", -1))
        if sell_pct < 0: sell_pct = global_sell
        row = {"name": friendly(name), "className": name, "category": LABELS.get(stem, stem.replace("_", " ")), "traderSells": sells, "traderBuys": buys}
        if sells: row["buyPrice"] = round(base * buy_pct / 100)
        if buys: row["sellPrice"] = round(base * sell_pct / 100)
        rows[name.lower()] = row

    ordered = sorted(rows.values(), key=lambda r: (r["category"].lower(), r["name"].lower()))
    lines=[]
    for r in ordered:
        fields=[f"name:'{js(r['name'])}'", f"className:'{js(r['className'])}'", f"category:'{js(r['category'])}'", f"traderSells:{str(r['traderSells']).lower()}", f"traderBuys:{str(r['traderBuys']).lower()}"]
        if "buyPrice" in r: fields.append(f"buyPrice:{r['buyPrice']}")
        if "sellPrice" in r: fields.append(f"sellPrice:{r['sellPrice']}")
        lines.append("{" + ",".join(fields) + "}")
    OUT.write_text("window.traderCatalogue={traderName:'Indar',currency:'USD',items:[\n" + ",\n".join(lines) + "\n]};\n", encoding="utf-8")
    print(f"Built Indar catalogue: {len(ordered)} items")

if __name__ == "__main__":
    main()
