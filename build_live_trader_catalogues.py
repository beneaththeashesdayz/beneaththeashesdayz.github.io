from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE_ROOT = ROOT / "data" / "live-market"
MARKET_DIR = LIVE_ROOT / "market"
TRADERS_DIR = LIVE_ROOT / "traders"
ZONE_DIR = LIVE_ROOT / "traderzones"
MARKET_SETTINGS_FILE = LIVE_ROOT / "market-settings.json"

TRADERS = {
    "naomi": {
        "name": "Naomi",
        "zone": "Main_Consumables_Trader.json",
        "currency": "USD",
        "currency_label": None,
        # Naomi's normal consumables are available in both directions. Gardening
        # stock is the deliberate exception: players may sell it to Naomi only.
        "inherited_category_buyback": True,
        "buyback_excluded_categories": ["Gardening"],
    },
    "rolf": {
        "name": "Rolf",
        "zone": "Main_ZombieNote_Trader.json",
        "currency": "ZOMBIE_NOTES",
        "currency_label": "Zombie Notes",
    },
}

TRADER_CONFIG_CATALOGUES = {
    "gabi": {
        "name": "Gabi",
        "trader": "Collectables_Trader_Main.json",
        "zone": "Collectables.json",
        "currency": "USD",
        "currency_label": None,
        "group_collectable_variants": True,
    },
    "attachment-trader": {
        "name": "Attachment Trader",
        "trader": "Attachments.json",
        "zone": "Main_Attachments_Trader.json",
        "currency": "USD",
        "currency_label": None,
    },
    "emberline-motors": {
        "name": "Emberline Motors",
        "trader": "Exotic_Vehicle_Trader.json",
        "zone": "ExoticVehicleTrader.json",
        "currency": "ZOMBIE_NOTES",
        "currency_label": "Zombie Notes",
        "use_market_display_names": True,
    },
    "emberline-parts": {
        "name": "Emberline Parts",
        "trader": "Exotric_Vehicle_Parts.json",
        "zone": "ExoticVehicleTrader.json",
        "currency": "ZOMBIE_NOTES",
        "currency_label": "Zombie Notes",
        "use_market_display_names": True,
    },
}

CATEGORY_LABELS = {
    "Drippy_Sneakers": "Drippy Sneakers",
    "Paragon_Collectables": "Paragon Collectables",
    "Pokemon": "Pokémon Collection Boxes",
    "Vyse_Collectables": "Vyse Collectables",
    "Fallout": "Fallout Collectables",
    "Fallout_Bobbleheads": "Fallout Bobbleheads",
    "Fallout_Nuka_Cola": "Fallout Nuka-Cola",
    "Adult_Toys": "Adult Toys",
    "Collector_Cards_Storage": "Collector Card Storage",
    "MYDF_Attachments": "My DF Attachments",
    "MYDF_Ammo": "My DF Ammo",
    "MYDF_Mags": "My DF Magazines",
    "Haralds_Ammo": "Harald's Ammo",
    "Morty's_Ammo": "Morty's Ammo",
    "Ammo": "Vanilla Ammo",
    "Magazines": "Vanilla Magazines",
    "Bayonets": "Bayonets",
    "Buttstocks": "Buttstocks",
    "Handguards": "Handguards",
    "Optics": "Optics",
    "Batteries": "Batteries",
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
        "my": "My",
        "df": "DF",
        "mags": "Magazines",
        "ammo": "Ammo",
    }
    return " ".join(special.get(word.lower(), word.capitalize()) for word in words if word)


def special_friendly_name(class_name: str) -> str | None:
    lower = class_name.lower()

    pokemon_box = re.fullmatch(r"pokemoncard_sealedbox(\d+)", lower)
    if pokemon_box:
        return f"Sealed Pokémon Collection Box {pokemon_box.group(1)}"

    pokemon_storage = re.fullmatch(r"pokemoncard_box(\d+)", lower)
    if pokemon_storage:
        return f"Pokémon Card Storage Box {pokemon_storage.group(1)}"

    if lower == "dlt_falloutz_bobbleheadstandkit":
        return "Fallout Bobblehead Display Stand Kit"
    fallout_bobblehead = re.fullmatch(r"dlt_falloutz_bobblehead(.+)", lower)
    if fallout_bobblehead:
        skill = title_words(fallout_bobblehead.group(1))
        skill = skill.replace("Biggun", "Big Guns").replace("Smallgun", "Small Guns")
        return f"Fallout {skill} Bobblehead"

    if lower == "dlt_falloutz_nukacolarackkit":
        return "Fallout Nuka-Cola Display Rack Kit"
    nuka_cola = re.fullmatch(r"dlt_falloutz_nukacola(?:_(.+))?", lower)
    if nuka_cola:
        flavor = title_words(nuka_cola.group(1) or "Classic")
        return f"Fallout Nuka-Cola {flavor}"

    yugioh_card = re.fullmatch(r"vyse_yugioh_card_(\d+)", lower)
    if yugioh_card:
        return f"Yu-Gi-Oh! Card {int(yugioh_card.group(1))}"

    explicit_collectables = {
        "unciv_dayz_cardalbum_s1": "Collector Card Album",
        "unciv_graded_sleeve": "Graded Card Sleeve",
        "fallout_eyebottoy": "Fallout Eyebot Toy",
        "fallout_rockettoy": "Fallout Rocket Toy",
        "fallout_sheriffbadge": "Fallout Sheriff Badge",
    }
    if lower in explicit_collectables:
        return explicit_collectables[lower]

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

    explicit = {
        "weaponcleaningkit": "Weapon Cleaning Kit",
        "ammo_40mm_chemgas": "40mm PO-X Grenade",
        "ammo_40mm_explosive": "40mm Explosive Grenade",
        "ammo_40mm_smoke_black": "40mm Smoke Grenade - Black",
        "ammo_40mm_smoke_green": "40mm Smoke Grenade - Green",
        "ammo_40mm_smoke_red": "40mm Smoke Grenade - Red",
        "ammo_40mm_smoke_white": "40mm Smoke Grenade - White",
    }
    return explicit.get(lower)


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


