from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _target(*, os_name: str, arch: str, artifact: Path, url: str) -> dict[str, Any]:
    path = artifact.expanduser().resolve()
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValueError(f"artifact missing or empty: {artifact}")
    clean_url = str(url or "").strip()
    if not clean_url.startswith("https://"):
        raise ValueError(f"HTTPS target required for {os_name}")
    return {
        "os": os_name,
        "arch": arch,
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
        "url": clean_url,
    }


def build_payload(
    *,
    sequence: int,
    version: str,
    windows_artifact: Path,
    windows_url: str,
    macos_artifact: Path,
    macos_url: str,
    issued_at: datetime | None = None,
    expires_hours: int = 8,
) -> dict[str, Any]:
    if sequence <= 0:
        raise ValueError("sequence must be > 0")
    if not VERSION_PATTERN.fullmatch(str(version or "").strip()):
        raise ValueError("version must be MAJOR.MINOR.PATCH")
    if not (1 <= int(expires_hours) <= 24):
        raise ValueError("expires_hours must be between 1 and 24")

    issued = (issued_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expires = issued + timedelta(hours=int(expires_hours))
    return {
        "schema": 1,
        "sequence": int(sequence),
        "version": str(version).strip(),
        "issued_at": _utc_text(issued),
        "expires_at": _utc_text(expires),
        "targets": [
            _target(
                os_name="windows",
                arch="amd64",
                artifact=windows_artifact,
                url=windows_url,
            ),
            _target(
                os_name="macos",
                arch="arm64",
                artifact=macos_artifact,
                url=macos_url,
            ),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the unsigned canonical payload for a Digital Crown P10/P13 update manifest."
    )
    parser.add_argument("--sequence", required=True, type=int)
    parser.add_argument("--version", required=True)
    parser.add_argument("--windows-artifact", required=True, type=Path)
    parser.add_argument("--windows-url", required=True)
    parser.add_argument("--macos-artifact", required=True, type=Path)
    parser.add_argument("--macos-url", required=True)
    parser.add_argument("--expires-hours", type=int, default=8)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    payload = build_payload(
        sequence=args.sequence,
        version=args.version,
        windows_artifact=args.windows_artifact,
        windows_url=args.windows_url,
        macos_artifact=args.macos_artifact,
        macos_url=args.macos_url,
        expires_hours=args.expires_hours,
    )
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        "P10_UPDATE_MANIFEST_PAYLOAD=READY "
        f"sequence={payload['sequence']} version={payload['version']} output={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
