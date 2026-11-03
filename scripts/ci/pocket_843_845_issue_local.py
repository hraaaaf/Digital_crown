#!/usr/bin/env python3
"""Create real short-lived (5 min) mobile pairing for a disposable synthetic tenant.

Do not print JWTs, test password, QR token, cookie or any real cabinet data.
The temporary six-digit code and its capability-gated link are intentionally
printed so the owner can enter them on the iPhone during the live runner window.
"""
import datetime
import http.cookiejar
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8005"
KEYFILE = Path("/tmp/pocket-fue-gateway-session.json")
ALLOWED_HOST = "127.0.0.1"


def send(path, *, method="GET", payload=None, bearer=None):
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.load(response)


def check_tunnel(origin, key):
    jar = http.cookiejar.CookieJar()
    tls = ssl.create_default_context(cafile="/tmp/pocket-fue-loopback-cert.pem")
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPSHandler(context=tls),
    )
    public_url = origin + "/session/" + key
    for _ in range(40):
        try:
            # The first-party 200 confirmation avoids iOS redirect cookie loss.
            with opener.open(public_url, timeout=7) as response:
                landing = response.read(20000).decode("utf-8", "replace")
                if response.url != public_url or response.status != 200:
                    raise ValueError("Unexpected session landing response")
                if "Continuer vers l'appairage" not in landing:
                    raise ValueError("Missing Safari first-party confirmation")
                if not any(cookie.name == "pocket_fue" and cookie.secure for cookie in jar):
                    raise ValueError("Secure session cookie missing")
            with opener.open(origin + "/mobile/onboarding", timeout=7) as response:
                html = response.read(20000).decode("utf-8", "replace")
                if response.url != origin + "/mobile/onboarding" or "<html" not in html.lower():
                    raise ValueError("Authenticated onboarding failed")
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("TLS tunnel and authenticated onboarding not reachable")


def main():
    if os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "1" or os.environ.get("ENVIRONMENT") != "test":
        raise RuntimeError("Refusing any nonisolated pairing issuance")
    origin = os.environ.get("FUE_TUNNEL_ORIGIN", "").rstrip("/")
    parsed = urllib.parse.urlparse(origin)
    if (parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST
            or parsed.port != 5443 or parsed.path or parsed.query or parsed.fragment):
        raise RuntimeError("Refusing any nonloopback synthetic TLS target")
    key = json.loads(KEYFILE.read_text())["key"]
    check_tunnel(origin, key)

    password = os.environ.get("T2_PASSWORD")
    if not password:
        raise RuntimeError("Isolated T2 password missing")
    form = urllib.parse.urlencode({"username": "t2-browser@cabinet.ma", "password": password}).encode()
    request = urllib.request.Request(
        BASE + "/api/auth/login", data=form, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        login = json.load(response)
    token = login.get("access_token")
    if not token:
        raise RuntimeError("Synthetic owner authentication failed")
    options = send("/api/mobile/bridge-options", bearer=token)
    target = next((t for t in options.get("targets", []) if t.get("is_current_user")), None)
    if target is None:
        raise RuntimeError("No synthetic owner available for approved pairing")
    response = send(
        "/api/mobile/bridge-pairing", method="POST", bearer=token,
        payload={"target_user_id": target["id"], "destination": "agenda"},
    )
    code = response.get("token_code")
    if not isinstance(code, str) or not (len(code) == 6 and code.isdigit()):
        raise RuntimeError("Backend did not issue valid six-digit pairing code")
    if response.get("expires_in") != 300:
        raise RuntimeError("Unexpected backend pairing TTL")

    deadline = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=300)
    print("POCKET_FUE_READY=true", flush=True)
    print("POCKET_FUE_LINK=" + origin + "/session/" + key, flush=True)
    print("POCKET_FUE_CODE=" + code, flush=True)
    print("POCKET_FUE_EXPIRES_UTC=" + deadline.isoformat(timespec="seconds"), flush=True)
    print("POCKET_FUE_DEMO_ONLY=synthetic-disposable-no-clinic-data", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Error messages must not contain secret URLs/tokens in workflow logs.
        print("POCKET_FUE_FAILED=" + type(exc).__name__, file=sys.stderr)
        raise SystemExit(1)
