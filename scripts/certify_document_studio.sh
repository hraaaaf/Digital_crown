#!/usr/bin/env bash
set -euo pipefail

# T2 — Document Studio full-repository certification harness.
# Covers automated engineering gates for P1→P7 + T1.
# It intentionally does NOT certify authenticated runtime, cabinet PDF visuals,
# browser/responsive behavior, or human clinical/regulatory validity.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'DOCUMENT-STUDIO T2 FAIL: %s\n' "$1" >&2
  exit 1
}

pass() {
  printf 'DOCUMENT-STUDIO T2 PASS: %s\n' "$1"
}

command -v git >/dev/null 2>&1 || fail "git is required"
command -v python >/dev/null 2>&1 || fail "python is required"
command -v node >/dev/null 2>&1 || fail "node is required"
command -v npm >/dev/null 2>&1 || fail "npm is required"

python - <<'PY' || fail "Python >=3.12 required"
import sys
if sys.version_info < (3, 12):
    raise SystemExit(f"Python >=3.12 required; found {sys.version.split()[0]}")
print(f"Python {sys.version.split()[0]}")
PY

NODE_MAJOR="$(node -p 'Number(process.versions.node.split(".")[0])')"
[[ "$NODE_MAJOR" -ge 20 ]] || fail "Node >=20 required; found $(node --version)"

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

BACKEND_TARGETS=(
  backend/tests/test_document_preview_read_only.py
  backend/tests/test_partial_payment_no_inference.py
  backend/tests/test_ordonnance_preview_read_only_r7.py
  backend/tests/test_certificate_payload_policy_p3.py
  backend/tests/test_certificate_signature_policy_p3.py
  backend/tests/test_certificate_signer_policy_p3.py
  backend/tests/test_certificate_suggestion_policy_p3.py
  backend/tests/test_certificat_dates_p3.py
  backend/tests/test_certificat_free_content_p3.py
  backend/tests/test_certificat_pdf_integrity_p3.py
  backend/tests/test_certificat_pdf_robustness_p3.py
  backend/tests/test_certificat_qr_safety_p3.py
  backend/tests/test_certificat_semantics_p3.py
  backend/tests/test_devis_backend_contract_hardening.py
  backend/tests/test_devis_document_lifecycle.py
  backend/tests/test_devis_phase_contract.py
  backend/tests/test_devis_phase_sanitizer.py
  backend/tests/test_devis_teeth_data_consistency.py
  backend/tests/test_accounting_act_learning_guard.py
  backend/tests/test_accounting_pdf_readability.py
  backend/tests/test_honoraires_backend_contract_hardening.py
  backend/tests/test_honoraires_installment_contract_p2e.py
  backend/tests/test_honoraires_payment_allocation_p2f.py
  backend/tests/test_honoraires_pdf_safety.py
  backend/tests/test_honoraires_persistence_p2f.py
  backend/tests/test_installment_integrity_guards.py
  backend/tests/test_installment_payment_integrity_p4b.py
  backend/tests/test_installment_plan_contract_hardening.py
  backend/tests/test_installment_reconciliation_p2e.py
  backend/tests/test_installments_router.py
  backend/tests/test_document_installment_contract.py
  backend/tests/test_document_request_installment_boundary.py
  backend/tests/test_document_libre_permission_p3.py
  backend/tests/test_document_libre_safety_p3.py
  backend/tests/test_document_libre_title_escape_p3.py
  backend/tests/test_cmo_non_prescriptive_boundary.py
)

for target in "${BACKEND_TARGETS[@]}"; do
  [[ -f "$target" ]] || fail "expected targeted test missing: $target"
done

printf '\n[1/8] Positive development safety gate\n'
python scripts/prod_safety_check.py
pass "development safety configuration accepted"

printf '\n[2/8] Targeted Document Studio backend regression\n'
python -m pytest "${BACKEND_TARGETS[@]}" -q --maxfail=1
pass "targeted backend regression"

printf '\n[3/8] Full backend regression\n'
python -m pytest backend/tests -q --maxfail=1
pass "full backend suite"

printf '\n[4/8] Targeted Document Studio frontend regression\n'
(
  cd frontend
  npx vitest run src/features/admin/DocumentStudio
)
pass "targeted Document Studio frontend tests"

printf '\n[5/8] Full frontend regression\n'
(
  cd frontend
  npm test
)
pass "full frontend suite"

printf '\n[6/8] Frontend production build\n'
(
  cd frontend
  npm run build
)
pass "frontend production build"

printf '\n[7/8] Document Studio source invariants\n'
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
pass "Document Studio ghost-AI/autonomous-diagnosis invariants"

printf '\n[8/8] Negative production-safety gate\n'
if ENVIRONMENT=production \
   SECRET_KEY=changeme \
   DEBUG=true \
   DATABASE_URL='sqlite:///./x.db' \
   python scripts/prod_safety_check.py; then
  fail "production safety guard accepted intentionally unsafe production settings"
else
  pass "production safety guard rejected unsafe settings"
fi

printf '\nAUTOMATED DOCUMENT STUDIO T2 GATES PASSED for %s\n' "$HEAD_SHA"
printf 'SEPARATE GATES STILL REQUIRED BEFORE A FULL CERTIFICATION CLAIM:\n'
printf '  - authenticated P1→P7 runtime smoke on the complete app\n'
printf '  - real archive/reopen/duplicate/print/payment flows where applicable\n'
printf '  - cabinet-branded PDF visual checks, including long/multipage cases\n'
printf '  - responsive/browser/accessibility checks at 390px, 768px and desktop\n'
printf '  - human clinical/scientific/regulatory validation where applicable\n'
printf '  - stacked PR merge + post-merge recertification\n'
printf 'This harness proves automated engineering gates only.\n'
