from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path, PurePosixPath

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
INNO_RELEASE = "is-6_7_3"
INNO_URL = "https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe"
INNO_SHA256 = "9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732"
FIREBASE_ADMIN_REQUIREMENT = "firebase-admin==7.5.0"

REQUIRED_SPEC_SNIPPETS = [
    "_required('frontend/dist')",
    "_required('backend/templates')",
    "_required('backend/static/assets')",
    "_required('backend/data')",
    "_required('backend/scientific_assets.json')",
    "windows-version-info.txt",
]
FORBIDDEN_SPEC_SNIPPETS = [
    "('backend/static', 'backend/static')",
    "panoramic_model.onnx",
    "ceph_weights.pth",
    "_collect_scientific_runtime",
    "_collect_legacy_cephalo_runtime",
]


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def _string_literals(source: str) -> list[str]:
    tree = ast.parse(source)
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def _looks_like_forbidden_packaged_path(value: str) -> str | None:
    normalized = value.replace('\\', '/').strip()
    if not normalized or '\n' in normalized:
        return None
    name = PurePosixPath(normalized).name.lower()
    if name == '.env' or name.startswith('.env.'):
        return '.env'
    if name == 'firebase_creds.json':
        return 'firebase_creds.json'
    return None


def _validate_requirement_includes(requirements_path: Path) -> None:
    for raw_line in requirements_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        target = None
        if line.startswith('-r '):
            target = line[3:].strip()
        elif line.startswith('--requirement '):
            target = line[len('--requirement '):].strip()
        if target:
            include_path = (requirements_path.parent / target).resolve()
            require(
                include_path.is_file(),
                f'unresolved requirement include from {requirements_path.name}: {target}',
            )


def _validate_runtime_boot_contract(root: Path) -> None:
    requirements = (root / 'backend' / 'requirements.txt').read_text(encoding='utf-8')
    require(
        FIREBASE_ADMIN_REQUIREMENT in requirements.splitlines(),
        f'packaged runtime dependency missing: {FIREBASE_ADMIN_REQUIREMENT}',
    )

    workflow = (root / '.github' / 'workflows' / 'portability-p6-windows-packaging.yml').read_text(encoding='utf-8')
    require('$proc.HasExited' in workflow, 'P6 runtime smoke must fail fast when the frozen process exits')
    require('digitalcrown.log' in workflow, 'P6 runtime diagnostics must retain the frozen startup log')

    run_source = (root / 'run.py').read_text(encoding='utf-8')
    require(
        'logging.getLogger("digitalcrown.launcher").exception("Runtime startup failed")' in run_source,
        'frozen launcher must persist the startup exception before returning exit 1',
    )


def _validate_fail_closed_scientific_packaging(root: Path) -> None:
    workflow = (root / '.github' / 'workflows' / 'portability-p6-windows-packaging.yml').read_text(encoding='utf-8')
    require('P6_ASSET_TOKEN' not in workflow, 'P6 packaging must not depend on an unavailable cross-repo asset token')
    require('P6_ASSET_REPO' not in workflow, 'P6 packaging must not download unqualified scientific assets')
    require('gh release download' not in workflow, 'P6 packaging must not download a scientific release')
    require('provision_p6_scientific_assets.py' not in workflow, 'legacy scientific provisioner must not be in the P6 production path')
    require('python -m pip check' in workflow, 'P6 dependency consistency check missing')

    run_source = (root / 'run.py').read_text(encoding='utf-8')
    require(
        'P6_SCIENTIFIC_CAPABILITIES=FAIL_CLOSED' in run_source,
        'frozen package self-test does not prove fail-closed scientific capability state',
    )


