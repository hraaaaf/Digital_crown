from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SPEC_SNIPPETS = [
    "_required('frontend/dist')",
    "_required('backend/templates')",
    "_required('backend/static/assets')",
    "_required('backend/data')",
    "_required('backend/scientific_assets.json')",
    "panoramic_model.onnx",
    "ceph_weights.pth",
    "windows-version-info.txt",
]
FORBIDDEN_SPEC = ['.env', 'firebase_creds.json', "('backend/static', 'backend/static')"]


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def static_contract(root: Path) -> None:
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    require(re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version) is not None, 'invalid VERSION')
    spec = (root / 'DigitalCrown.spec').read_text(encoding='utf-8')
    for snippet in REQUIRED_SPEC_SNIPPETS:
        require(snippet in spec, f'missing spec contract: {snippet}')
    for snippet in FORBIDDEN_SPEC:
        require(snippet not in spec, f'forbidden spec content: {snippet}')
    legacy = (root / 'scripts' / 'build_exe.py').read_text(encoding='utf-8')
    require('LEGACY_BUILDER_DISABLED' in legacy, 'legacy builder is not quarantined')
    iss = (root / 'installer' / 'DigitalCrown.iss').read_text(encoding='utf-8')
    require('AppVersion={#MyAppVersion}' in iss, 'Inno version is not parameterized')
    require('PrivilegesRequired=lowest' in iss, 'installer must remain per-user')
    require('%APPDATA%' in iss or 'APPDATA' in iss, 'installer must document data preservation')
    manifest = json.loads((root / 'backend' / 'scientific_assets.json').read_text(encoding='utf-8'))
    ids = {a['id']: a for a in manifest['assets']}
    require(ids['cephalo_sota']['lifecycle'] == 'deferred', 'SOTA must stay deferred in P6')
    require(ids['cephalo_legacy']['lifecycle'] == 'external', 'legacy cephalo must stay external')
    require(ids['panoramic']['lifecycle'] == 'external', 'panoramic must stay external')
    print(f'P6_PACKAGING_CONTRACT=SUCCESS version={version}')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--static', action='store_true')
    ap.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()
    static_contract(args.root)

if __name__ == '__main__':
    main()
