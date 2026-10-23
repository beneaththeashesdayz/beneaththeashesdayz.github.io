from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
from datetime import datetime, timezone
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent
OUT_FILE = ROOT / "data" / "live-market" / "p2p-listings.json"

HOST = os.environ["GTX_HOST"]
PORT = int(os.environ.get("GTX_PORT", "22"))
USERNAME = os.environ["GTX_USERNAME"]
PASSWORD = os.environ["GTX_PASSWORD"]

MISSION_REMOTE = os.environ.get(
    "GTX_MISSION_PATH", "mpmissions/dayzOffline.chernarusplus"
)
P2P_SETTINGS_REMOTE = os.environ.get(
    "GTX_P2P_SETTINGS_PATH",
    "mpmissions/dayzOffline.chernarusplus/expansion/settings/P2PMarketSettings.json",
)

# Beneath the Ashes defaults. Live P2PMarketSettings.json replaces these when present.
DEFAULT_MAX_LISTING_TIME = 7 * 24 * 60 * 60
DEFAULT_LISTING_FEE_PERCENT = 10


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


def remote_candidates(server_root: str, configured: str) -> list[str]:
    configured = configured.strip().replace("\\", "/").lstrip("/")
    return [posixpath.join(server_root, configured), configured, "/" + configured]


def resolve_remote_dir(
    sftp: paramiko.SFTPClient, server_root: str, configured: str
) -> str:
    seen: set[str] = set()
    for candidate in remote_candidates(server_root, configured):
        if candidate in seen:
            continue
        seen.add(candidate)
        if is_dir(sftp, candidate):
            return candidate
    raise FileNotFoundError(f"Could not resolve GTX directory '{configured}'.")


def try_resolve_remote_file(
    sftp: paramiko.SFTPClient, server_root: str, configured: str
) -> str | None:
    seen: set[str] = set()
    for candidate in remote_candidates(server_root, configured):
        if candidate in seen:
            continue
        seen.add(candidate)
        if is_file(sftp, candidate):
            return candidate
    return None


def read_json_remote(sftp: paramiko.SFTPClient, path: str) -> dict | list:
    with sftp.open(path, "rb") as fh:
        raw = fh.read()
    return json.loads(raw.decode("utf-8-sig"))