def _validate_inno_toolchain(root: Path) -> None:
    workflow = (root / '.github' / 'workflows' / 'portability-p6-windows-packaging.yml').read_text(encoding='utf-8')
    require('choco install innosetup' not in workflow, 'P6 must not rely on unpinned Chocolatey Inno Setup availability')
    require(INNO_RELEASE in workflow, 'P6 exact Inno Setup release tag missing')
    require(INNO_URL in workflow, 'P6 exact Inno Setup 6.7.3 official URL missing')
    require(INNO_SHA256 in workflow, 'P6 exact Inno Setup 6.7.3 SHA256 missing')
    require('P6_ISCC' in workflow, 'P6 deterministic ISCC path missing')
    require('Get-FileHash' in workflow, 'P6 Inno Setup hash verification missing')
    require('Get-AuthenticodeSignature' in workflow, 'P6 Inno Setup Authenticode verification missing')
    require('ProductVersion' not in workflow, 'P6 must not use unreliable ISCC ProductVersion as release identity')
    require('types: [opened, synchronize]' in workflow, 'P6 PR trigger must avoid duplicate run on PR reopen')


def _validate_authenticode_distribution_gate(root: Path) -> None:
    workflow = (root / '.github' / 'workflows' / 'portability-p6-windows-packaging.yml').read_text(encoding='utf-8')
    required = {
        'P6_PRIVATE_CODESIGN_NOT_CONFIGURED': 'P6 signing must fail closed when credentials are absent',
        'P6_PRIVATE_CODESIGN_PARTIAL_CONFIGURATION': 'P6 signing must fail closed on partial credential configuration',
        'P6_PRIVATE_CODESIGN_CERT_SHA256_MISMATCH': 'P6 signing certificate SHA-256 pin check missing',
        '& $signtool sign /fd SHA256': 'P6 Authenticode SHA-256 signing command missing',
        '/tr http://timestamp.digicert.com /td SHA256': 'P6 RFC3161 SHA-256 timestamp command missing',
        '& $signtool verify /pa /v $setup': 'P6 signtool verification gate missing',
        'P6_PRIVATE_AUTHENTICODE_TIMESTAMP_MISSING': 'P6 timestamp certificate gate missing',
        'P6_PRIVATE_AUTHENTICODE_SIGNER_MISMATCH': 'P6 signer identity gate missing',
        'dc-p6-authenticode-proof.json': 'P6 retained Authenticode JSON proof missing',
        'dc-p6-signtool-verify.txt': 'P6 retained signtool verification log missing',
        'P6_SIGNED_INSTALLER_MUTATED': 'P6 signed-installer immutability gate missing',
    }
    for snippet, message in required.items():
        require(snippet in workflow, message)
    require('P6_AUTHENTICODE=NOT_CONFIGURED' not in workflow, 'P6 signing workflow must not green-pass an unsigned distribution')
    require('"ready=false"' not in workflow, 'P6 signing workflow must not expose a non-failing unsigned ready=false path')


def static_contract(root: Path) -> None:
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    require(re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version) is not None, 'invalid VERSION')
    spec = (root / 'DigitalCrown.spec').read_text(encoding='utf-8')
    for snippet in REQUIRED_SPEC_SNIPPETS:
        require(snippet in spec, f'missing spec contract: {snippet}')
    for snippet in FORBIDDEN_SPEC_SNIPPETS:
        require(snippet not in spec, f'forbidden spec content: {snippet}')
    forbidden_paths = [
        (literal, forbidden)
        for literal in _string_literals(spec)
        if (forbidden := _looks_like_forbidden_packaged_path(literal)) is not None
    ]
    require(not forbidden_paths, f'forbidden packaged path(s): {forbidden_paths}')
    _validate_requirement_includes(root / 'backend' / 'requirements-p6-windows.txt')
    _validate_runtime_boot_contract(root)
    _validate_fail_closed_scientific_packaging(root)
    _validate_inno_toolchain(root)
    _validate_authenticode_distribution_gate(root)

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
    print(f'P6_PACKAGING_CONTRACT=SUCCESS version={version} scientific=FAIL_CLOSED_NO_WEIGHTS inno=6.7.3 authenticode=FAIL_CLOSED')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--static', action='store_true')
    ap.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()
    static_contract(args.root)


if __name__ == '__main__':
    main()
