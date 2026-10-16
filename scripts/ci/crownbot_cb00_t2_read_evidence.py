#!/usr/bin/env python3
"""CB-00: measure a useful, permissioned patient read on an ISOLATED localhost T2.

This script NEVER starts T2 or toggles feature flags; use synthetic patients only.
It measures complete HTTP response, not DOM/UX or genuine process cold-start.
A standalone positive read is NOT proof of zero DB writes; compare isolated DB
snapshots/audit logs separately. Do not use in a real cabinet.

Example, from repo root with disposable T2 flags explicitly enabled there:
  DIGITALCROWN_ISOLATED_RUNTIME=1 T2_USER=t2-dentist@example.test \
  T2_PASSWORD='synthetic' T2_PATIENT_ID=7 \
  python scripts/ci/crownbot_cb00_t2_read_evidence.py --out /tmp/cb00-read.json
Optional negative T2 fixtures: T2_DENIED_USER, T2_DENIED_PASSWORD,
T2_FOREIGN_PATIENT_ID, T2_DENIED_COMMAND. Never store names, credentials, tokens or responses.
"""
import argparse
import json
import os
import platform
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from http.cookiejar import CookieJar
from urllib.request import Request, HTTPRedirectHandler, HTTPCookieProcessor, build_opener

class _NoRedirect(HTTPRedirectHandler):
    # Prevent auth header forwarding to any redirect destination.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

_NO_REDIRECT_OPENER = build_opener(_NoRedirect, HTTPCookieProcessor(CookieJar()))
_ANONYMOUS_OPENER = build_opener(_NoRedirect)


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        raise ValueError('No successful measurements')
    ordered = sorted(values)
    x = (len(ordered) - 1) * ratio
    low = int(x)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (x - low)


def checked_origin(url: str) -> str:
    parsed = urlparse(url)
    if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost')
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment
            or parsed.port is None):
        raise ValueError('REFUSED: explicit http://localhost:<port> T2 origin only')
    return f'http://{parsed.hostname}:{parsed.port}'


def require_t2_environment(args) -> tuple[str, str, str, int]:
    api = checked_origin(args.api)
    if os.getenv('DIGITALCROWN_ISOLATED_RUNTIME') != '1':
        raise ValueError('REFUSED: isolated T2 environment assertion required')
    user = os.getenv('T2_USER', '')
    password = os.getenv('T2_PASSWORD', '')
    raw_id = os.getenv('T2_PATIENT_ID', '')
    if not user.startswith('t2-') or not password:
        raise ValueError('REFUSED: synthetic T2 dentist credentials required')
    if not re.fullmatch(r'[1-9]\d{0,9}', raw_id):
        raise ValueError('REFUSED: T2_PATIENT_ID must be a synthetic positive ID')
    if not 30 <= args.n <= 200:
        raise ValueError('REFUSED: n must be 30..200 warm measurements')
    denied_user = os.getenv('T2_DENIED_USER', '')
    denied_password = os.getenv('T2_DENIED_PASSWORD', '')
    if bool(denied_user) != bool(denied_password):
        raise ValueError('REFUSED: denied identity fixture must have user and password')
    if denied_user and not denied_user.startswith('t2-'):
        raise ValueError('REFUSED: denied identity is not synthetic')
    if os.getenv('T2_DENIED_COMMAND', '/rdv') not in ('/patient', '/rdv', '/devis'):
        raise ValueError('REFUSED: denied command not in supported capabilities')
    foreign_id = os.getenv('T2_FOREIGN_PATIENT_ID', '')
    if foreign_id and not re.fullmatch(r'[1-9]\d{0,9}', foreign_id):
        raise ValueError('REFUSED: foreign patient fixture must be synthetic positive ID')
    if not Path(args.out).parent.exists():
        raise ValueError('REFUSED: output parent directory missing')
    return api, user, password, int(raw_id)


def http_json(url: str, data: dict, bearer: str | None = None, form=False, anonymous=False):
    encoded = (urlencode(data).encode('utf-8') if form
               else json.dumps(data, separators=(',', ':')).encode('utf-8'))
    headers = {'Content-Type': 'application/x-www-form-urlencoded' if form
               else 'application/json'}
    if bearer:
        headers['Authorization'] = f'Bearer {bearer}'
    request = Request(url, data=encoded, headers=headers, method='POST')
    started = time.perf_counter_ns()
    try:
        with (_ANONYMOUS_OPENER if anonymous else _NO_REDIRECT_OPENER).open(request, timeout=15) as response:
            raw = response.read()
            status = response.status
    except HTTPError as exc:
        status = exc.code
        raw = exc.read()
    except URLError as exc:
        raise RuntimeError('T2 HTTP unreachable (response NOT measured)') from exc
    elapsed = (time.perf_counter_ns() - started) / 1e6
    try:
        payload = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError('T2 returned non-JSON content') from exc
    if not isinstance(payload, dict):
        raise RuntimeError('T2 returned non-object content')
    return status, payload, elapsed


