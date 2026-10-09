"""FUE-G CLOUD-LAB: 4 disposable Docker clients using real HTTPS to T2 API.

Network roles are distinct Docker namespaces. HTTPS validates the SAN and
ephemeral CA with Python's default strict certificate verification. This is
NOT browser CA trust, OS installation, actual Windows networking, or FUE-G.
Never print PIN, pairing code, tokens, credentials, or cookie material.
"""
import hashlib
import http.cookiejar
import json
import os
import pathlib
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

role = os.getenv("FUE_CLIENT_ROLE")
phase = os.getenv("FUE_PHASE")
if role not in {"A", "B", "C", "D"} or phase not in {"setup", "pair", "offline", "recover"}:
    raise SystemExit("Invalid role or phase")
base = "https://cabinet.local:8005"
ca = os.environ["FUE_CA_FILE"]
state_dir = pathlib.Path(os.environ["FUE_STATE_DIR"])
state_dir.mkdir(parents=True, exist_ok=True)
cookies_path = state_dir / "cookies.txt"
identity_path = state_dir / "identity.json"
report_dir = state_dir / "reports"
report_dir.mkdir(exist_ok=True)
password = os.environ["T2_PASSWORD"]
owner_pin = os.environ["T2_OWNER_PIN"]
context = ssl.create_default_context(cafile=ca)
context.check_hostname = True
context.verify_mode = ssl.CERT_REQUIRED
cookies = http.cookiejar.MozillaCookieJar(str(cookies_path))
if cookies_path.exists():
    cookies.load(ignore_discard=True, ignore_expires=True)
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=context),
    urllib.request.HTTPCookieProcessor(cookies),
    urllib.request.ProxyHandler({}),
)

def call(route, *, method="GET", data=None, bearer=None, expect=200, timeout=10):
    if data is not None:
        if route == "/api/auth/login":
            payload = urllib.parse.urlencode(data).encode()
            content_type = "application/x-www-form-urlencoded"
        else:
            payload = json.dumps(data, separators=(",", ":")).encode()
            content_type = "application/json"
    else:
        payload = None
        content_type = None
    headers = {}
    if content_type:
        headers["Content-Type"] = content_type
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    req = urllib.request.Request(base + route, data=payload, headers=headers, method=method)
    try:
        with opener.open(req, timeout=timeout) as response:
            status = response.status
            body = response.read(150000)
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read(150000)
    if status != expect:
        raise AssertionError(f"{route}: HTTP {status}, expected {expect}")
    try:
        return json.loads(body)
    except ValueError:
        return {}

def login(username="t2-browser@cabinet.ma"):
    response = call("/api/auth/login", method="POST", data={
        "username": username, "password": password,
    })
    token = response.get("access_token")
    if not token:
        raise AssertionError("Synthetic owner login did not yield access token")
    return token

def ensure_tls_refusal():
    # Unknown ephemeral root must fail in a normal strict client.
    default_client = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        urllib.request.ProxyHandler({}),
    )
    try:
        default_client.open(base + "/health", timeout=6)
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLCertVerificationError):
            return
        raise AssertionError("Expected explicit certificate verification error") from exc
    raise AssertionError("Untrusted CA was silently accepted")

def record(status, **kwargs):
    d = {"role": role, "phase": phase, "status": status, "tlsVerified": phase != "offline",
         "utc": int(time.time()), "productHead": os.environ.get("PRODUCT_HEAD")}
    d.update(kwargs)
    (report_dir / (phase + ".json")).write_text(json.dumps(d, indent=2), encoding="utf-8")
    print(json.dumps({"role": role, "phase": phase, "status": status,
                      "tlsVerified": d["tlsVerified"], "productHead": d["productHead"]}))

if phase == "offline":
    try:
        call("/health", timeout=3)
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
        record("PASS", refusal="SERVER_UNREACHABLE")
    else:
        raise AssertionError("Stopped server was unexpectedly reachable")
    sys.exit(0)

topology = call("/api/health/topology")
if topology.get("port") != 8005 or topology.get("tlsEnabled") is not True or topology.get("lanExposed") is not True:
    raise AssertionError("Real topology endpoint does not describe LAN HTTPS :8005")
