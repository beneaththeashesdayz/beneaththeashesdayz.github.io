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
    parsed = json.loads(raw.decode("utf-8-sig"))
    normalized = (json.dumps(parsed, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return normalized, parsed


def resolve_remote_dir(sftp: paramiko.SFTPClient, configured: str) -> str:
    """Resolve GTX paths whether SFTP starts at server root or a nested home directory."""
    configured = configured.strip().replace("\\", "/")
    candidates = []

    if configured.startswith("/"):
        candidates.append(configured)
    else:
        candidates.extend([configured, "/" + configured])

    home = sftp.normalize(".")
    if home and home != "/":
        candidates.append(posixpath.join(home, configured.lstrip("/")))

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            sftp.listdir_attr(candidate)
            print(f"Resolved {configured} -> {candidate}")
            return candidate
        except (FileNotFoundError, IOError):
            pass

    # GTX panels sometimes show paths relative to a directory above the SFTP login root.
    # Walk a few levels from the login directory and look for the expected first folder.
    first = configured.lstrip("/").split("/", 1)[0]
    remainder = configured.lstrip("/").split("/", 1)[1] if "/" in configured.lstrip("/") else ""
    bases = [home, ".", "/"]
    for base in bases:
        try:
            names = sftp.listdir(base)
        except (FileNotFoundError, IOError):
            continue
        match = next((n for n in names if n.lower() == first.lower()), None)
        if match:
            candidate = posixpath.join(base, match, remainder) if remainder else posixpath.join(base, match)
            try:
                sftp.listdir_attr(candidate)
                print(f"Resolved {configured} -> {candidate}")
                return candidate
            except (FileNotFoundError, IOError):
                pass

    try:
        root_names = sftp.listdir(home)
    except Exception:
        root_names = []
    raise FileNotFoundError(
        f"Could not resolve GTX directory '{configured}'. "
        f"SFTP login directory is '{home}' and contains: {root_names[:40]}"
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
            market_remote = resolve_remote_dir(sftp, MARKET_REMOTE)
            zones_remote = resolve_remote_dir(sftp, ZONES_REMOTE)
            market_items = sync_dir(sftp, market_remote, MARKET_OUT, "market")
            zone_items = sync_dir(sftp, zones_remote, ZONES_OUT, "traderzones")
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
    (OUT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Synced {len(market_items)} market files and {len(zone_items)} trader-zone files.")


if __name__ == "__main__":
    main()
