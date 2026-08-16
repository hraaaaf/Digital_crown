#!/usr/bin/env bash
set -euo pipefail

# P7 Compagnon Diagnostique — automated engineering gate.
# This script proves only executable repository checks. It does not certify
# diagnostic science, clinical appropriateness, authenticated runtime or visuals.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'P7 FAIL: %s\n' "$1" >&2
  exit 1
}

pass() {
  printf 'P7 PASS: %s\n' "$1"
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
printf 'Document Studio P7 candidate head: %s\n' "$HEAD_SHA"

printf '\n[1/3] Targeted P7 regression\n'
(
  cd frontend
  npm test -- \
    src/features/admin/DocumentStudio/DiagnosticEngine.p5p0.test.ts \
    src/features/admin/DocumentStudio/TreatmentPlanStudio.p7a.test.tsx \
    src/features/admin/DocumentStudio/TreatmentPlanStudio.p7d.test.tsx \
    src/features/admin/DocumentStudio/P7DirtyState.p7f.test.tsx \
    src/features/admin/DocumentStudio/TreatmentPlanStudio.p7g.test.tsx \
    src/features/admin/DocumentStudio/AccountingPlanConversionPolicy.test.ts
)
pass "targeted P7 regression"

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
pass "frontend build"

printf '\nAUTOMATED P7 ENGINEERING GATES PASSED for %s\n' "$HEAD_SHA"
printf 'REMAINING NON-AUTOMATED / ARCHITECTURAL GATES:\n'
printf '  - P7-C: structured clinical context, including authoritative allergy data model\n'
printf '  - P7-E: persisted proposal provenance, rule-set/version/evidence and practitioner confirmation\n'
printf '  - authenticated patient A → B runtime non-contamination check\n'
printf '  - real 390px / 768px / desktop browser and keyboard verification\n'
printf '  - P7-H scientific/clinical human validation of diagnostic and therapeutic rules\n'
printf 'NO clinical, scientific, merge-ready or production-ready claim is implied until those gates pass.\n'