def category_label(stem: str) -> str:
    return CATEGORY_LABELS.get(stem, title_words(stem))


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
    """Index Expansion parent items and every Variant classname."""
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
                "sellPricePercent": item.get("SellPricePercent", -1),
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


def effective_sell_percent(market: dict, zone: dict, global_sell_percent: float | None = None) -> float | None:
    item_percent = market.get("sellPricePercent", -1)
    try:
        item_percent = float(item_percent)
    except (TypeError, ValueError):
        item_percent = -1
    if item_percent >= 0:
        return item_percent

    zone_percent = zone.get("SellPricePercent", -1)
    try:
        zone_percent = float(zone_percent)
    except (TypeError, ValueError):
        zone_percent = -1
    if zone_percent >= 0:
        return zone_percent

    return global_sell_percent


def format_js_catalogue(slug: str, cfg: dict, rows: list[dict]) -> None:
    header = f"window.traderCatalogue={{traderName:'{js_escape(cfg['name'])}',currency:'{js_escape(cfg['currency'])}'"
    if cfg.get("currency_label"):
        header += f",currencyLabel:'{js_escape(cfg['currency_label'])}'"
    if cfg.get("group_collectable_variants"):
        header += ",groupCollectableVariants:true"
    header += ",items:[\n"

    lines = []
    for item in rows:
        fields = [
            "name:'%s'" % js_escape(item["name"]),
            "className:'%s'" % js_escape(item["className"]),
            "category:'%s'" % js_escape(item["category"]),
        ]
        if "mode" in item:
            fields.append("mode:'%s'" % item["mode"])
        if "price" in item:
            price = item["price"]
            if isinstance(price, float) and price.is_integer():
                price = int(price)
            fields.append(f"price:{price}")
        if "buyPrice" in item:
            fields.append(f"buyPrice:{int(item['buyPrice'])}")
        if "sellPrice" in item:
            fields.append(f"sellPrice:{int(item['sellPrice'])}")
        if "traderSells" in item:
            fields.append("traderSells:%s" % ("true" if item["traderSells"] else "false"))
        if "traderBuys" in item:
            fields.append("traderBuys:%s" % ("true" if item["traderBuys"] else "false"))
        lines.append("{" + ",".join(fields) + "}")

    output = header + ",\n".join(lines) + "\n]};\n"
    out_path = ROOT / "chernarus" / "traders" / slug / "catalogue-data.js"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output, encoding="utf-8")


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

        special_name = special_friendly_name(class_name)
        name = special_name or (curated_item["name"] if curated_item else friendly_from_classname(class_name))

        if market["source"] == "Gebs_Fishing_Gear.json":
            category = "Geb's Fishing Gear"
        else:
            category = curated_item["category"] if curated_item else market["category"]

        mode = "buy" if int(stock_value) == 1 else "sell"
        row = {
            "name": name,
            "className": class_name,
            "category": category,
            "mode": mode,
            "price": market["price"],
        }

        if mode == "buy":
            percent = effective_sell_percent(market, zone)
            if percent is not None:
                row["sellPrice"] = round(float(market["price"]) * (percent / 100.0))

        rows.append(row)

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

    if cfg.get("inherited_category_buyback"):
        sell_percent = zone.get("SellPricePercent")
        if sell_percent is not None and float(sell_percent) >= 0:
            header += f",inheritedCategoryBuyback:true,inheritedSellPercent:{float(sell_percent):g}"
        excluded = cfg.get("buyback_excluded_categories") or []
        if excluded:
            encoded = ",".join("'%s'" % js_escape(category) for category in excluded)
            header += f",buybackExcludedCategories:[{encoded}]"

    header += ",items:[\n"

    lines = []
    for item in rows:
        price = item["price"]
        if isinstance(price, float) and price.is_integer():
            price = int(price)
        fields = (
            "{name:'%s',className:'%s',category:'%s',mode:'%s',price:%s"
            % (
                js_escape(item["name"]),
                js_escape(item["className"]),
                js_escape(item["category"]),
                item["mode"],
                price,
            )
        )
        if "sellPrice" in item:
            fields += f",sellPrice:{int(item['sellPrice'])}"
        fields += "}"
        lines.append(fields)

    output = header + ",\n".join(lines) + "\n]};\n"
    out_path = ROOT / "chernarus" / "traders" / slug / "catalogue-data.js"
    out_path.write_text(output, encoding="utf-8")
    print(f"Built {slug}: {len(rows)} live items from {cfg['zone']}")
    if missing:
        print(f"WARNING {slug}: {len(missing)} stock items were not found in Market JSON: {', '.join(missing)}")


