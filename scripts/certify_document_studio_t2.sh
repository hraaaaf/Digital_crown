#!/usr/bin/env bash
set -euo pipefail

# Document Studio T2 — global automated engineering recertification gate.
# This proves repository execution only. It does NOT replace authenticated runtime,
# PDF/browser inspection, financial reconciliation or human clinical/regulatory review.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'T2 FAIL: %s\n' "$1" >&2
  exit 1
}

pass() {
  printf 'T2 PASS: %s\n' "$1"
}

command -v git >/dev/null 2>&1 || fail "git is required"
command -v python >/dev/null 2>&1 || fail "python is required"
command -v node >/dev/null 2>&1 || fail "node is required"
command -v npm >/dev/null 2>&1 || fail "npm is required"

PY_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[[ "$PY_VERSION" == "3.12" ]] || fail "Python 3.12 required to mirror CI; found $PY_VERSION"
[[ "$NODE_MAJOR" == "20" ]] || fail "Node 20 required to mirror CI; found $(node --version)"

if ! git diff --quiet || ! git diff --cached --quiet; then
  fail "worktree must be clean before certification"
fi

HEAD_SHA="$(git rev-parse HEAD)"
printf 'Document Studio T2 candidate head: %s\n' "$HEAD_SHA"

export SECRET_KEY="ci-only-secret-key-minimum-32-characters-long"
export DATABASE_URL="sqlite:///:memory:"
export ENVIRONMENT="development"
export TELEMETRY_ENABLED="false"
export CLOUD_AI_ENABLED="false"

printf '\n[1/7] Positive production-safety gate\n'
python scripts/prod_safety_check.py
pass "development safety configuration accepted"

printf '\n[2/7] Targeted T1/T2 frontend regression\n'
(
  cd frontend
  npm test -- \
    src/features/admin/DocumentStudio/DocumentStudioVocabulary.t2a.test.ts \
    src/features/admin/DocumentStudio/DocumentPreviewFingerprint.t2b.test.ts \
    src/features/admin/DocumentStudio/DocumentStudioProductPolish.t2e.test.ts \
    src/features/admin/DocumentStudio/DocumentStudioShellA11y.test.ts \
    src/features/admin/DocumentStudio/DocumentHubClinicalBoundary.test.ts \
    src/features/admin/DocumentStudio/DocumentTabNavigationPolicy.test.ts \
    src/features/admin/DocumentStudio/PatientWorkspaceBoundary.test.tsx
)
pass "targeted T1/T2 frontend regression"

printf '\n[3/7] Full backend suite\n'
python -m pytest backend/tests -q --maxfail=1
pass "full backend suite"

printf '\n[4/7] Full frontend suite\n'
(
  cd frontend
  npm test
)
pass "full frontend suite"

printf '\n[5/7] Frontend production build\n'
(
  cd frontend
  npm run build
)
pass "frontend build"

printf '\n[6/7] Legacy P3→P7 harness availability\n'
for script in \
  scripts/certify_document_studio_p3_p6.sh \
  scripts/certify_document_studio_p7.sh \
  scripts/certify_document_studio_t1.sh; do
  [[ -f "$script" ]] || fail "missing prerequisite harness: $script"
done
pass "prerequisite harnesses present"

printf '\n[7/7] Negative production-safety gate\n'
if ENVIRONMENT=production \
   SECRET_KEY=changeme \
   DEBUG=true \
   DATABASE_URL='sqlite:///./x.db' \
   python scripts/prod_safety_check.py; then
  fail "production safety guard accepted an intentionally unsafe production config"
else
  pass "production safety guard rejected unsafe config"
fi

printf '\nAUTOMATED DOCUMENT STUDIO T2 ENGINEERING GATES PASSED for %s\n' "$HEAD_SHA"
printf 'REMAINING NON-AUTOMATED / ARCHITECTURAL GATES:\n'
printf '  - T2-A: remove dormant ai route/dead AI generator plumbing and formalize committed P7→P3 transition\n'
printf '  - T2-B: wire preview fingerprint/controller and remove synthetic EN_ATTENTE payment transport\n'
printf '  - T2-C: decompose DocumentHub router/session/preview boundaries with regression proof\n'
printf '  - T2-D: close residual DocumentHub dialog/switch accessibility and browser keyboard checks\n'
printf '  - authenticated patient A→B and dirty navigation matrix\n'
printf '  - real PDF/preview/print checks and 390/430/768/1280 browser matrix\n'
printf '  - financial P3/P4/P5 persisted reconciliation review\n'
printf '  - separate human clinical/pharmacological/regulatory certification where required\n'
printf 'NO production-ready, merge-ready or global certification claim is implied until those gates pass.\n'
