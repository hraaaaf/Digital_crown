#!/usr/bin/env python3
"""Temporary, synthetic-only GitHub Actions iPhone validation gateway.

The browser must first open /session/<random capability>; every subsequent
request uses the short-lived Secure HttpOnly cookie. Never point this gateway
at a clinical/production instance.
"""
import hmac
import http.client
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

KEY_PATH = Path("/tmp/pocket-fue-gateway-session.json")
SESSION_KEY = secrets.token_urlsafe(32)
KEY_PATH.write_text(json.dumps({"key": SESSION_KEY}))
KEY_PATH.chmod(0o600)
COOKIE = f"pocket_fue={SESSION_KEY}"
HOST = "127.0.0.1"
PORT = 5183
TARGET_PORT = 5173
HOP_HEADERS = {
    "connection", "keep-alive", "transfer-encoding", "te", "trailer",
    "upgrade", "proxy-authenticate", "proxy-authorization",
}


class Gateway(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # Never emit the capability URL, session cookie or patient-like payloads.
        pass

    def answer(self, status: int, message: bytes, headers=None, content_type="text/plain; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(message)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for key, value in headers or []:
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(message)

    def dispatch(self):
        path = urlsplit(self.path).path
        if path == "/healthz":
            return self.answer(200, b"ok")
        if hmac.compare_digest(path, "/session/" + SESSION_KEY):
            # Some iOS Safari contexts do not retain Secure cookies on a
            # cross-app 302 chain. Commit the HttpOnly cookie on a real 200
            # first-party document and require a user navigation gesture.
            # Never downgrade to URL bearer auth for protected API calls.
            landing = """<!doctype html><html lang="fr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Session iPhone de test</title><style>
body{font-family:system-ui,sans-serif;max-width:460px;margin:18vh auto;padding:24px;color:#17253d}
a{display:block;text-align:center;background:#083781;color:white;border-radius:14px;
padding:18px;text-decoration:none;font-weight:700;min-height:26px}
p{line-height:1.5}</style></head><body>
<h1>Session de test prête</h1>
<p>Appuyez sur le bouton pour ouvrir Digital Crown dans Safari.
L'autorisation reste limitée à ce cabinet fictif et temporaire.</p>
<a href="/mobile/onboarding">Continuer vers l'appairage</a></body></html>"""
            return self.answer(200, landing.encode("utf-8"), [
                ("Set-Cookie", COOKIE + "; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=1500"),
                ("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'"),
            ], content_type="text/html; charset=utf-8")
        received = self.headers.get("Cookie", "")
        cookies = [cookie.strip() for cookie in received.split(";")]
        if not any(hmac.compare_digest(cookie, COOKIE) for cookie in cookies):
            return self.answer(403, b"Test session authorization required")
        # The public test endpoint exposes ONLY pairing claim + Pocket functions.
        # Administration, authentication, workstation and license APIs are
        # private to the 127.0.0.1 runner even after a session is authorized.
        if (path.startswith("/api/auth/")
            or path.startswith("/api/admin/")
            or path.startswith("/api/workstation/")
            or path in ("/api/mobile/bridge-pairing", "/api/mobile/bridge-options")
            or path.startswith("/api/backup")
            or path.startswith("/api/clinics/") and path != "/api/clinics/mobile-theme"):
            return self.answer(403, b"Test gateway: endpoint denied")

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1024 * 1024 or length < 0:
                return self.answer(413, b"Request too large")
            body = self.rfile.read(length) if length else None
            # Public frontend and test-only FastAPI share one HTTPS origin.
            # No backend port :8005 ever needs to be opened to the Internet.
            backend_path = path.startswith("/api/") or path in ("/stock/alerts", "/health")
            port = 8005 if backend_path else TARGET_PORT
            upstream = http.client.HTTPConnection(HOST, port, timeout=25)
            forward_headers = {
                key: value for key, value in self.headers.items()
                if key.lower() not in HOP_HEADERS and key.lower() not in {"host", "cookie"}
            }
            forward_headers["Host"] = f"{HOST}:{port}"
            forward_headers["X-Forwarded-Proto"] = "https"
            upstream.request(self.command, self.path, body=body, headers=forward_headers)
            response = upstream.getresponse()
            result = response.read()
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in HOP_HEADERS and key.lower() not in {
                    "content-length", "set-cookie", "access-control-allow-origin",
                    "access-control-allow-credentials",
                }:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(result)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(result)
            upstream.close()
        except Exception:
            self.answer(502, b"Temporary test backend unavailable")

    def do_GET(self):
        self.dispatch()

    def do_POST(self):
        self.dispatch()

    def do_PUT(self):
        self.dispatch()

    def do_PATCH(self):
        self.dispatch()

    def do_DELETE(self):
        self.dispatch()

    def do_OPTIONS(self):
        self.dispatch()

    def do_HEAD(self):
        self.dispatch()


if __name__ == "__main__":
    print("Pocket FUE gateway listening on 127.0.0.1:5183", flush=True)
    ThreadingHTTPServer((HOST, PORT), Gateway).serve_forever()