def parse_permission(value: int) -> tuple[bool, bool, bool]:
    """Return (trader_sells, trader_buys, visible) for Expansion trader 0/1/2/3."""
    value = int(value)
    if value == 0:
        return True, False, True
    if value == 1:
        return True, True, True
    if value == 2:
        return False, True, True
    if value == 3:
        return False, False, False
    return False, False, False


def build_from_trader_config(slug: str, cfg: dict, market_index: dict[str, list[dict]]) -> None:
    trader = read_json(TRADERS_DIR / cfg["trader"])
    zone = read_json(ZONE_DIR / cfg["zone"])
    market_settings = read_json(MARKET_SETTINGS_FILE) if MARKET_SETTINGS_FILE.exists() else {}
    global_sell_percent = float(market_settings.get("SellPricePercent", 75))
    buy_percent = float(zone.get("BuyPricePercent", 100))

    rows_by_class: dict[str, dict] = {}
    missing_categories = []
    missing_items = []

    for declaration in trader.get("Categories", []):
        if ":" in declaration:
            category_stem, raw_permission = declaration.rsplit(":", 1)
            permission = int(raw_permission)
        else:
            category_stem, permission = declaration, 0

        trader_sells, trader_buys, visible = parse_permission(permission)
        if not visible:
            continue

        category_path = MARKET_DIR / f"{category_stem}.json"
        if not category_path.exists():
            missing_categories.append(category_stem)
            continue

        category_data = read_json(category_path)
        label = (
            category_data.get("DisplayName")
            if cfg.get("use_market_display_names")
            else category_label(category_stem)
        ) or category_label(category_stem)
        for market_item in category_data.get("Items", []):
            parent = market_item.get("ClassName")
            if not parent:
                continue
            class_names = [parent] + list(market_item.get("Variants", []) or [])
            base_price = float(market_item.get("MaxPriceThreshold", market_item.get("MinPriceThreshold", 0)))
            market_meta = {
                "sellPricePercent": market_item.get("SellPricePercent", -1),
            }
            sell_percent = effective_sell_percent(market_meta, zone, global_sell_percent)

            for class_name in class_names:
                row = {
                    "name": friendly_from_classname(class_name),
                    "className": class_name,
                    "category": label,
                    "traderSells": trader_sells,
                    "traderBuys": trader_buys,
                }
                if trader_sells:
                    row["buyPrice"] = round(base_price * (buy_percent / 100.0))
                if trader_buys and sell_percent is not None:
                    row["sellPrice"] = round(base_price * (float(sell_percent) / 100.0))
                rows_by_class[class_name.lower()] = row

    # Explicit Items override category-level permissions for the same classname.
    for class_name, permission in trader.get("Items", {}).items():
        trader_sells, trader_buys, visible = parse_permission(permission)
        key = class_name.lower()
        if not visible:
            rows_by_class.pop(key, None)
            continue

        candidates = market_index.get(key, [])
        if not candidates:
            missing_items.append(class_name)
            continue
        market = candidates[0]
        base_price = float(market["price"])
        sell_percent = effective_sell_percent(market, zone, global_sell_percent)
        source_stem = Path(market["source"]).stem
        row = {
            "name": friendly_from_classname(class_name),
            "className": class_name,
            "category": category_label(source_stem),
            "traderSells": trader_sells,
            "traderBuys": trader_buys,
        }
        if trader_sells:
            row["buyPrice"] = round(base_price * (buy_percent / 100.0))
        if trader_buys and sell_percent is not None:
            row["sellPrice"] = round(base_price * (float(sell_percent) / 100.0))
        rows_by_class[key] = row

    rows = sorted(rows_by_class.values(), key=lambda x: (x["category"].lower(), x["name"].lower(), x["className"].lower()))
    format_js_catalogue(slug, cfg, rows)
    print(f"Built {slug}: {len(rows)} live items from {cfg['trader']} + {cfg['zone']}")
    if missing_categories:
        print("WARNING %s: missing market categories: %s" % (slug, ", ".join(missing_categories)))
    if missing_items:
        print("WARNING %s: explicit trader items not found in Market JSON: %s" % (slug, ", ".join(missing_items)))


def main() -> None:
    if not MARKET_DIR.exists() or not ZONE_DIR.exists():
        raise SystemExit("Live market snapshot is missing. Run sync_gtx_market.py first.")
    market_index = build_market_index()
    for slug, cfg in TRADERS.items():
        build_trader(slug, cfg, market_index)
    for slug, cfg in TRADER_CONFIG_CATALOGUES.items():
        build_from_trader_config(slug, cfg, market_index)


if __name__ == "__main__":
    main()

