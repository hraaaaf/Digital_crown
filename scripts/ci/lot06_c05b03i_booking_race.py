"""C05B-03I — two true SQLite connections invoking the real cabinet booking lock.
Disposable DB; no patient data, network, API or product certification.
"""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
import importlib.util
import tempfile
import time
import json
import os

def main():
    assert os.getenv("ENVIRONMENT") == "test", "TEST_ONLY"
    assert os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "true", "ISOLATED_ONLY"
    assert os.getenv("C05B03H_NETWORK_POLICY_APPROVED", "false") == "false", "NETWORK_GATE_MUST_REMAIN_FALSE"
    path = Path(__file__).resolve().parents[2] / "backend/services/agenda_transaction_lock.py"
    assert path.is_file()
    spec = importlib.util.spec_from_file_location("dc06i_actual_lock", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    lock = mod.lock_cabinet_booking
    with tempfile.TemporaryDirectory(prefix="dc06i-db-") as folder:
        engine = create_engine("sqlite:///" + str(Path(folder) / "test.db"),
            connect_args={"timeout": 10, "check_same_thread": False}, poolclass=NullPool)
        md = MetaData()
        t = Table("appointments", md,
            Column("id", Integer, primary_key=True),
            Column("employer_id", Integer, nullable=False),
            Column("praticien_id", Integer, nullable=False),
            Column("datetime_start", String(32), nullable=False),
            Column("patient_id", String(32), nullable=False))
        md.create_all(engine)
        for round_number in range(12):
            with engine.begin() as conn:
                conn.execute(t.delete())
            barrier = Barrier(2)
            def contender(patient):
                with Session(engine) as db:
                    barrier.wait(timeout=10)
                    lock(db, 941121)
                    occupied = db.execute(select(t.c.id).where(
                        t.c.employer_id == 941121,
                        t.c.praticien_id == 5,
                        t.c.datetime_start == "2030-02-14T10:00:00")).first()
                    if occupied:
                        db.rollback()
                        return "CONFLICT"
                    time.sleep(0.025)
                    db.execute(t.insert().values(employer_id=941121, praticien_id=5,
                        datetime_start="2030-02-14T10:00:00", patient_id=patient))
                    db.commit()
                    return "COMMITTED"
            with ThreadPoolExecutor(max_workers=2) as pool:
                a = pool.submit(contender, "A")
                b = pool.submit(contender, "B")
                result = sorted((a.result(timeout=15), b.result(timeout=15)))
            assert result == ["COMMITTED", "CONFLICT"], (round_number, result)
            with engine.connect() as conn:
                assert len(conn.execute(select(t.c.id)).all()) == 1
        with engine.begin() as conn:
            conn.execute(t.delete())
        with Session(engine) as db:
            lock(db, 941121)
            db.execute(t.insert().values(employer_id=941121, praticien_id=5,
                datetime_start="2030-02-14T10:00:00", patient_id="ABORT"))
            db.rollback()
        with engine.connect() as conn:
            assert not conn.execute(select(t.c.id)).all()
        engine.dispose()
    return dict(marker="C05B03I_REAL_SQLITE_TWO_CONNECTION_LOCK_RACE_PASS",
        rounds=12, separate_sessions=True, real_production_lock=True,
        no_slot_unique_constraint=True, rollback_no_ack=True, product_ready=False)

if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True))
