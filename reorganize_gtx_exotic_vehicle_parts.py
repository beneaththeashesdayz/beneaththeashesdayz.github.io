#!/usr/bin/env python3
"""Split the live exotic vehicle-parts market into one category per model."""

from __future__ import annotations

import argparse
import json
import os
import posixpath
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


SOURCE_CATEGORY = "Car_Parts"
TRADER_FILE = "Exotric_Vehicle_Parts.json"
PRESERVED_CATEGORIES = ["Car_Keys"]

# Prefixes are matched against each parent ClassName in Car_Parts.json. The
# complete Expansion row, including every Variant and all price/stock fields,
# moves together into the model category.
MODEL_GROUPS = [
    ("Exotic_Armada_Bearcat_Parts", "Armada BearCat Parts", ("armada_bearcat_",)),
    ("Exotic_Audi_RS5_Parts", "Audi RS5 Parts", ("star_audi_rs5_",)),
    ("Exotic_BMW_E60_Parts", "BMW E60 Parts", ("e60_", "e60wheel_")),
    ("Exotic_BMW_G81_Parts", "BMW G81 Parts", ("star_bmw_g81_",)),
    ("Exotic_BMW_M3_G80_Parts", "BMW M3 G80 Parts", ("m3_g80_", "m3_g80wheel_")),
    ("Exotic_BMW_M4W_Parts", "BMW M4W Parts", ("m4w_", "m4wwheel_")),
    ("Exotic_BMW_M5_Parts", "BMW M5 Parts", ("m5_", "m5wheel_")),
    ("Exotic_BMW_X5M_Competition_Parts", "BMW X5 M Competition Parts", ("x5mcompetition_",)),
    ("Exotic_Cadillac_Escalade_Parts", "Cadillac Escalade Parts", ("esc_", "escwheel_")),
    ("Exotic_Chevrolet_Camaro_Parts", "Chevrolet Camaro Parts", ("camaro_", "camarowheel_")),
    ("Exotic_Chevrolet_Chevelle_1970_Parts", "Chevrolet Chevelle 1970 Parts", ("chevelle1970_", "chevelle1970wheel_")),
    ("Exotic_Chevrolet_Z71_Parts", "Chevrolet Z71 Parts", ("star_chevrolet_z71_",)),
    ("Exotic_Dodge_Charger_Parts", "Dodge Charger Parts", ("dodgecharger_",)),
    ("Exotic_Dodge_Widebody_Hellcat_Parts", "Dodge Widebody Hellcat Parts", ("widebody_hellcat_", "widebody_hellcatwheel_")),
    ("Exotic_Hennessey_F150D_Parts", "Hennessey F150D Parts", ("hennesseyf150d_", "hennesseyf150dwheel_")),
    ("Exotic_Hummer_H1_Parts", "Hummer H1 Parts", ("star_hummer_h1_",)),
    ("Exotic_Jeep_Rubicon_Parts", "Jeep Rubicon Parts", ("star_jeep_rubi_extra_",)),
    ("Exotic_Land_Rover_Defender_Parts", "Land Rover Defender Parts", ("star_rover_defender_",)),
    ("Exotic_Mercedes_GT63_Parts", "Mercedes GT63 Parts", ("gt63_", "gt63wheel_")),
    ("Exotic_MK5_Parts", "MK5 Parts", ("mk5_", "mk5wheel_")),
    ("Exotic_Toyota_86_Parts", "Toyota 86 Parts", ("toyota_86_",)),
    ("Exotic_Toyota_Tundra_Parts", "Toyota Tundra Parts", ("tundra_", "tundrawheel_")),
]


def json_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def parse_json(raw: bytes, label: str) -> dict:
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        raise RuntimeError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must contain a JSON object.")
    return payload


def build_categories(source: dict) -> tuple[dict[str, dict], dict[str, int]]:
    rows = source.get("Items")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Car_Parts.json has no Items array to reorganize.")

    grouped_rows = {stem: [] for stem, _, _ in MODEL_GROUPS}
    unknown = []
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("Car_Parts.json contains a non-object item row.")
        class_name = str(row.get("ClassName") or "").strip()
        matches = [stem for stem, _, prefixes in MODEL_GROUPS if class_name.lower().startswith(prefixes)]
        if len(matches) != 1:
            unknown.append(class_name or "<missing ClassName>")
            continue
        grouped_rows[matches[0]].append(deepcopy(row))

    if unknown:
        raise RuntimeError("Unmapped or ambiguous Car_Parts parent rows: " + ", ".join(unknown))

    categories = {}
    counts = {}
    seen_classes = set()
    for stem, display_name, _ in MODEL_GROUPS:
        model_rows = grouped_rows[stem]
        if not model_rows:
            raise RuntimeError(f"No rows were assigned to {stem}.")
        payload = deepcopy(source)
        payload["DisplayName"] = display_name
        payload["Items"] = model_rows
        categories[stem] = payload

        class_count = 0
        for row in model_rows:
            classes = [row["ClassName"], *(row.get("Variants") or [])]
            for class_name in classes:
                key = str(class_name).casefold()
                if key in seen_classes:
                    raise RuntimeError(f"Duplicate class across generated categories: {class_name}")
                seen_classes.add(key)
                class_count += 1
        counts[stem] = class_count

    original_classes = sum(1 + len(row.get("Variants") or []) for row in rows)
    if sum(counts.values()) != original_classes:
        raise RuntimeError("Generated class total does not match Car_Parts.json.")
    return categories, counts


