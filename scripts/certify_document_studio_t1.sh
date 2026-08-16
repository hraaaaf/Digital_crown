#!/usr/bin/env bash
set -euo pipefail

# T1 Document Studio transversal premium — automated engineering gate.
# This script proves repository checks only. It does not certify authenticated
# runtime behavior, visual rendering, clinical science, finance or production.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'T1 FAIL: %s\n' "$1" >&2
  exit 1
}

pass() {
  printf 'T1 PASS: %s\n' "$1"
}

command -v git >/dev/null 2>&1 || fail "git is required"
command -v node >/dev/null 2>&1 || fail "node is required"
command -v npm >/dev/null 2>&1 || fail "npm is required"

NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[[ "$NODE_MAJOR" == "20" ]] || fail "Node 20 required to mirror CI; found $(node --version)"

if ! git diff --quiet || ! git diff --cached --quiet; then
  fail "worktree must be clean before certification"
fi

HEAD_SHA="$(git rev-parse HEAD)"
printf 'Document Studio T1 candidate head: %s\n' "$HEAD_SHA"

printf '\n[1/3] Targeted T1 transversal regression\n'
(
  cd frontend
  npm test -- \
    src/features/patients/patientDocumentBoundary.test.ts \
    src/features/admin/DocumentStudio/DocumentTabNavigationPolicy.test.ts \
    src/features/admin/DocumentStudio/DocumentHubClinicalBoundary.test.ts \
    src/features/admin/DocumentStudio/DocumentStudioUiTruth.test.ts \
    src/features/admin/DocumentStudio/DocumentStudioShellA11y.test.ts \
    src/features/admin/DocumentStudio/PrescriptionDirtyState.test.ts \
    src/features/admin/DocumentStudio/LibreDirtyState.test.ts \
    src/features/admin/DocumentStudio/P7DirtyState.p7f.test.tsx
)
pass "targeted T1 transversal regression"

printf '\n[2/3] Full frontend suite\n'
(
  cd frontend
  npm test
)
pass "full frontend suite"

printf '\n[3/3] Frontend production build\n'
(
  cd frontend
  npm run build
)
pass "frontend production build"

printf '\nAUTOMATED T1 ENGINEERING GATES PASSED for %s\n' "$HEAD_SHA"
printf 'REMAINING NON-AUTOMATED GATES:\n'
printf '  - authenticated patient A → B non-contamination check, including delayed A response\n'
printf '  - manual + URL-driven dirty navigation checks across P1–P7\n'
printf '  - 390px / 430px / 1280px browser matrix and keyboard/focus smoke check\n'
printf '  - real PDF preview / print interaction checks\n'
printf '  - clinical and financial certification remain independent where applicable\n'
printf 'NO runtime, clinical, financial, merge-ready or production-ready claim is implied until those gates pass.\n'
