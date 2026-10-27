"""Real OS SIGKILL durability probe on a disposable encrypted SQLCipher file.

This certifies process death and disk recovery, NOT FastAPI/browser integration.
"""
import json
import os
import secrets
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from sqlcipher3 import dbapi2 as cipher

assert os.getenv("GITHUB_ACTIONS") == "true"
assert os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
head = os.getenv("CB03_G7_SOURCE_HEAD", "")
assert len(head) == 40 and subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == head

CHILD = r"""
import os,sys,time
from sqlcipher3 import dbapi2 as cipher
p,key,phase,ready=sys.argv[1:]
db=cipher.connect(p,timeout=10)
db.execute("PRAGMA key = \"x'%s'\"" % key)
db.execute("PRAGMA busy_timeout=10000")
if phase=="pre":
    db.execute("BEGIN IMMEDIATE")
    db.execute("UPDATE actions SET status='executed' WHERE id=1 AND status='prepared'")
    db.execute("INSERT INTO audit(action_id) VALUES(1)")
    open(ready,"w").write("uncommitted")
    while True: time.sleep(.1)
else:
    db.execute("BEGIN IMMEDIATE")
    db.execute("UPDATE actions SET status='executed' WHERE id=1 AND status='prepared'")
    db.execute("INSERT INTO audit(action_id) VALUES(1)")
    db.commit()
    open(ready,"w").write("committed-no-ack")
    while True: time.sleep(.1)
"""

def connect(path,key):
    db=cipher.connect(str(path),timeout=10)
    db.execute("PRAGMA key = \"x'%s'\"" % key)
    assert db.execute("PRAGMA cipher_version").fetchone()
    return db

def kill_case(path,key,phase,ready):
    proc=subprocess.Popen([sys.executable,"-c",CHILD,str(path),key,phase,str(ready)])
    try:
        deadline=time.monotonic()+20
        while not ready.exists() and proc.poll() is None and time.monotonic()<deadline:
            time.sleep(.05)
        assert ready.exists() and proc.poll() is None, "worker did not reach verified kill point"
        os.kill(proc.pid,signal.SIGKILL)
        assert proc.wait(timeout=10)==-signal.SIGKILL, "not a real SIGKILL"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)

with tempfile.TemporaryDirectory(prefix="cb03-g7-sigkill-sqlcipher-") as temp:
    path=Path(temp)/"synthetic-encrypted.db"
    key=secrets.token_hex(32)
    with connect(path,key) as db:
        db.execute("CREATE TABLE actions(id INTEGER PRIMARY KEY,status TEXT NOT NULL)")
        db.execute("CREATE TABLE audit(id INTEGER PRIMARY KEY,action_id INTEGER NOT NULL)")
        db.execute("INSERT INTO actions VALUES(1,'prepared')")
    kill_case(path,key,"pre",Path(temp)/"pre.ready")
    with connect(path,key) as db:
        assert db.execute("SELECT status FROM actions WHERE id=1").fetchone()[0]=="prepared"
        assert db.execute("SELECT COUNT(*) FROM audit").fetchone()[0]==0
    kill_case(path,key,"post",Path(temp)/"post.ready")
    with connect(path,key) as db:
        assert db.execute("SELECT status FROM actions WHERE id=1").fetchone()[0]=="executed"
        assert db.execute("SELECT COUNT(*) FROM audit").fetchone()[0]==1
        assert db.execute("UPDATE actions SET status='executed' WHERE id=1 AND status='prepared'").rowcount==0
        assert db.execute("SELECT COUNT(*) FROM audit").fetchone()[0]==1
    assert path.read_bytes()[:16]!=b"SQLite format 3\\x00"
    try:
        with sqlite3.connect(path) as db:
            db.execute("SELECT * FROM actions").fetchall()
    except sqlite3.DatabaseError:
        pass
    else:
        raise AssertionError("plaintext reader opened SQLCipher")
    wrong=connect(path,secrets.token_hex(32))
    try:
        try:
            wrong.execute("SELECT * FROM actions").fetchall()
        except cipher.DatabaseError:
            pass
        else:
            raise AssertionError("wrong key opened SQLCipher")
    finally:
        wrong.close()
    report={"head":head,"pre_commit":"REAL_SIGKILL_ROLLBACK","post_commit":"REAL_SIGKILL_DURABLE","audit_count":1,"encrypted_file":True,"scope":"SQLCipher process primitives; NOT browser/FastAPI end-to-end"}
    target=Path("artifacts/cb03-g7/sqlcipher-real-sigkill.json")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+"\\n")
    print("CB03_G7_REAL_SQLCIPHER_SIGKILL_PASS",json.dumps(report))
