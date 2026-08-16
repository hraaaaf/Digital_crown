#!/usr/bin/env bash
set -euo pipefail

# P3 Devis full-repository certification harness.
# Mirrors the repository CI commands and fails closed.
# This script does NOT replace the authenticated UI/PDF/responsive smoke gates.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
  printf 'P3-H FAIL: %s\n' "$1" >&2
  exit 1
}

pass() {
  printf 'P3-H PASS: %s\n' "$1"
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
printf 'P3-H candidate head: %s\n' "$HEAD_SHA"

export SECRET_KEY="ci-only-secret-key-minimum-32-characters-long"
export DATABASE_URL="sqlite:///:memory:"
export ENVIRONMENT="development"
export TELEMETRY_ENABLED="false"
export CLOUD_AI_ENABLED="false"

printf '\n[1/6] Positive production-safety gate\n'
python scripts/prod_safety_check.py
pass "development safety configuration accepted"

printf '\n[2/6] Targeted P3 Devis backend regression\n'
python -m pytest \
  backend/tests/test_devis_document_lifecycle.py \
  backend/tests/test_devis_phase_sanitizer.py \
  backend/tests/test_devis_phase_contract.py \
  backend/tests/test_devis_backend_contract_hardening.py \
  backend/tests/test_accounting_pdf_readability.py \
  -q
pass "targeted P3 backend regression"

printf '\n[3/6] Full backend suite\n'
python -m pytest backend/tests -q --maxfail=1
pass "full backend suite"

printf '\n[4/6] Full frontend test suite\n'
(
  cd frontend
  npm test
)
pass "full frontend test suite"

printf '\n[5/6] Frontend production build\n'
(
  cd frontend
  npm run build
)
pass "frontend build"

printf '\n[6/6] Negative production-safety gate\n'
if ENVIRONMENT=production \
   SECRET_KEY=changeme \
   DEBUG=true \
   DATABASE_URL='sqlite:///./x.db' \
   python scripts/prod_safety_check.py; then
  fail "production safety guard accepted an intentionally unsafe production config"
else
  pass "production safety guard rejected unsafe config"
fi

printf '\nAUTOMATED P3-H GATES PASSED for %s\n' "$HEAD_SHA"
printf 'REMAINING MANUAL GATES:\n'
printf '  - authenticated Devis runtime smoke: adult + pediatric, edit/reorder, preview, explicit archive, duplicate handling, print\n'
printf '  - cabinet-branded PDF visual checks: short, signature, adult/pediatric examples\n'
printf '  - responsive/browser checks: 390px, 768px, desktop\n'
printf 'NO production-ready or merge-ready claim is implied until those manual gates also pass.\n'
