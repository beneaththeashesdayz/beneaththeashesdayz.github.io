from __future__ import annotations

import hashlib
import json
import os
import posixpath
from datetime import datetime, timezone
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent
OUT_ROOT = ROOT / "data" / "live-market"
MARKET_OUT = OUT_ROOT / "market"
TRADERS_OUT = OUT_ROOT / "traders"
ZONES_OUT = OUT_ROOT / "traderzones"

HOST = os.environ["GTX_HOST"]
PORT = int(os.environ.get("GTX_PORT", "22"))
USERNAME = os.environ["GTX_USERNAME"]
PASSWORD = os.environ["GTX_PASSWORD"]

MARKET_REMOTE = os.environ.get("GTX_MARKET_PATH", "profiles/ExpansionMod/Market")
TRADERS_REMOTE = os.environ.get("GTX_TRADERS_PATH", "profiles/ExpansionMod/Traders")
ZONES_REMOTE = os.environ.get(
    "GTX_TRADERZONES_PATH",
    "mpmissions/dayzOffline.chernarusplus/expansion/traderzones",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_json(raw: bytes) -> tuple[bytes, dict | list]:
    parsed = json.loads(raw.decode("utf-8-sig"))
    normalized = (json.dumps(parsed, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return normalized, parsed


def is_dir(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.listdir_attr(path)
        return True
    except (FileNotFoundError, IOError):
        return False


def discover_server_root(sftp: paramiko.SFTPClient) -> str:
    """Find the DayZ server folder GTX places beneath the SFTP root."""
    home = sftp.normalize(".") or "/"

    # If the login directory itself already contains the expected server folders, use it.
    for base in [home, "/", "."]:
        if is_dir(sftp, posixpath.join(base, "profiles")) or is_dir(sftp, posixpath.join(base, "mpmissions")):
            print(f"Detected GTX server root: {base}")
            return base

    # GTX commonly exposes one server-instance directory beneath '/'. Search one level down.
    for base in [home, "/"]:
        try:
            names = sftp.listdir(base)
        except (FileNotFoundError, IOError):
            continue

        for name in names:
            candidate = posixpath.join(base, name)
            if is_dir(sftp, posixpath.join(candidate, "profiles")) or is_dir(sftp, posixpath.join(candidate, "mpmissions")):
                print(f"Detected GTX server root: {candidate}")
                return candidate

    try:
        root_names = sftp.listdir(home)
    except Exception:
        root_names = []
    raise FileNotFoundError(
        f"Could not discover GTX DayZ server root. SFTP login directory is '{home}' "
        f"and contains: {root_names[:40]}"
    )


def resolve_remote_dir(sftp: paramiko.SFTPClient, server_root: str, configured: str) -> str:
    configured = configured.strip().replace("\\", "/").lstrip("/")
    candidates = [
        posixpath.join(server_root, configured),
        configured,
        "/" + configured,
    ]

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if is_dir(sftp, candidate):
            print(f"Resolved {configured} -> {candidate}")
            return candidate

    raise FileNotFoundError(
        f"Could not resolve GTX directory '{configured}' beneath detected server root '{server_root}'."
    )


def list_json_files(sftp: paramiko.SFTPClient, remote_dir: str) -> list[str]:
    return sorted(
        [
            posixpath.join(remote_dir, entry.filename)
            for entry in sftp.listdir_attr(remote_dir)
            if entry.filename.lower().endswith(".json")
        ],
        key=str.lower,
    )


def sync_dir(sftp: paramiko.SFTPClient, remote_dir: str, local_dir: Path, group: str) -> list[dict]:
    local_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    manifest_items: list[dict] = []

    for remote_file in list_json_files(sftp, remote_dir):
        filename = posixpath.basename(remote_file)
        seen.add(filename)
        with sftp.open(remote_file, "rb") as fh:
            raw = fh.read()

        normalized, parsed = normalize_json(raw)
        (local_dir / filename).write_bytes(normalized)

        manifest_items.append({
            "group": group,
            "filename": filename,
            "sha256": sha256_bytes(normalized),
            "topLevelType": "object" if isinstance(parsed, dict) else "array" if isinstance(parsed, list) else type(parsed).__name__,
            "entryCount": len(parsed) if isinstance(parsed, (dict, list)) else None,
        })

    for local_file in local_dir.glob("*.json"):
        if local_file.name not in seen:
            local_file.unlink()

    return manifest_items


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    transport = paramiko.Transport((HOST, PORT))
    try:
        transport.connect(username=USERNAME, password=PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            print(f"SFTP login directory: {sftp.normalize('.')}")
            server_root = discover_server_root(sftp)
            market_remote = resolve_remote_dir(sftp, server_root, MARKET_REMOTE)
            traders_remote = resolve_remote_dir(sftp, server_root, TRADERS_REMOTE)
            zones_remote = resolve_remote_dir(sftp, server_root, ZONES_REMOTE)
            market_items = sync_dir(sftp, market_remote, MARKET_OUT, "market")
            trader_items = sync_dir(sftp, traders_remote, TRADERS_OUT, "traders")
            zone_items = sync_dir(sftp, zones_remote, ZONES_OUT, "traderzones")
        finally:
            sftp.close()
    finally:
        transport.close()

    manifest = {
        "source": "GTX Gaming DayZ Chernarus live server",
        "syncedAt": datetime.now(timezone.utc).isoformat(),
        "marketPath": MARKET_REMOTE,
        "tradersPath": TRADERS_REMOTE,
        "traderZonesPath": ZONES_REMOTE,
        "marketFileCount": len(market_items),
        "traderFileCount": len(trader_items),
        "traderZoneFileCount": len(zone_items),
        "files": market_items + trader_items + zone_items,
    }
    (OUT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Synced {len(market_items)} market files, {len(trader_items)} trader files "
        f"and {len(zone_items)} trader-zone files."
    )


if __name__ == "__main__":
    main()
