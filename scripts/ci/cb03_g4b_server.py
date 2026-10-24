"""CB-03 G4-B CI-only actual FastAPI server with optional ACK withholding.

Only a fresh disposable loopback PostgreSQL database is permitted. Never run
against Neon, existing cabinet storage, production, or real patients.
"""
import asyncio
import os
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

u = urlsplit(os.environ.get("DATABASE_URL", ""))
head = os.environ.get("CB03_G4B_SOURCE_HEAD", "")
if not (
    os.environ.get("GITHUB_ACTIONS") == "true"
    and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
    and os.environ.get("CB03_G4B_SERVER") == "1"
    and os.environ.get("ENVIRONMENT") == "rehearsal"
    and u.scheme == "postgresql" and u.hostname == "127.0.0.1"
    and u.port == 5432 and u.path == "/cb03_g4b_disposable"
    and u.username == "cb03_g4b" and not u.query and not u.fragment
    and len(head) == 40 and all(c in "0123456789abcdef" for c in head)
    and subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == head
):
    raise RuntimeError("REFUSED: G4-B ephemeral PG-only exact-SHA server")

# All flags are enabled strictly inside this new CI-only worker subprocess;
# all outside processes must keep them OFF.
from backend.main import app as real_application

class WithholdCommittedAck:
    def __init__(self, wrapped):
        self.wrapped = wrapped

    async def __call__(self, scope, receive, send):
        if (scope["type"] == "http"
                and scope.get("path") == "/api/bot/guided/confirm"
                and scope.get("method") == "POST"
                and os.environ.get("CB03_G4B_WITHHOLD_ACK") == "1"):
            async def delayed_send(message):
                # FastAPI G2's route commits before returning the 200 response.
                # Kill the process AFTER the durable commit but BEFORE sending
                # HTTP response headers. This is not a mocked HTTP response.
                if message["type"] == "http.response.start" and message["status"] == 200:
                    marker = Path(os.environ["CB03_G4B_ACK_MARKER"])
                    marker.write_text("COMMITTED_BEFORE_ACK\n", encoding="utf-8")
                    await asyncio.Event().wait()
                await send(message)
            return await self.wrapped(scope, receive, delayed_send)
        return await self.wrapped(scope, receive, send)

app = WithholdCommittedAck(real_application)