def login(api, user, password, *, enroll_workstation=True):
    status, payload, _ = http_json(
        f'{api}/api/auth/login', {'username': user, 'password': password}, form=True)
    token = payload.get('access_token')
    if status != 200 or not isinstance(token, str) or not token:
        raise RuntimeError('Synthetic T2 login failed (check workstation session)')
    # Workstation identity is a separate production authorization boundary.
    # Preserve HttpOnly workstation cookies in the restricted localhost opener.
    if enroll_workstation:
        enroll_status, _, _ = http_json(
            f'{api}/api/workstation/enroll',
            {'accountPassword': password},
            token,
        )
        if enroll_status != 200:
            raise RuntimeError('T2 workstation enrollment denied; no measurements accepted')
    return token


def assert_read(status, payload, expected_id):
    patient = payload.get('patient')
    if (status != 200 or payload.get('status') != 'read'
            or not isinstance(patient, dict) or patient.get('id') != expected_id
            or payload.get('proposal') is not None
            or any(k in payload for k in ('pendingActionId', 'pending_action_id', 'action_id'))):
        raise RuntimeError('FAIL CLOSED: unexpected useful patient-read contract')


def assert_clarification(status, payload):
    if (status != 200 or payload.get('status') != 'clarification'
            or payload.get('proposal') is not None or 'patient' in payload):
        raise RuntimeError('FAIL CLOSED: unexpected clarification contract')


def run(args):
    api, user, password, patient_id = require_t2_environment(args)
    token = login(api, user, password)
    endpoint = f'{api}/api/bot/workflows/preview'
    # Permission and route gate: missing token must fail, never silently pass.
    unauth_status, _, _ = http_json(endpoint, {'messages': ['/patient', str(patient_id)]}, anonymous=True)
    if unauth_status != 401:
        raise RuntimeError('FAIL CLOSED: anonymous preview did not return 401')
    status, payload, _ = http_json(endpoint, {'messages': ['/patient']}, token)
    assert_clarification(status, payload)
    transcript = {'messages': ['/patient', str(patient_id)]}
    # First after-login useful read; NOT a true cold-start measurement.
    status, payload, first_ms = http_json(endpoint, transcript, token)
    assert_read(status, payload, patient_id)
    timings = []
    for _ in range(args.n):
        status, payload, elapsed = http_json(endpoint, transcript, token)
        assert_read(status, payload, patient_id)
        timings.append(elapsed)
    checks = {'anonymous_401': 'PASS', 'clarification_no_patient': 'PASS',
              'useful_read_no_proposal': 'PASS'}
    denied_user = os.getenv('T2_DENIED_USER', '')
    if denied_user:
        denied_token = login(api, denied_user, os.environ['T2_DENIED_PASSWORD'], enroll_workstation=False)
        status, payload, _ = http_json(endpoint, {'messages': [os.getenv('T2_DENIED_COMMAND', '/rdv')]}, denied_token)
        if status != 403 or 'patient' in payload or 'proposal' in payload:
            raise RuntimeError('FAIL CLOSED: denied permission is not isolated')
        checks['permission_denied_403'] = 'PASS'
    else:
        checks['permission_denied_403'] = 'NOT_RUN_NO_FIXTURE'
    foreign_id = os.getenv('T2_FOREIGN_PATIENT_ID', '')
    if foreign_id:
        status, payload, _ = http_json(
            endpoint, {'messages': ['/patient', foreign_id]}, token)
        if status != 404 or 'patient' in payload or 'proposal' in payload:
            raise RuntimeError('FAIL CLOSED: cross-tenant lookup contract failure')
        checks['foreign_patient_404'] = 'PASS'
    else:
        checks['foreign_patient_404'] = 'NOT_RUN_NO_FIXTURE'
    data = {
        'scope': 'SYNTHETIC_LOCALHOST_T2',
        'measurement': 'full HTTP response for an authorized useful patient read',
        'browser_click_to_DOM': 'NOT_MEASURED',
        'true_process_cold_start': 'NOT_MEASURED',
        'database_before_after_diff': 'NOT_MEASURED',
        'source_head': os.getenv('T2_SOURCE_HEAD', 'UNVERIFIED'),
        'source_head_provenance': 'operator-provided, not introspected by this script',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'platform': platform.platform(), 'python': platform.python_version(),
        'n_warm': len(timings),
        'first_useful_read_ms': round(first_ms, 2),
        'p50_http_ms': round(percentile(timings, .50), 2),
        'p95_http_ms': round(percentile(timings, .95), 2),
        'max_http_ms': round(max(timings), 2),
        'checks': checks,
    }
    # Atomic output, no credentials, patient labels, IDs or response bodies.
    output = Path(args.out)
    temporary = output.with_suffix(output.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    temporary.replace(output)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api', default='http://127.0.0.1:8005')
    parser.add_argument('--n', type=int, default=30)
    parser.add_argument('--out', default='/tmp/cb00-t2-useful-read.json')
    args = parser.parse_args()
    try:
        data = run(args)
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from None
    print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
