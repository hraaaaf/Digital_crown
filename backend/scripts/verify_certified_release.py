"""CLI gate for immutable certified cabinet releases."""

from __future__ import annotations

import argparse
import json
import sys

from backend.release_certification import ReleaseCertificationError, verify_release_directory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", required=True)
    parser.add_argument("--expected-pack", choices=("BASIC", "GOLD", "ELITE"))
    args = parser.parse_args()

    try:
        payload = verify_release_directory(args.release_dir, expected_pack=args.expected_pack)
    except ReleaseCertificationError as exc:
        print(f"CERTIFIED_RELEASE_REFUSED: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "status": "CERTIFIED_RELEASE_OK",
                "release_id": payload["release_id"],
                "commit_sha": payload["commit_sha"],
                "certified_packs": payload["certified_packs"],
                "certification_run_id": payload["certification_run_id"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
