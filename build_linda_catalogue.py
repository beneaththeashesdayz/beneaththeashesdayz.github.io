from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKET_FILE = ROOT / "data" / "live-market" / "market" / "Medical.json"
TRADER_FILE = ROOT / "data" / "live-market" / "traders" / "Medicals.json"
ZONE_FILE = ROOT / "data" / "live-market" / "traderzones" / "Main_Medicals_Trader.json"
SETTINGS_FILE = ROOT / "data" / "live-market" / "market-settings.json"
OUT_FILE = ROOT / "chernarus" / "traders" / "linda" / "catalogue-data.js"

FRIENDLY_NAMES = {
    "anticheminjector": "PO-X Antidote Injector",
    "bandagedressing": "Bandage Dressing",
    "bloodbagempty": "Empty Blood Bag",
    "bloodtestkit": "Blood Test Kit",
    "charcoaltablets": "Charcoal Tablets",
    "chelatingtablets": "Chelating Tablets",
    "disinfectantalcohol": "Alcohol Tincture",
    "disinfectantspray": "Disinfectant Spray",
    "epinephrine": "Epinephrine Auto-Injector",
    "firstaidkit": "First Aid Kit",
    "gasmask_filter": "Gas Mask Filter",
    "heatpack": "Heat Pack",
    "iodinetincture": "Iodine Tincture",
    "morphine": "Morphine Auto-Injector",
    "painkillertablets": "Codeine Pills",
    "purificationtablets": "Chlorine Tablets",
    "salinebag": "Saline Bag",
    "startkitiv": "IV Start Kit",
    "tetracyclineantibiotics": "Tetracycline Antibiotics",
    "thermometer": "Medical Thermometer",
    "vitaminbottle": "Multivitamin Pills",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def js_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def permission(value: int) -> tuple[bool, bool]:
    value = int(value)
    return value in (0, 1), value in (1, 2)


def effective_sell_percent(item: dict, zone: dict, settings: dict) -> float:
    item_percent = float(item.get("SellPricePercent", -1))
    if item_percent >= 0:
        return item_percent
    zone_percent = float(zone.get("SellPricePercent", -1))
    if zone_percent >= 0:
        return zone_percent
    return float(settings.get("SellPricePercent", 75))


def main() -> None:
    market = load(MARKET_FILE)
    trader = load(TRADER_FILE)
    zone = load(ZONE_FILE)
    settings = load(SETTINGS_FILE)

    medical_permission = None
    for declaration in trader.get("Categories", []):
        stem, raw = declaration.rsplit(":", 1) if ":" in declaration else (declaration, "0")
        if stem == "Medical":
            medical_permission = int(raw)
            break
    if medical_permission is None:
        raise SystemExit("Medicals.json does not expose Medical category")

    trader_sells, trader_buys = permission(medical_permission)
    buy_percent = float(zone.get("BuyPricePercent", 100))

    rows = []
    for item in market.get("Items", []):
        class_name = item.get("ClassName")
        if not class_name:
            continue
        base_price = float(item.get("MaxPriceThreshold", item.get("MinPriceThreshold", 0)))
        row = {
            "name": FRIENDLY_NAMES.get(class_name.lower(), class_name),
            "className": class_name,
            "category": "Medical Supplies",
            "traderSells": trader_sells,
            "traderBuys": trader_buys,
        }
        if trader_sells:
            row["buyPrice"] = round(base_price * buy_percent / 100.0)
        if trader_buys:
            sell_percent = effective_sell_percent(item, zone, settings)
            row["sellPrice"] = round(base_price * sell_percent / 100.0)
        rows.append(row)

    rows.sort(key=lambda row: row["name"].lower())
    lines = []
    for row in rows:
        lines.append(
            "{name:'%s',className:'%s',category:'%s',buyPrice:%d,sellPrice:%d,traderSells:true,traderBuys:true}"
            % (
                js_escape(row["name"]),
                js_escape(row["className"]),
                js_escape(row["category"]),
                row["buyPrice"],
                row["sellPrice"],
            )
        )

    output = "window.traderCatalogue={traderName:'Linda',currency:'USD',items:[\n" + ",\n".join(lines) + "\n]};\n"
    OUT_FILE.write_text(output, encoding="utf-8")
    print(f"Built Linda: {len(rows)} medical items from Medicals.json + Main_Medicals_Trader.json")


if __name__ == "__main__":
    main()
