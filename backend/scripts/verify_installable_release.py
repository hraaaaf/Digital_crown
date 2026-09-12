from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.release_certification import (
    ReleaseCertificationError,
    verify_installable_release_directory,
)
from backend.runtime_asset_certification import RuntimeAssetCertificationError


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a Digital Crown INSTALLABLE_CERTIFIED release")
    parser.add_argument("--release-dir", required=True, type=Path)
    parser.add_argument("--expected-pack", choices=["BASIC", "GOLD", "ELITE"])
    args = parser.parse_args()

    try:
        payload = verify_installable_release_directory(
            args.release_dir,
            expected_pack=args.expected_pack,
        )
    except (ReleaseCertificationError, RuntimeAssetCertificationError) as exc:
        print(f"INSTALLABLE_CERTIFICATION=REJECTED: {exc}")
        return 1

    print("INSTALLABLE_CERTIFICATION=OK")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
