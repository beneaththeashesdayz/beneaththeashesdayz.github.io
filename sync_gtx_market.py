from __future__ import annotations

import hashlib
import json
import os
import posixpath
import shutil
from datetime import datetime, timezone
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent
OUT_ROOT = ROOT / "data" / "live-market"
MARKET_OUT = OUT_ROOT / "market"
ZONES_OUT = OUT_ROOT / "traderzones"

HOST = os.environ["GTX_HOST"]
PORT = int(os.environ.get("GTX_PORT", "22"))
USERNAME = os.environ["GTX_USERNAME"]
PASSWORD = os.environ["GTX_PASSWORD"]

MARKET_REMOTE = os.environ.get("GTX_MARKET_PATH", "profiles/ExpansionMod/Market")
ZONES_REMOTE = os.environ.get(
    "GTX_TRADERZONES_PATH",
    "mpmissions/dayzOffline.chernarusplus/expansion/traderzones",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_json(raw: bytes) -> tuple[bytes, dict | list]:
    """Parse JSON and return stable, human-readable bytes plus parsed content."""
    parsed = json.loads(raw.decode("utf-8-sig"))
    normalized = (json.dumps(parsed, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return normalized, parsed


def list_json_files(sftp: paramiko.SFTPClient, remote_dir: str) -> list[str]:
    files: list[str] = []
    for entry in sftp.listdir_attr(remote_dir):
        if entry.filename.lower().endswith(".json"):
            files.append(posixpath.join(remote_dir, entry.filename))
    return sorted(files, key=str.lower)


def sync_dir(
    sftp: paramiko.SFTPClient,
    remote_dir: str,
    local_dir: Path,
    group: str,
) -> list[dict]:
    local_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    manifest_items: list[dict] = []

    for remote_file in list_json_files(sftp, remote_dir):
        filename = posixpath.basename(remote_file)
        seen.add(filename)

        with sftp.open(remote_file, "rb") as fh:
            raw = fh.read()

        normalized, parsed = normalize_json(raw)
        local_file = local_dir / filename
        local_file.write_bytes(normalized)

        if isinstance(parsed, dict):
            top_level_type = "object"
            entry_count = len(parsed)
        elif isinstance(parsed, list):
            top_level_type = "array"
            entry_count = len(parsed)
        else:
            top_level_type = type(parsed).__name__
            entry_count = None

        manifest_items.append(
            {
                "group": group,
                "filename": filename,
                "sha256": sha256_bytes(normalized),
                "topLevelType": top_level_type,
                "entryCount": entry_count,
            }
        )

    # Remove files that disappeared from the live server.
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
            market_items = sync_dir(sftp, MARKET_REMOTE, MARKET_OUT, "market")
            zone_items = sync_dir(sftp, ZONES_REMOTE, ZONES_OUT, "traderzones")
        finally:
            sftp.close()
    finally:
        transport.close()

    manifest = {
        "source": "GTX Gaming DayZ Chernarus live server",
        "syncedAt": datetime.now(timezone.utc).isoformat(),
        "marketPath": MARKET_REMOTE,
        "traderZonesPath": ZONES_REMOTE,
        "marketFileCount": len(market_items),
        "traderZoneFileCount": len(zone_items),
        "files": market_items + zone_items,
    }

    (OUT_ROOT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(
        f"Synced {len(market_items)} market files and "
        f"{len(zone_items)} trader-zone files."
    )


if __name__ == "__main__":
    main()
