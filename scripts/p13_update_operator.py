from __future__ import annotations

import argparse
import getpass
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CONFIRMATION_TOKEN = "METTRE_A_JOUR"


class OperatorError(RuntimeError):
    pass


def _base_url(value: str) -> str:
    raw = str(value or "").strip().rstrip("/")
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        raise OperatorError("BASE_URL_SCHEME_INVALID")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise OperatorError("BASE_URL_MUST_BE_LOOPBACK")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise OperatorError("BASE_URL_INVALID")
    return raw


def _request_json(
    request: urllib.request.Request,
    *,
    expected_status: set[int],
    timeout: int = 90,
) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            body = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise OperatorError(f"HTTP_{exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise OperatorError("LOCAL_API_UNREACHABLE") from exc
    if status not in expected_status:
        raise OperatorError(f"UNEXPECTED_HTTP_STATUS_{status}")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OperatorError("LOCAL_API_JSON_INVALID") from exc
    if not isinstance(payload, dict):
        raise OperatorError("LOCAL_API_RESPONSE_INVALID")
    return payload


def _login(base_url: str, username: str) -> str:
    password = getpass.getpass("Synthetic cabinet admin password: ")
    body = urllib.parse.urlencode({"username": username, "password": password}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/api/auth/login",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    payload = _request_json(request, expected_status={200}, timeout=30)
    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise OperatorError("LOGIN_ACCESS_TOKEN_MISSING")
    return token


def _authorized_request(base_url: str, token: str, path: str, *, body: dict[str, Any] | None = None, method: str = "GET"):
    data = None
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    return _request_json(request, expected_status={200, 202})


def prepare(base_url: str, username: str, manifest_path: Path) -> dict[str, Any]:
    envelope = json.loads(manifest_path.expanduser().resolve().read_text(encoding="utf-8"))
    if not isinstance(envelope, dict):
        raise OperatorError("SIGNED_MANIFEST_INVALID")
    token = _login(base_url, username)
    return _authorized_request(
        base_url,
        token,
        "/api/update/prepare",
        body={"manifest": envelope},
        method="POST",
    )


def apply(base_url: str, username: str, job_id: str) -> dict[str, Any]:
    token = _login(base_url, username)
    return _authorized_request(
        base_url,
        token,
        f"/api/update/{job_id}/apply",
        body={"confirmation": CONFIRMATION_TOKEN},
        method="POST",
    )


def status(base_url: str, username: str, job_id: str) -> dict[str, Any]:
    token = _login(base_url, username)
    return _authorized_request(base_url, token, f"/api/update/{job_id}/status")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Operate the installed Digital Crown P10 update API through loopback only."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8005")
    parser.add_argument("--username", required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--manifest", required=True, type=Path)

    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("--job-id", required=True)

    status_parser = sub.add_parser("status")
    status_parser.add_argument("--job-id", required=True)

    args = parser.parse_args()
    base_url = _base_url(args.base_url)
    if args.command == "prepare":
        result = prepare(base_url, args.username, args.manifest)
        print(json.dumps(result, indent=2, sort_keys=True))
        print(f"P13_UPDATE_PREPARED=PASS_ATTESTED job_id={result.get('job_id', '')}")
    elif args.command == "apply":
        result = apply(base_url, args.username, args.job_id)
        print(json.dumps(result, indent=2, sort_keys=True))
        print(f"P13_UPDATE_APPLY_ACCEPTED=PASS_ATTESTED job_id={args.job_id}")
    else:
        result = status(base_url, args.username, args.job_id)
        print(json.dumps(result, indent=2, sort_keys=True))
        print(f"P13_UPDATE_STATUS=OBSERVED job_id={args.job_id} status={result.get('status', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