def build_trader(trader: dict) -> dict:
    current = trader.get("Categories")
    expected = [stem for stem, _, _ in MODEL_GROUPS] + PRESERVED_CATEGORIES
    if current == expected:
        return deepcopy(trader)
    if current != [SOURCE_CATEGORY, *PRESERVED_CATEGORIES]:
        raise RuntimeError(
            "Exotic parts trader categories changed since the audit; refusing to overwrite: "
            + repr(current)
        )
    updated = deepcopy(trader)
    updated["Categories"] = expected
    return updated


def check_snapshot(source_path: Path, trader_path: Path) -> None:
    source = parse_json(source_path.read_bytes(), str(source_path))
    trader = parse_json(trader_path.read_bytes(), str(trader_path))
    categories, counts = build_categories(source)
    updated_trader = build_trader(trader)
    summary = {
        "modelCategories": len(categories),
        "parentRows": sum(len(payload["Items"]) for payload in categories.values()),
        "itemClasses": sum(counts.values()),
        "traderCategories": updated_trader["Categories"],
        "counts": counts,
    }
    print(json.dumps(summary, indent=2))


def read_remote(sftp, path: str) -> bytes:
    with sftp.open(path, "rb") as handle:
        return handle.read()


def mkdir_p(sftp, path: str) -> None:
    current = ""
    for part in path.strip("/").split("/"):
        current = posixpath.join(current, part)
        try:
            sftp.stat(current)
        except OSError:
            sftp.mkdir(current)


def atomic_write(sftp, path: str, raw: bytes, token: str) -> None:
    temp_path = f"{path}.codex-tmp-{token}"
    with sftp.open(temp_path, "wb") as handle:
        handle.write(raw)
        handle.flush()
    try:
        sftp.posix_rename(temp_path, path)
    except Exception:
        with sftp.open(path, "wb") as handle:
            handle.write(raw)
            handle.flush()
        try:
            sftp.remove(temp_path)
        except OSError:
            pass


def apply_live() -> None:
    import paramiko

    host = os.environ["GTX_HOST"]
    port = int(os.environ.get("GTX_PORT", "22"))
    username = os.environ["GTX_USERNAME"]
    password = os.environ["GTX_PASSWORD"]
    market_root = os.environ.get("GTX_MARKET_PATH", "profiles/ExpansionMod/Market").rstrip("/")
    traders_root = os.environ.get("GTX_TRADERS_PATH", "profiles/ExpansionMod/Traders").rstrip("/")
    backup_root = os.environ.get("GTX_BACKUP_PATH", "profiles/CodexBackups").rstrip("/")
    source_path = posixpath.join(market_root, f"{SOURCE_CATEGORY}.json")
    trader_path = posixpath.join(traders_root, TRADER_FILE)
    token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    transport = paramiko.Transport((host, port))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        source_raw = read_remote(sftp, source_path)
        trader_raw = read_remote(sftp, trader_path)
        source = parse_json(source_raw, source_path)
        trader = parse_json(trader_raw, trader_path)
        categories, counts = build_categories(source)
        updated_trader = build_trader(trader)
        expected = updated_trader["Categories"]

        if trader.get("Categories") == expected:
            for stem, payload in categories.items():
                remote = parse_json(read_remote(sftp, posixpath.join(market_root, f"{stem}.json")), stem)
                if remote != payload:
                    raise RuntimeError(f"Existing {stem}.json does not match the generated category.")
            print(f"Live exotic parts trader is already organized into {len(categories)} model categories.")
            return

        backup_dir = posixpath.join(backup_root, f"exotic-parts-{token}")
        mkdir_p(sftp, backup_dir)
        with sftp.open(posixpath.join(backup_dir, f"{SOURCE_CATEGORY}.json"), "wb") as handle:
            handle.write(source_raw)
        with sftp.open(posixpath.join(backup_dir, TRADER_FILE), "wb") as handle:
            handle.write(trader_raw)

        for stem, payload in categories.items():
            target = posixpath.join(market_root, f"{stem}.json")
            try:
                existing = parse_json(read_remote(sftp, target), target)
            except OSError:
                existing = None
            if existing is not None and existing != payload:
                raise RuntimeError(f"Refusing to overwrite unrelated existing category: {target}")
            atomic_write(sftp, target, json_bytes(payload), token)

        # Switch the trader only after every new category has been written.
        atomic_write(sftp, trader_path, json_bytes(updated_trader), token)

        verified_trader = parse_json(read_remote(sftp, trader_path), trader_path)
        if verified_trader.get("Categories") != expected:
            raise RuntimeError("Trader verification failed after upload.")
        for stem, payload in categories.items():
            verified = parse_json(read_remote(sftp, posixpath.join(market_root, f"{stem}.json")), stem)
            if verified != payload:
                raise RuntimeError(f"Verification failed for {stem}.json")

        print(f"BACKUP_PATH={backup_dir}")
        print(
            f"Organized {sum(len(payload['Items']) for payload in categories.values())} parent rows "
            f"and {sum(counts.values())} item classes into {len(categories)} live model categories."
        )
    finally:
        sftp.close()
        transport.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-snapshot", nargs=2, metavar=("CAR_PARTS_JSON", "TRADER_JSON"))
    args = parser.parse_args()
    if args.check_snapshot:
        check_snapshot(Path(args.check_snapshot[0]), Path(args.check_snapshot[1]))
    else:
        apply_live()


if __name__ == "__main__":
    main()

