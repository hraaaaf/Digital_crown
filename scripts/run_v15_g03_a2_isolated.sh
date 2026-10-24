#!/usr/bin/env bash
# FUE-G03 A2 — authorized manual lab, not a GitHub Actions workflow.
# Only disposable synthetic patients. NEVER run on a cabinet or production host.
set -Eeuo pipefail

fail() { printf 'A2 MANUAL LAB BLOCKED: %s\n' "$*" >&2; exit 1; }

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "not inside a Git checkout"
cd "$ROOT"
[[ "$(git branch --show-current)" == "test/v15-fue-g03-a2-fallback-20261024" ]] ||
  fail "checkout the A2 branch (not main, master, A1 or A3)"
git diff --quiet && git diff --cached --quiet ||
  fail "tracked files changed; use a clean A2 checkout"
command -v python3.12 >/dev/null 2>&1 || fail "Python 3.12 required"
command -v npm >/dev/null 2>&1 || fail "Node/npm required"
command -v curl >/dev/null 2>&1 || fail "curl required"
node -e 'if (+process.versions.node.split(".")[0]<20) process.exit(1)' ||
  fail "Node.js 20+ required"

[[ ! -e t2-runtime-cert.db ]] ||
  fail "disposable SQLite already exists: start a FRESH Codespace; refusing overwrite"
[[ ! -e frontend/artifacts/v15-03-a2-fallback-real/seed.json ]] ||
  fail "old evidence exists: start a FRESH Codespace to prevent stale evidence reuse"
for port in 8005 5173; do
  if curl --silent --max-time 2 "http://127.0.0.1:$port/" >/dev/null 2>&1; then
    fail "localhost port $port already in use; refusing to attach to an unknown runtime"
  fi
done

export ENVIRONMENT=test
export DATABASE_URL="sqlite:///./t2-runtime-cert.db"
export DIGITALCROWN_ISOLATED_RUNTIME=1
export DIGITALCROWN_ISOLATION_DB_FINGERPRINT=c04779c8d18b3ac12a0f4093a47a5d0c3c0e2251714be532893cfa052e9ee780
export T2_G03_A2=1
export T2_STATION_FUE=1
export TELEMETRY_ENABLED=false
export CLOUD_AI_ENABLED=false
export DEBUG=false
export ALLOWED_ORIGINS="http://127.0.0.1:5173,http://localhost:5173"
export STATION_HANDOFF_PUBLIC_ORIGIN="http://127.0.0.1:5173"
export T2_USER="t2-browser@cabinet.ma"
export T2_PASSWORD="$(python3.12 -c 'import secrets;print(secrets.token_urlsafe(32))')"
export EVALUATED_SHA="$(git rev-parse HEAD)"
[[ "$EVALUATED_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "invalid exact Git SHA"

backend_pid=''
frontend_pid=''
cleanup() {
  if [[ -n "$frontend_pid" ]]; then kill "$frontend_pid" 2>/dev/null || true; fi
  if [[ -n "$backend_pid" ]]; then kill "$backend_pid" 2>/dev/null || true; fi
}
trap cleanup EXIT

printf 'A2 disposable browser/API/SQL lab — exact SHA %s\n' "$EVALUATED_SHA"
python3.12 -m venv .venv-a2-cert
# shellcheck disable=SC1091
source .venv-a2-cert/bin/activate
python -m pip install --upgrade pip
# Match the previously reviewed A1/A2 CI Python dependency contract.
python -m pip install torch==2.12.0 torchvision==0.27.0 \
  --index-url https://download.pytorch.org/whl/cpu
grep -vE '^(torch|torchvision)([<=>].*)?$' requirements.txt \
  > .venv-a2-cert/requirements-no-torch.txt
python -m pip install -r .venv-a2-cert/requirements-no-torch.txt
python -m py_compile scripts/seed_v15_station_fallback_a2.py
python -m pytest backend/tests/test_station_patient_session_v15.py \
  backend/tests/test_station_identity_pairing_migration_v15.py \
  -q --disable-warnings

(
  cd frontend
  npm ci
  npm install --no-save --package-lock=false playwright@1.55.0
  npx playwright install --with-deps chromium
  node --check scripts/certify-v15-03-a2-real-fallback.mjs
  npx vitest run src/features/hub/StationPatientIdentity.test.tsx \
    --maxWorkers=1 --fileParallelism=false
  npm run build
)

python scripts/t2_runtime_server.py > /tmp/v15-g03-a2-manual-backend.log 2>&1 &
backend_pid=$!
backend_ready=0
for i in $(seq 1 90); do
  if curl --fail --silent http://127.0.0.1:8005/health > /dev/null; then
    backend_ready=1
    break
  fi
  sleep 1
done
if [[ "$backend_ready" != 1 ]]; then
  tail -60 /tmp/v15-g03-a2-manual-backend.log >&2
  fail "isolated backend did not become healthy"
fi
python scripts/seed_v15_station_fallback_a2.py

(
  cd frontend
  exec npm run dev -- --host 127.0.0.1 --port 5173
) > /tmp/v15-g03-a2-manual-frontend.log 2>&1 &
frontend_pid=$!
frontend_ready=0
for i in $(seq 1 90); do
  if curl --fail --silent http://127.0.0.1:5173/ > /dev/null; then
    frontend_ready=1
    break
  fi
  sleep 1
done
if [[ "$frontend_ready" != 1 ]]; then
  tail -60 /tmp/v15-g03-a2-manual-frontend.log >&2
  fail "Vite Station did not become healthy"
fi

(cd frontend && node scripts/certify-v15-03-a2-real-fallback.mjs)
python scripts/seed_v15_station_fallback_a2.py --verify

python - <<'PY'
import json, os
from pathlib import Path
p=Path("frontend/artifacts/v15-03-a2-fallback-real/sql-after.json")
d=json.loads(p.read_text())
assert d["status"]=="PASS" and d["head"]==os.environ["EVALUATED_SHA"]
assert d["visualCaptures"]>=10
assert {390,430,768,1280}.issubset(d["verifiedViewports"])
print("A2_MANUAL_ISOLATED_LAB_PASS", os.environ["EVALUATED_SHA"])
PY
python -m zipfile -c A2_REAL_AFTER_LAB_EVIDENCE.zip \
  frontend/artifacts/v15-03-a2-fallback-real
sha256sum A2_REAL_AFTER_LAB_EVIDENCE.zip
printf '\nDONE — synthetic proof archive: A2_REAL_AFTER_LAB_EVIDENCE.zip\n'
printf 'Manual Codespaces lab only. Does NOT waive required GitHub CI/human approval.\n'