call("/api/health/db")
ensure_tls_refusal()
token = login()

if phase == "setup":
    if role != "A":
        raise AssertionError("PIN setup only by A coordinator")
    call("/api/workstation/owner-pin", method="POST", bearer=token,
         data={"accountPassword": password, "newPin": owner_pin})
    record("PASS")
elif phase == "pair":
    pre = call("/api/workstation/bootstrap", bearer=token)
    if pre.get("workstationId"):
        raise AssertionError("Annex had workstation identity BEFORE pairing")
    code = call("/api/workstation/pairing-code", method="POST", bearer=token,
                data={"ownerPin": owner_pin}).get("code")
    if not code or len(code) != 6:
        raise AssertionError("No single-use pairing code")
    paired = call("/api/workstation/pair", method="POST", bearer=token,
                  data={"code": code, "displayName": ("Cloud Annex Assistante" if role == "C" else ("Cloud Reception Accueil" if role == "D" else "Cloud Annex " + role))})
    wid = paired.get("workstationId")
    if not wid:
        raise AssertionError("No workstationId after pairing")
    cookies.save(ignore_discard=True, ignore_expires=True)
    identity_path.write_text(json.dumps({"id": wid}), encoding="utf-8")
    # A separate fresh identity must not replay the already-consumed code.
    new_opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=context), urllib.request.ProxyHandler({}),
    )
    req = urllib.request.Request(base + "/api/workstation/pair",
        data=json.dumps({"code": code, "displayName": "Replay probe"}).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="POST")
    try:
        new_opener.open(req, timeout=10)
    except urllib.error.HTTPError as exc:
        if exc.code != 403:
            raise AssertionError(f"Replay returned HTTP {exc.code}, expected 403")
    else:
        raise AssertionError("Pairing code replay unexpectedly succeeded")
    digest = hashlib.sha256(str(wid).encode()).hexdigest()[:16]
    if role in {"C", "D"}:
        # App models SECRETAIRE, not a separate ASSISTANTE enum.
        assistant = login("t2-restricted@cabinet.ma" if role == "C" else "t2-reception@cabinet.ma")
        me = call("/api/auth/me", bearer=assistant)
        if me.get("role") != "SECRETAIRE":
            raise AssertionError("Unexpected synthetic assistant role")
        state = call("/api/workstation/bootstrap", bearer=assistant)
        if state.get("workstationId") != wid:
            raise AssertionError("Staff session lost its own paired workstation")
        call("/api/patients/", bearer=assistant, expect=403)
        record("PASS", workstationHash=digest, replayRejected=True,
               assistantPermissionDenied=True, assistantRole="SECRETAIRE",
               persona=("Assistante" if role == "C" else "Accueil"))
    else:
        record("PASS", workstationHash=digest, replayRejected=True)
elif phase == "recover":
    expected = json.loads(identity_path.read_text())["id"]
    bootstrap = call("/api/workstation/bootstrap", bearer=token)
    if bootstrap.get("workstationId") != expected:
        raise AssertionError("Workstation identity changed across server restart")
    digest = hashlib.sha256(str(expected).encode()).hexdigest()[:16]
    if role in {"C", "D"}:
        assistant = login("t2-restricted@cabinet.ma" if role == "C" else "t2-reception@cabinet.ma")
        me = call("/api/auth/me", bearer=assistant)
        if me.get("role") != "SECRETAIRE":
            raise AssertionError("Assistant role changed after server restart")
        state = call("/api/workstation/bootstrap", bearer=assistant)
        if state.get("workstationId") != expected:
            raise AssertionError("Assistant identity changed after restart")
        call("/api/patients/", bearer=assistant, expect=403)
        record("PASS", workstationHash=digest, identityPersisted=True,
               assistantPermissionDenied=True, assistantRole="SECRETAIRE",
               persona=("Assistante" if role == "C" else "Accueil"))
    else:
        record("PASS", workstationHash=digest, identityPersisted=True)
else:
    raise AssertionError("Unexpected cloud lab phase")
