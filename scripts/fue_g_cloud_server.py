"""Isolated FUE-G CLOUD-LAB transport wrapper. NEVER a cabinet installer/runtime.

Reuses the real T2 synthetic FastAPI app with its ephemeral SQLite store while
enforcing the *real* cabinet topology TLS contract on an ephemeral Docker host
bridge endpoint. Test-only ENVIRONMENT=test remains owned by the T2 harness.
"""
import os
import runpy
from pathlib import Path

if os.environ.get("T2_CLOUD_LAB") != "1":
    raise SystemExit("Cloud lab requires explicit T2_CLOUD_LAB=1")
if os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "1":
    raise SystemExit("Refusing any non-isolated runtime")

from backend.core.cabinet_topology import resolve_cabinet_network
import uvicorn

# Evaluate transport as cabinet, but execute synthetic T2 test mode; never claim
# that this proves SQLCipher/PostgreSQL, packaged runtime or Windows installation.
contract = resolve_cabinet_network({**os.environ, "ENVIRONMENT": "cabinet"})
if (
    contract.port != 8005
    or not contract.lan_exposed
    or not contract.https_enabled
    or not contract.tls_ready
    or contract.host in ("0.0.0.0", "::")
):
    raise SystemExit("Cloud lab requires explicitly bound, TLS-protected bridge endpoint")

original_uvicorn_run = uvicorn.run

def tls_run(app, **kwargs):
    if kwargs.get("host") != "127.0.0.1" or kwargs.get("port") != 8005:
        raise RuntimeError("T2 harness unexpectedly changed, refusing cloud TLS wrapper")
    return original_uvicorn_run(
        app,
        host=contract.host,
        port=contract.port,
        ssl_certfile=contract.cert_file,
        ssl_keyfile=contract.key_file,
        log_level="warning",
    )

uvicorn.run = tls_run
runpy.run_path(
    str(Path(__file__).with_name("t2_runtime_server.py")),
    run_name="__main__",
)
