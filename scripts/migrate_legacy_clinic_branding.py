from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.core.media_paths import get_media_root
from backend.core.paths import AppPaths


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def migrate(source_root: Path, *, dry_run: bool = False) -> tuple[int, int, int]:
    source_root = source_root.expanduser().resolve(strict=False)
    destination_root = (get_media_root() / "clinics").resolve(strict=False)
    if not source_root.exists():
        return 0, 0, 0

    copied = skipped = conflicts = 0
    for source in sorted(source_root.rglob("*")):
        if not source.is_file() or source.is_symlink():
            continue
        relative = source.relative_to(source_root)
        destination = destination_root / relative
        if destination.exists():
            if destination.is_file() and _digest(destination) == _digest(source):
                skipped += 1
                continue
            conflicts += 1
            print(f"CONFLICT {relative}")
            continue

        copied += 1
        print(f"COPY {relative}")
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    return copied, skipped, conflicts


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy cabinet branding into persistent MEDIA_ROOT.")
    parser.add_argument(
        "--source-root",
        type=Path,
        default=AppPaths.get_base_dir() / "backend" / "static" / "uploads" / "clinics",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    copied, skipped, conflicts = migrate(args.source_root, dry_run=args.dry_run)
    print(f"RESULT copied={copied} skipped={skipped} conflicts={conflicts} dry_run={args.dry_run}")
    return 2 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
