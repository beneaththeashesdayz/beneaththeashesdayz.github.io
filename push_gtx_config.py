from __future__ import annotations

import argparse
import json
import os
import posixpath
from datetime import datetime, timezone
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent
HOST = os.environ["GTX_HOST"]
PORT = int(os.environ.get("GTX_PORT", "22"))
USERNAME = os.environ["GTX_USERNAME"]
PASSWORD = os.environ["GTX_PASSWORD"]

# Repository-relative file -> GTX server-relative destination.
# Keep this deliberately narrow. Add new paths only when we intentionally want
# GitHub to be able to write that config back to the live server.
ALLOWLIST = {
    "data/live-market/traders/Clothing.json": "profiles/ExpansionMod/Traders/Clothing.json",
    "data/live-market/traders/Attachments.json": "profiles/ExpansionMod/Traders/Attachments.json",
}


def is_dir(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.listdir_attr(path)
        return True
    except (FileNotFoundError, IOError):
        return False


def discover_server_root(sftp: paramiko.SFTPClient) -> str:
    home = sftp.normalize(".") or "/"
    for base in [home, "/", "."]:
        if is_dir(sftp, posixpath.join(base, "profiles")) or is_dir(sftp, posixpath.join(base, "mpmissions")):
            return base
    for base in [home, "/"]:
        try:
            names = sftp.listdir(base)
        except (FileNotFoundError, IOError):
            continue
        for name in names:
            candidate = posixpath.join(base, name)
            if is_dir(sftp, posixpath.join(candidate, "profiles")) or is_dir(sftp, posixpath.join(candidate, "mpmissions")):
                return candidate
    raise FileNotFoundError("Could not discover GTX DayZ server root.")


def validate_json(path: Path) -> bytes:
    raw = path.read_bytes()
    parsed = json.loads(raw.decode("utf-8-sig"))
    return (json.dumps(parsed, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Push one approved config from GitHub to GTX over SFTP.")
    parser.add_argument("repo_path", choices=sorted(ALLOWLIST))
    args = parser.parse_args()

    repo_path = args.repo_path
    local_path = ROOT / repo_path
    if not local_path.is_file():
        raise FileNotFoundError(f"Missing local config: {repo_path}")

    payload = validate_json(local_path)
    remote_relative = ALLOWLIST[repo_path]

    transport = paramiko.Transport((HOST, PORT))
    try:
        transport.connect(username=USERNAME, password=PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            server_root = discover_server_root(sftp)
            remote_path = posixpath.join(server_root, remote_relative)
            remote_dir = posixpath.dirname(remote_path)
            if not is_dir(sftp, remote_dir):
                raise FileNotFoundError(f"GTX destination directory does not exist: {remote_dir}")

            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_path = f"{remote_path}.bak-{stamp}"

            # Back up the current live file before replacing it.
            try:
                with sftp.open(remote_path, "rb") as src, sftp.open(backup_path, "wb") as dst:
                    dst.write(src.read())
                print(f"Backup created: {backup_path}")
            except FileNotFoundError:
                print("No existing live file found; skipping backup.")

            with sftp.open(remote_path, "wb") as dst:
                dst.write(payload)
            print(f"Uploaded {repo_path} -> {remote_path}")
        finally:
            sftp.close()
    finally:
        transport.close()


if __name__ == "__main__":
    main()
