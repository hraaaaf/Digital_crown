"""G8 disposable FastAPI wrapper: SQLite UDF pre-COMMIT pause + post-COMMIT lost ACK.

The real G2 route, ORM, transaction and encrypted SQLCipher engine remain
unchanged. Only a virgin, exact-path CI rehearsal may import this module.
"""
import asyncio
import os
import subprocess
import time
from pathlib import Path

head=os.environ.get("CB03_G8_SOURCE_HEAD","")
temp=Path(os.environ.get("RUNNER_TEMP","/nonexistent")).resolve()
db=temp/"cb03-g8-synthetic.db"
media=temp/"cb03-g8-rehearsal-media"
marker=temp/"cb03-g8-precommit.marker"
ack=temp/"cb03-g8-postcommit.marker"
if not (
    os.environ.get("GITHUB_ACTIONS")=="true"
    and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME")=="1"
    and os.environ.get("CB03_G8_SERVER")=="1"
    and os.environ.get("ENVIRONMENT")=="rehearsal"
    and os.environ.get("DATABASE_URL")=="sqlite:///"+str(db)
    and os.environ.get("MEDIA_ROOT")==str(media)
    and os.environ.get("SQLCIPHER_KEY_HEX")
    and os.environ.get("DIGITALCROWN_ISOLATION_DB_FINGERPRINT")
    and len(head)==40
    and subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()==head
    and db.is_file() and media.is_dir()
):
    raise RuntimeError("REFUSED: G8 only on exact virgin CI SQLCipher identity")

from backend import database
from sqlalchemy import event
assert database.engine.dialect.name=="sqlite" and "pysqlcipher" in database.engine.url.drivername

def pause_during_transaction():
    if os.environ.get("CB03_G8_HOLD_PRECOMMIT")!="1":
        raise RuntimeError("REFUSED: no explicit G8 precommit hold")
    if marker.exists():
        raise RuntimeError("REFUSED: marker already exists")
    marker.write_text("IN_G2_UNCOMMITTED_TRANSACTION\\n",encoding="utf-8")
    time.sleep(100)
    return 0

@event.listens_for(database.engine,"connect")
def register_g8_pause(dbapi_connection,connection_record):
    dbapi_connection.create_function("cb03_g8_precommit_pause",0,pause_during_transaction)

# CI opt-in must be set before importing real app; nothing in backend G2 is patched.
from backend.main import app as real_fastapi

class G8WithholdCommittedAck:
    def __init__(self,wrapped):
        self.wrapped=wrapped

    async def __call__(self,scope,receive,send):
        if (scope["type"]=="http"
            and scope.get("path")=="/api/bot/guided/confirm"
            and scope.get("method")=="POST"
            and os.environ.get("CB03_G8_WITHHOLD_ACK")=="1"):
            async def delayed(message):
                if message["type"]=="http.response.start" and message["status"]==200:
                    if ack.exists():
                        raise RuntimeError("REFUSED: duplicate G8 commit marker")
                    ack.write_text("COMMITTED_BEFORE_ACK\\n",encoding="utf-8")
                    await asyncio.Event().wait()
                await send(message)
            return await self.wrapped(scope,receive,delayed)
        return await self.wrapped(scope,receive,send)

app=G8WithholdCommittedAck(real_fastapi)
