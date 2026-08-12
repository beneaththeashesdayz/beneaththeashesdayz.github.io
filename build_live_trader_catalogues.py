from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE_ROOT = ROOT / "data" / "live-market"
MARKET_DIR = LIVE_ROOT / "market"
ZONE_DIR = LIVE_ROOT / "traderzones"

TRADERS = {
    "naomi": {
        "name": "Naomi",
        "zone": "Main_Consumables_Trader.json",
        "currency": "USD",
        "currency_label": None,
    },
    "rolf": {
        "name": "Rolf",
        "zone": "Main_ZombieNote_Trader.json",
        "currency": "ZOMBIE_NOTES",
        "currency_label": "Zombie Notes",
    },
}

ITEM_RE = re.compile(
    r"\{name:'(?P<name>(?:\\'|[^'])*)',className:'(?P<class>(?:\\'|[^'])*)',"
    r"category:(?P<q>['\"])(?P<category>.*?)(?P=q),mode:'(?P<mode>buy|sell)',price:(?P<price>-?\d+(?:\.\d+)?)\}"
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def js_unescape(value: str) -> str:
    return value.replace("\\'", "'").replace("\\\\", "\\")


def js_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def title_words(value: str) -> str:
    words = value.replace("-", "_").split("_")
    special = {
        "gps": "GPS",
        "nbc": "NBC",
        "zedklr": "ZedKLR",
        "rick": "Rick",
        "morty": "Morty",
    }
    return " ".join(special.get(word.lower(), word.capitalize()) for word in words if word)


def special_friendly_name(class_name: str) -> str | None:
    lower = class_name.lower()

    geb_match = re.fullmatch(r"geb_([a-z]+)fish(hat|shirt|gloves)", lower)
    if geb_match:
        color, item_type = geb_match.groups()
        label = {
            "hat": "Fish Hat",
            "shirt": "Fish Shirt",
            "gloves": "Fishing Gloves",
        }[item_type]
        return f"{color.capitalize()} {label}"

    sleeping_prefixes = (
        "lbs_sleepingpacked_new_",
        "lbs_sleepingpacked_extended_",
        "lbs_sleepingpacked_old_",
    )
    for prefix in sleeping_prefixes:
        if lower.startswith(prefix):
            theme = lower[len(prefix):]
            theme_name = title_words(theme)
            theme_name = theme_name.replace("Rick And Morty", "Rick & Morty")
            return f"{theme_name} Sleeping Bag"

    return None


def friendly_from_classname(class_name: str) -> str:
    special = special_friendly_name(class_name)
    if special:
        return special
    text = re.sub(r"[_-]+", " ", class_name)
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return " ".join(word.capitalize() for word in text.split())


def category_from_filename(path: Path) -> str:
    if path.name == "Gebs_Fishing_Gear.json":
        return "Geb's Fishing Gear"
    return path.stem.replace("_", " ")


def load_curated_metadata(slug: str) -> dict[str, dict]:
    path = ROOT / "chernarus" / "traders" / slug / "catalogue-data.js"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    metadata = {}
    for match in ITEM_RE.finditer(text):
        class_name = js_unescape(match.group("class"))
        metadata[class_name.lower()] = {
            "name": js_unescape(match.group("name")),
            "category": js_unescape(match.group("category")),
        }
    return metadata


def add_market_entry(index: dict[str, list[dict]], class_name: str, entry: dict) -> None:
    key = class_name.lower()
    existing = index.setdefault(key, [])
    if not any(x["source"] == entry["source"] and x["price"] == entry["price"] for x in existing):
        existing.append(entry)


def build_market_index() -> dict[str, list[dict]]:
    """Index Expansion parent items and every Variant classname.

    Trader zones can reference a variant directly even when the market file stores
    that classname only inside a parent item's Variants array. Variants inherit the
    parent market entry's price and category.
    """
    index: dict[str, list[dict]] = {}
    for path in sorted(MARKET_DIR.glob("*.json"), key=lambda p: p.name.lower()):
        data = read_json(path)
        for item in data.get("Items", []):
            class_name = item.get("ClassName")
            if not class_name:
                continue
            entry = {
                "className": class_name,
                "category": category_from_filename(path),
                "price": item.get("MaxPriceThreshold", item.get("MinPriceThreshold", 0)),
                "source": path.name,
            }
            add_market_entry(index, class_name, entry)
            for variant in item.get("Variants", []) or []:
                if variant:
                    variant_entry = dict(entry)
                    variant_entry["className"] = variant
                    add_market_entry(index, variant, variant_entry)
    return index


def choose_market_entry(class_name: str, candidates: list[dict], curated: dict | None) -> dict:
    if curated:
        wanted = curated.get("category", "").lower().replace("'", "")
        for candidate in candidates:
            candidate_category = candidate["category"].lower().replace("'", "")
            if candidate_category == wanted:
                return candidate
            if wanted in candidate_category or candidate_category in wanted:
                return candidate
    return candidates[0]


def build_trader(slug: str, cfg: dict, market_index: dict[str, list[dict]]) -> None:
    zone = read_json(ZONE_DIR / cfg["zone"])
    curated = load_curated_metadata(slug)
    rows = []
    missing = []

    for class_name, stock_value in zone.get("Stock", {}).items():
        candidates = market_index.get(class_name.lower(), [])
        if not candidates:
            missing.append(class_name)
            continue

        curated_item = curated.get(class_name.lower())
        market = choose_market_entry(class_name, candidates, curated_item)

        # Known mod classname families get a deterministic human-friendly name even
        # if an earlier generated catalogue contained a rough fallback name.
        special_name = special_friendly_name(class_name)
        name = special_name or (curated_item["name"] if curated_item else friendly_from_classname(class_name))

        # Market-file category is authoritative for known categories such as Geb's
        # Fishing Gear; curated labels remain preferred elsewhere.
        if market["source"] == "Gebs_Fishing_Gear.json":
            category = "Geb's Fishing Gear"
        else:
            category = curated_item["category"] if curated_item else market["category"]

        mode = "buy" if int(stock_value) == 1 else "sell"
        rows.append(
            {
                "name": name,
                "className": class_name,
                "category": category,
                "mode": mode,
                "price": market["price"],
            }
        )

    category_order = []
    for item in curated.values():
        category = "Geb's Fishing Gear" if item["category"] == "Gebs Fishing Gear" else item["category"]
        if category not in category_order:
            category_order.append(category)
    order_lookup = {name: i for i, name in enumerate(category_order)}
    rows.sort(key=lambda x: (order_lookup.get(x["category"], 999), x["category"].lower(), x["name"].lower()))

    header = f"window.traderCatalogue={{traderName:'{js_escape(cfg['name'])}',currency:'{js_escape(cfg['currency'])}'"
    if cfg.get("currency_label"):
        header += f",currencyLabel:'{js_escape(cfg['currency_label'])}'"
    header += ",items:[\n"

    lines = []
    for item in rows:
        price = item["price"]
        if isinstance(price, float) and price.is_integer():
            price = int(price)
        lines.append(
            "{name:'%s',className:'%s',category:'%s',mode:'%s',price:%s}"
            % (
                js_escape(item["name"]),
                js_escape(item["className"]),
                js_escape(item["category"]),
                item["mode"],
                price,
            )
        )

    output = header + ",\n".join(lines) + "\n]};\n"
    out_path = ROOT / "chernarus" / "traders" / slug / "catalogue-data.js"
    out_path.write_text(output, encoding="utf-8")
    print(f"Built {slug}: {len(rows)} live items from {cfg['zone']}")
    if missing:
        print(f"WARNING {slug}: {len(missing)} stock items were not found in Market JSON: {', '.join(missing)}")


def main() -> None:
    if not MARKET_DIR.exists() or not ZONE_DIR.exists():
        raise SystemExit("Live market snapshot is missing. Run sync_gtx_market.py first.")
    market_index = build_market_index()
    for slug, cfg in TRADERS.items():
        build_trader(slug, cfg, market_index)


if __name__ == "__main__":
    main()
