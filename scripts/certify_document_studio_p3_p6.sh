#!/usr/bin/env bash
set -euo pipefail

# Document Studio P3→P6 full-repository certification harness.
# Mirrors the repository CI environment and fails closed.
# It does NOT replace authenticated runtime, visual PDF, responsive or financial human gates.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'P3-P6 FAIL: %s\n' "$1" >&2
  exit 1
}

pass() {
  printf 'P3-P6 PASS: %s\n' "$1"
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
printf 'Document Studio P3-P6 candidate head: %s\n' "$HEAD_SHA"

export SECRET_KEY="ci-only-secret-key-minimum-32-characters-long"
export DATABASE_URL="sqlite:///:memory:"
export ENVIRONMENT="development"
export TELEMETRY_ENABLED="false"
export CLOUD_AI_ENABLED="false"

printf '\n[1/7] Positive production-safety gate\n'
python scripts/prod_safety_check.py
pass "development safety configuration accepted"

printf '\n[2/7] Targeted backend regression P3→P6\n'
python -m pytest \
  backend/tests/test_devis_document_lifecycle.py \
  backend/tests/test_devis_phase_sanitizer.py \
  backend/tests/test_devis_phase_contract.py \
  backend/tests/test_devis_backend_contract_hardening.py \
  backend/tests/test_accounting_pdf_readability.py \
  backend/tests/test_document_financial_contract_p4_p5.py \
  backend/tests/test_honoraires_financial_contract_p4.py \
  backend/tests/test_honoraires_prearchive_contract_p4.py \
  backend/tests/test_honoraires_installment_contract_p2e.py \
  backend/tests/test_honoraires_payment_allocation_p2f.py \
  backend/tests/test_honoraires_persistence_p2f.py \
  backend/tests/test_financial_document_no_clinical_inference_p4.py \
  backend/tests/test_installment_contract_p5.py \
  backend/tests/test_installments_router.py \
  backend/tests/test_installment_payment_integrity_p4b.py \
  backend/tests/test_installment_reconciliation_p2e.py \
  backend/tests/test_document_libre_safety_p3.py \
  backend/tests/test_document_libre_permission_p3.py \
  backend/tests/test_document_libre_title_escape_p3.py \
  backend/tests/test_document_libre_certification_p6.py \
  backend/tests/test_document_preview_read_only.py \
  -q
pass "targeted P3-P6 backend regression"

printf '\n[3/7] Full backend suite\n'
python -m pytest backend/tests -q --maxfail=1
pass "full backend suite"

printf '\n[4/7] Targeted frontend regression P4→P6\n'
(
  cd frontend
  npm test -- \
    src/features/admin/store/useAccountingStore.p4.test.ts \
    src/features/admin/DocumentStudio/Forms/InstallmentStudio.p5.test.tsx \
    src/features/admin/DocumentStudio/Forms/LibreForm.p3c.test.tsx
)
pass "targeted P4-P6 frontend regression"

printf '\n[5/7] Full frontend suite\n'
(
  cd frontend
  npm test
)
pass "full frontend suite"

printf '\n[6/7] Frontend production build\n'
(
  cd frontend
  npm run build
)
pass "frontend build"

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

printf '\nAUTOMATED DOCUMENT STUDIO P3-P6 GATES PASSED for %s\n' "$HEAD_SHA"
printf 'REMAINING MANUAL GATES:\n'
printf '  - authenticated P3/P4/P5/P6 runtime flows on the same exact head\n'
printf '  - cabinet-branded PDF visual inspection, including P6 A4/A5, long/table/special-character cases\n'
printf '  - responsive/browser checks at 390px, 768px and desktop\n'
printf '  - financial reconciliation review for P4/P5 persisted Acte/Payment/Installment records\n'
printf 'NO production-ready, merge-ready or clinical/financial certification claim is implied until those gates pass.\n'
