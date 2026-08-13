from __future__ import annotations

import json
import os
import posixpath
import re
from datetime import datetime, timezone
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent
OUT_FILE = ROOT / "data" / "live-market" / "sparky.json"

HOST = os.environ["GTX_HOST"]
PORT = int(os.environ.get("GTX_PORT", "22"))
USERNAME = os.environ["GTX_USERNAME"]
PASSWORD = os.environ["GTX_PASSWORD"]

LBMASTER_ROOT = os.environ.get("GTX_LBMASTER_PATH", "profiles/LBmaster")


def is_dir(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.listdir_attr(path)
        return True
    except (FileNotFoundError, IOError):
        return False


def is_file(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.stat(path)
        return True
    except (FileNotFoundError, IOError):
        return False


def discover_server_root(sftp: paramiko.SFTPClient) -> str:
    home = sftp.normalize(".") or "/"
    for base in [home, "/", "."]:
        if is_dir(sftp, posixpath.join(base, "profiles")) or is_dir(
            sftp, posixpath.join(base, "mpmissions")
        ):
            return base

    for base in [home, "/"]:
        try:
            names = sftp.listdir(base)
        except (FileNotFoundError, IOError):
            continue
        for name in names:
            candidate = posixpath.join(base, name)
            if is_dir(sftp, posixpath.join(candidate, "profiles")) or is_dir(
                sftp, posixpath.join(candidate, "mpmissions")
            ):
                return candidate

    raise FileNotFoundError("Could not discover the GTX DayZ server root.")


def resolve_case_insensitive(sftp: paramiko.SFTPClient, base: str, parts: list[str]) -> str:
    current = base
    for wanted in parts:
        try:
            names = sftp.listdir(current)
        except (FileNotFoundError, IOError) as exc:
            raise FileNotFoundError(f"Could not list '{current}' while resolving '{wanted}'.") from exc
        match = next((name for name in names if name.lower() == wanted.lower()), None)
        if not match:
            raise FileNotFoundError(f"Could not find '{wanted}' beneath '{current}'.")
        current = posixpath.join(current, match)
    return current


def resolve_relative(sftp: paramiko.SFTPClient, server_root: str, relative: str) -> str:
    parts = [part for part in relative.replace("\\", "/").split("/") if part]
    return resolve_case_insensitive(sftp, server_root, parts)


def read_json(sftp: paramiko.SFTPClient, path: str):
    with sftp.open(path, "rb") as fh:
        raw = fh.read()
    return json.loads(raw.decode("utf-8-sig"))


def get_any(data: dict, *names: str, default=None):
    if not isinstance(data, dict):
        return default
    by_lower = {str(key).lower(): value for key, value in data.items()}
    for name in names:
        if name in data:
            return data[name]
        if name.lower() in by_lower:
            return by_lower[name.lower()]
    return default


def clean_name(value: str) -> str:
    if not value:
        return "Unknown Vehicle"
    value = value.replace("\\", "/").rstrip("/")
    if "/" in value:
        value = value.rsplit("/", 1)[-1]
    value = re.sub(r"(?i)_base$", "", value)
    value = re.sub(r"[_-]+", " ", value)
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    words = value.split()
    special = {
        "atv": "ATV",
        "bmw": "BMW",
        "m3s": "M3S",
        "mcx": "MCX",
        "suv": "SUV",
        "vw": "VW",
        "uaz": "UAZ",
        "hmmwv": "HMMWV",
        "humvee": "Humvee",
    }
    return " ".join(special.get(word.lower(), word.capitalize()) for word in words)


def sanitize_levels(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    result = []
    for row in value:
        if not isinstance(row, dict):
            continue
        result.append({
            "level": get_any(row, "level"),
            "cost": get_any(row, "cost"),
            "slots": get_any(row, "slots"),
        })
    return result


def sanitize_group(group: dict) -> dict:
    fields = [
        "name",
        "costWithdraw",
        "costDeposit",
        "createNewKeyWhenWithdrawing",
        "spawnVehicleLocked",
        "requireKeyToDeposit",
        "requireVehicleLockedToStore",
        "requireKeyToWithdraw",
        "deleteKeyWhenDepositing",
        "forceKeyAssignedToParkIn",
        "saveInventory",
        "canBuyVehiclesAtAdminPlaced",
        "canBuyVehiclesAtPlayerPlaced",
        "canSellVehiclesAtPlayerPlaced",
        "canSellVehiclesAtAdminPlaced",
        "addKeyToBoughtVehicle",
        "canRepaintVehicles",
        "canRepairVehicle",
        "baseVehicleRepairCost",
        "singleAttachmentRepairCost",
        "canRepairVehicleAttachments",
        "canRepairRuinedAttachments",
        "canRefuelVehicle",
        "fuelCostPerLiter",
        "waterCoolantCostPerLiter",
        "vehicleWhitelist",
    ]
    result = {field: get_any(group, field) for field in fields}
    result["levels"] = sanitize_levels(get_any(group, "levels", default=[]))
    return result


def sanitize_traders(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    result = []
    for row in value:
        if not isinstance(row, dict):
            continue
        result.append({
            "traderItemClassname": get_any(row, "traderItemClassname"),
            "personalTraderGroupname": get_any(row, "personalTraderGroupname"),
            "groupTraderGroupname": get_any(row, "groupTraderGroupname"),
            "blackboxPreview": get_any(row, "blackboxPreview"),
        })
    return result


def sanitize_attachment_items(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    result = []
    for row in value:
        if isinstance(row, str):
            result.append({"itemname": row})
        elif isinstance(row, dict):
            itemname = get_any(row, "itemname", "itemName", "classname", "className")
            result.append({
                "itemname": itemname,
                "colorGroup": get_any(row, "colorGroup"),
            })
    return result


def sanitize_vehicle(row: dict) -> dict:
    itemname = str(get_any(row, "itemname", default="") or "")
    group_name = str(get_any(row, "groupName", default="") or "")
    display_source = group_name if group_name else itemname
    return {
        "name": clean_name(display_source),
        "itemname": itemname,
        "groupName": group_name,
        "buyCost": get_any(row, "buyCost"),
        "sellPrice": get_any(row, "sellPrice"),
        "repaintCost": get_any(row, "repaintCost"),
        "insuranceCost": get_any(row, "insuranceCost"),
        "color": get_any(row, "color"),
        "additionalCargoItems": get_any(row, "additionalCargoItems", default=[]),
        "attachmentItems": sanitize_attachment_items(get_any(row, "attachmentItems", default=[])),
    }


def sanitize_impound(data: dict) -> dict:
    fields = [
        "defaultImpoundAfterTime",
        "minPlayerDistanceForImpound",
        "impoundVehiclesProtectedByFlagpole",
        "impoundRuinedVehicles",
        "ruinedVehiclesRequireVehicleInsurance",
        "bringBackIntoOriginalGarage",
        "impoundGarageGroup",
        "rebuyCostBuyFraction",
        "rebuyCostBase",
        "impoundTimePenalty",
        "ruinedVehicleRebuyCostFraction",
        "ruinedRebuyCostBase",
        "impoundTimePenaltyRuined",
        "costForExceedingMaxSlots",
    ]
    return {field: get_any(data, field) for field in fields}


def main() -> None:
    transport = paramiko.Transport((HOST, PORT))
    try:
        transport.connect(username=USERNAME, password=PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            server_root = discover_server_root(sftp)
            lb_root = resolve_relative(sftp, server_root, LBMASTER_ROOT)
            config_root = resolve_case_insensitive(sftp, lb_root, ["Config"])
            garage_root = resolve_case_insensitive(sftp, config_root, ["LBGarage"])
            common_root = resolve_case_insensitive(sftp, config_root, ["Common"])

            garage_config_path = resolve_case_insensitive(sftp, garage_root, ["config.json"])
            vehicles_path = resolve_case_insensitive(sftp, garage_root, ["vehicles.json"])
            impound_path = resolve_case_insensitive(sftp, garage_root, ["impoundConfig.json"])
            currencies_path = resolve_case_insensitive(sftp, common_root, ["Currencies.json"])

            garage = read_json(sftp, garage_config_path)
            vehicles_raw = read_json(sftp, vehicles_path)
            impound_raw = read_json(sftp, impound_path)
            currencies = read_json(sftp, currencies_path)
        finally:
            sftp.close()
    finally:
        transport.close()

    groups_raw = get_any(garage, "garageGroups", default=[])
    groups = [sanitize_group(row) for row in groups_raw if isinstance(row, dict)] if isinstance(groups_raw, list) else []
    traders = sanitize_traders(get_any(garage, "traders", default=[]))

    vehicle_rows = get_any(vehicles_raw, "vehicles", default=[])
    vehicles = [sanitize_vehicle(row) for row in vehicle_rows if isinstance(row, dict)] if isinstance(vehicle_rows, list) else []

    payload = {
        "source": "Beneath the Ashes Chernarus live LB Master garage",
        "status": "ok",
        "syncedAt": datetime.now(timezone.utc).isoformat(),
        "currency": {
            "prefix": get_any(currencies, "currencyPrefix", default="$"),
            "suffix": get_any(currencies, "currencySuffix", default=""),
            "thousandsSeparator": get_any(currencies, "thousandsSeparator", default=","),
        },
        "cargoItemsWhenBuyingVehicle": get_any(vehicles_raw, "cargoItemsWhenBuyingVehicle", default=[]),
        "garageGroups": groups,
        "traders": traders,
        "impound": sanitize_impound(impound_raw),
        "vehicleCount": len(vehicles),
        "vehicles": vehicles,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Synced {len(vehicles)} LB Master Sparky vehicle entries across {len(groups)} garage groups.")


if __name__ == "__main__":
    main()