def discover_instance_id(sftp: paramiko.SFTPClient, server_root: str) -> int | None:
    for filename in ("serverDZ.cfg", "serverdz.cfg"):
        path = posixpath.join(server_root, filename)
        if not is_file(sftp, path):
            continue
        try:
            with sftp.open(path, "rb") as fh:
                text = fh.read().decode("utf-8-sig", errors="ignore")
        except OSError:
            continue
        match = re.search(r"\binstanceId\s*=\s*(\d+)", text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def listing_json_mtime(sftp: paramiko.SFTPClient, p2p_dir: str) -> float:
    newest = 0.0
    try:
        entries = sftp.listdir_attr(p2p_dir)
    except OSError:
        return newest

    for entry in entries:
        name = entry.filename
        listing_dir = None
        if name.lower().startswith("traderid_"):
            candidate = posixpath.join(p2p_dir, name, "listings")
            if is_dir(sftp, candidate):
                listing_dir = candidate
        elif re.fullmatch(r"P2PTrader_\d+_Listings", name, flags=re.IGNORECASE):
            candidate = posixpath.join(p2p_dir, name)
            if is_dir(sftp, candidate):
                listing_dir = candidate

        if not listing_dir:
            continue

        try:
            for file_entry in sftp.listdir_attr(listing_dir):
                if file_entry.filename.lower().endswith(".json"):
                    newest = max(newest, float(getattr(file_entry, "st_mtime", 0) or 0))
        except OSError:
            continue

    return newest


def discover_p2p_data_dir(
    sftp: paramiko.SFTPClient, mission_dir: str, instance_id: int | None
) -> tuple[str, str]:
    if instance_id is not None:
        storage_name = f"storage_{instance_id}"
        candidate = posixpath.join(mission_dir, storage_name, "expansion", "p2pmarket")
        if is_dir(sftp, candidate):
            return candidate, storage_name

    candidates: list[tuple[float, str, str]] = []
    try:
        entries = sftp.listdir_attr(mission_dir)
    except OSError as exc:
        raise FileNotFoundError("Could not list the Chernarus mission directory.") from exc

    for entry in entries:
        if not entry.filename.lower().startswith("storage_"):
            continue
        candidate = posixpath.join(
            mission_dir, entry.filename, "expansion", "p2pmarket"
        )
        if not is_dir(sftp, candidate):
            continue
        newest_listing = listing_json_mtime(sftp, candidate)
        candidates.append((newest_listing, entry.filename, candidate))

    if not candidates:
        raise FileNotFoundError(
            "No Expansion P2P market storage folder was found under the Chernarus mission."
        )

    candidates.sort(key=lambda row: (row[0], row[1]), reverse=True)
    _, storage_name, p2p_dir = candidates[0]
    return p2p_dir, storage_name


def friendly_name(class_name: str) -> str:
    explicit = {
        "weaponcleaningkit": "Weapon Cleaning Kit",
        "ammo_40mm_chemgas": "40mm PO-X Grenade",
        "ammo_40mm_explosive": "40mm Explosive Grenade",
    }
    lower = class_name.lower()
    if lower in explicit:
        return explicit[lower]

    text = re.sub(r"[_-]+", " ", class_name)
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    return " ".join(part.capitalize() if part.islower() else part for part in text.split())


def flatten_container_items(items: object) -> list[dict]:
    flattened: list[dict] = []
    if not isinstance(items, list):
        return flattened

    for item in items:
        if not isinstance(item, dict):
            continue
        class_name = str(item.get("m_ClassName") or "").strip()
        if class_name:
            flattened.append(
                {
                    "className": class_name,
                    "name": friendly_name(class_name),
                    "quantity": item.get("m_Quantity"),
                    "attached": bool(item.get("m_IsAttached", False)),
                }
            )
        flattened.extend(flatten_container_items(item.get("m_ContainerItems")))
    return flattened


def iso_from_timestamp(value: int | float | None) -> str | None:
    if not isinstance(value, (int, float)) or value <= 0:
        return None
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def safe_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def trader_id_from_name(name: str) -> int | None:
    match = re.fullmatch(r"traderID_(\d+)", name, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.fullmatch(r"P2PTrader_(\d+)_Listings", name, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def list_listing_dirs(sftp: paramiko.SFTPClient, p2p_dir: str) -> list[tuple[int, str]]:
    listing_dirs: list[tuple[int, str]] = []
    for entry in sftp.listdir_attr(p2p_dir):
        trader_id = trader_id_from_name(entry.filename)
        if trader_id is None:
            continue

        if entry.filename.lower().startswith("traderid_"):
            candidate = posixpath.join(p2p_dir, entry.filename, "listings")
        else:
            candidate = posixpath.join(p2p_dir, entry.filename)

        if is_dir(sftp, candidate):
            listing_dirs.append((trader_id, candidate))

    return sorted(listing_dirs, key=lambda row: row[0])


def sanitize_listing(
    raw: dict,
    trader_id: int,
    filename: str,
    max_listing_time: int,
) -> dict | None:
    # ExpansionP2PMarketListingState.LISTED == 1. SOLD == 2.
    if safe_int(raw.get("m_ListingState"), 0) != 1:
        return None

    class_name = str(raw.get("m_ClassName") or "").strip()
    if not class_name:
        return None

    listing_time = safe_int(raw.get("m_ListingTime"), -1)
    expires = listing_time + max_listing_time if listing_time > 0 else None
    included_items = flatten_container_items(raw.get("m_ContainerItems"))
    stable_key = hashlib.sha256(
        f"{trader_id}:{filename}".encode("utf-8")
    ).hexdigest()[:16]

    return {
        "key": stable_key,
        "traderId": trader_id,
        "name": friendly_name(class_name),
        "className": class_name,
        "skinName": raw.get("m_SkinName") or None,
        "seller": raw.get("m_OwnerName") or "Unknown Survivor",
        "price": safe_int(raw.get("m_Price"), 0),
        "listedAt": iso_from_timestamp(listing_time),
        "expiresAt": iso_from_timestamp(expires),
        "healthLevel": raw.get("m_HealthLevel"),
        "quantity": raw.get("m_Quantity"),
        "quantityType": raw.get("m_QuantityType"),
        "includedItemCount": len(included_items),
        "includedItems": included_items,
    }


def write_output(payload: dict) -> None:
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    synced_at = datetime.now(timezone.utc).isoformat()
    max_listing_time = DEFAULT_MAX_LISTING_TIME
    listing_fee_percent = DEFAULT_LISTING_FEE_PERCENT
    listings: list[dict] = []
    status = "ok"
    note = None
    storage_name = None

    transport = paramiko.Transport((HOST, PORT))
    try:
        transport.connect(username=USERNAME, password=PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            server_root = discover_server_root(sftp)
            mission_dir = resolve_remote_dir(sftp, server_root, MISSION_REMOTE)

            settings_path = try_resolve_remote_file(
                sftp, server_root, P2P_SETTINGS_REMOTE
            )
            if settings_path:
                settings = read_json_remote(sftp, settings_path)
                if isinstance(settings, dict):
                    max_listing_time = safe_int(
                        settings.get("MaxListingTime"), DEFAULT_MAX_LISTING_TIME
                    )
                    listing_fee_percent = safe_int(
                        settings.get("ListingPricePercent"),
                        DEFAULT_LISTING_FEE_PERCENT,
                    )

            instance_id = discover_instance_id(sftp, server_root)
            try:
                p2p_dir, storage_name = discover_p2p_data_dir(
                    sftp, mission_dir, instance_id
                )
            except FileNotFoundError as exc:
                status = "unavailable"
                note = str(exc)
                p2p_dir = None

            if p2p_dir:
                for trader_id, listing_dir in list_listing_dirs(sftp, p2p_dir):
                    try:
                        entries = sorted(
                            sftp.listdir_attr(listing_dir),
                            key=lambda entry: entry.filename.lower(),
                        )
                    except OSError:
                        continue

                    for entry in entries:
                        if not entry.filename.lower().endswith(".json"):
                            continue
                        path = posixpath.join(listing_dir, entry.filename)
                        try:
                            raw = read_json_remote(sftp, path)
                        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                            print(f"Skipping unreadable P2P listing {entry.filename}: {exc}")
                            continue
                        if not isinstance(raw, dict):
                            continue
                        listing = sanitize_listing(
                            raw, trader_id, entry.filename, max_listing_time
                        )
                        if listing:
                            listings.append(listing)
        finally:
            sftp.close()
    finally:
        transport.close()

    if status != "ok" and OUT_FILE.exists():
        try:
            previous = json.loads(OUT_FILE.read_text(encoding="utf-8-sig"))
            previous_listings = previous.get("listings") if isinstance(previous, dict) else None
            if isinstance(previous_listings, list):
                listings = previous_listings
        except (OSError, json.JSONDecodeError):
            pass

    listings.sort(
        key=lambda item: (
            item.get("expiresAt") or "9999",
            item.get("price", 0),
            item.get("name", "").lower(),
        )
    )

    payload = {
        "source": "Beneath the Ashes Chernarus live P2P market",
        "status": status,
        "note": note,
        "syncedAt": synced_at,
        "maxListingTimeSeconds": max_listing_time,
        "listingFeePercent": listing_fee_percent,
        "listingCount": len(listings),
        "listings": listings,
    }
    write_output(payload)
    print(f"P2P market sync complete: {len(listings)} active listing(s), status={status}.")


if __name__ == "__main__":
    main()
