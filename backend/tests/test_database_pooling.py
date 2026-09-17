import os
import subprocess
import sys


def test_file_backed_sqlite_uses_queue_pool(tmp_path):
    db_path = tmp_path / "pool-contract.db"
    code = r"""
import os
from sqlalchemy.pool import QueuePool

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///" + os.environ["POOL_CONTRACT_DB"]
os.environ["SECRET_KEY"] = "pool-contract-secret-key-minimum-32chars"
os.environ["TELEMETRY_ENABLED"] = "false"
os.environ["CLOUD_AI_ENABLED"] = "false"

from backend import database

assert isinstance(database.engine.pool, QueuePool), type(database.engine.pool).__name__
"""
    env = os.environ.copy()
    env["POOL_CONTRACT_DB"] = str(db_path)
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=os.getcwd(),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
