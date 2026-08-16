#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'DOCUMENT_STUDIO_CERTIFICATION_FAIL: %s\n' "$1" >&2
  exit 1
}

printf '== Document Studio automated certification ==\n'
printf 'This harness does NOT certify clinical judgment, cabinet PDF appearance, or browser/runtime interaction.\n\n'

[[ -x scripts/certify_p3_devis.sh || -f scripts/certify_p3_devis.sh ]] \
  || fail "scripts/certify_p3_devis.sh is missing"

# Reuse the established full-repository gate: exact toolchain checks, clean worktree,
# targeted P3 contracts, full backend suite, frontend tests/build and prod safety.
bash scripts/certify_p3_devis.sh

printf '\n== T1/T2 backend boundaries ==\n'
python -m pytest -q \
  backend/tests/test_document_installment_contract.py \
  backend/tests/test_document_request_installment_boundary.py

printf '\n== Source invariants ==\n'
DOC_STUDIO_PATHS=(
  frontend/src/features/admin/DocumentHub.tsx
  frontend/src/features/admin/DocumentStudio
)

if grep -R -n --fixed-strings '/ai-diagnostic' "${DOC_STUDIO_PATHS[@]}"; then
  fail "ghost /ai-diagnostic path is present in Document Studio source"
fi

if grep -R -n -E "HubDocumentType[^\n]*['\"]ai['\"]|documentTab[^\n]*['\"]ai['\"]" "${DOC_STUDIO_PATHS[@]}"; then
  fail "ghost AI document route is present in Document Studio source"
fi

if grep -R -n --fixed-strings 'Diagnostic Établi' frontend/src/features/admin/DocumentStudio; then
  fail "autonomous diagnostic label returned to Document Studio"
fi

printf '\nAUTOMATED_DOCUMENT_STUDIO_GATES_PASS\n'
printf '%s\n' 'Manual/external gates still required before final certification:'
printf '%s\n' '  - authenticated P1-P7 runtime smoke'
printf '%s\n' '  - archive/reopen/duplicate/print interaction checks'
printf '%s\n' '  - cabinet-branded PDF inspection'
printf '%s\n' '  - responsive/browser checks at 390 / 768 / desktop'
printf '%s\n' '  - human clinical/scientific/regulatory validation where applicable'
printf '%s\n' '  - merge and post-merge recertification'
