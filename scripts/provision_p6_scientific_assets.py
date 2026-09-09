from __future__ import annotations

import argparse
import hashlib
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

ALLOWED_EXACT = {
    PurePosixPath('backend/ai_models/panoramic_model.onnx'),
    PurePosixPath('backend/ai_models/cephld_cca/ceph_weights.pth'),
}
ALLOWED_PREFIX = PurePosixPath('backend/ai_models/cephld_cca')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def normalize(name: str) -> PurePosixPath:
    p = PurePosixPath(name.replace('\\', '/'))
    if p.is_absolute() or '..' in p.parts:
        raise ValueError(f'unsafe archive path: {name}')
    return p


def allowed(p: PurePosixPath) -> bool:
    if p in ALLOWED_EXACT:
        return True
    if len(p.parts) > len(ALLOWED_PREFIX.parts) and p.parts[:len(ALLOWED_PREFIX.parts)] == ALLOWED_PREFIX.parts:
        return p.suffix == '.py' and '__pycache__' not in p.parts and 'model' not in p.parts[len(ALLOWED_PREFIX.parts):]
    return False


def provision(archive: Path, dest_root: Path, expected_sha: str | None) -> None:
    if expected_sha and sha256(archive).lower() != expected_sha.lower():
        raise SystemExit('P6 asset bundle SHA256 mismatch')
    stage = dest_root / '.p6-assets-stage'
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    with zipfile.ZipFile(archive) as zf:
        members = []
        for info in zf.infolist():
            p = normalize(info.filename)
            if not p.parts or info.is_dir():
                continue
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise SystemExit(f'symlink rejected: {info.filename}')
            if not allowed(p):
                raise SystemExit(f'unexpected P6 scientific asset: {info.filename}')
            members.append((info, p))
        present = {p for _, p in members}
        missing = sorted(str(p) for p in ALLOWED_EXACT - present)
        if missing:
            raise SystemExit(f'missing P6 scientific assets: {missing}')
        if not any(p.suffix == '.py' and p.parts[:len(ALLOWED_PREFIX.parts)] == ALLOWED_PREFIX.parts for _, p in members):
            raise SystemExit('missing cephld_cca runtime Python source')
        for info, p in members:
            out = stage.joinpath(*p.parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, out.open('wb') as dst:
                shutil.copyfileobj(src, dst)
    ai_src = stage / 'backend' / 'ai_models'
    ai_dst = dest_root / 'backend' / 'ai_models'
    if ai_dst.exists():
        shutil.rmtree(ai_dst)
    ai_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(ai_src), str(ai_dst))
    shutil.rmtree(stage)
    print(f'P6_ASSET_PROVISION=SUCCESS sha256={sha256(archive)}')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('archive', type=Path)
    ap.add_argument('--dest-root', type=Path, default=Path.cwd())
    ap.add_argument('--sha256', dest='expected_sha')
    args = ap.parse_args()
    provision(args.archive, args.dest_root, args.expected_sha)

if __name__ == '__main__':
    main()
