from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

SOURCE_USER_VERSION = 909
PROBE_TABLE = "p9_probe"
PROBE_MEDIA_RELATIVE = Path("p9-proof") / "sentinel.bin"


class P9CertificationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def configure_common(data_dir: Path, media_root: Path, port: int, *, cabinet: bool) -> dict[str, str]:
    data_dir = data_dir.resolve()
    media_root = media_root.resolve()
    for key in (
        "DATABASE_URL",
        "DIGITALCROWN_DR_DESTINATION",
        "DIGITALCROWN_DR_SECRET",
        "DIGITALCROWN_DR_KEEP",
    ):
        os.environ.pop(key, None)
    os.environ.update(
        {
            "ENVIRONMENT": "cabinet" if cabinet else "p9_cert_source",
            "DIGITALCROWN_USER_DATA_DIR": str(data_dir),
            "DIGITALCROWN_CONFIG_DIR": str(data_dir),
            "DIGITALCROWN_LOG_DIR": str(data_dir / "logs"),
            "DIGITALCROWN_RUNTIME_DIR": str(data_dir / "runtime"),
            "DIGITALCROWN_ENV_FILE": str(data_dir / ".env"),
            "MEDIA_ROOT": str(media_root),
            "CABINET_PORT": str(port),
            "ALLOWED_ORIGINS": f"http://127.0.0.1:{port}",
        }
    )
    return os.environ


def ensure_strong_keys(*, source: bool) -> tuple[str, str]:
    master = ("11" if source else "22") * 32
    secret = (
        "DigitalCrown-P9-Source-Secret-Key-For-CI-Only-2026"
        if source
        else "DigitalCrown-P9-Target-Secret-Key-For-CI-Only-2026"
    )
    os.environ["CABINET_MASTER_KEY_HEX"] = master
    os.environ["SECRET_KEY"] = secret
    return master, secret


def create_source_fixture(data_dir: Path, media_root: Path, source_label: str) -> tuple[str, str]:
    from backend import database, models

    models.Base.metadata.create_all(bind=database.engine)
    with database.SessionLocal() as session:
        owner = models.User(
            email=f"p9-{source_label}@example.invalid",
            hashed_password="p9-ci-not-a-login-secret",
            role=models.UserRole.ADMIN,
            is_licensed=True,
            nom_complet=f"P9 {source_label} owner",
        )
        session.add(owner)
        session.flush()
        cabinet = models.CabinetConfig(
            owner_id=owner.id,
            public_id=("p9winproof000001" if source_label == "windows" else "p9macproof000001"),
            clinic_id=("p9-win-clinic" if source_label == "windows" else "p9-mac-clinic"),
            nom_cabinet=f"P9 {source_label} cabinet",
            nom_praticien=f"P9 {source_label} owner",
            is_initialized=True,
        )
        session.add(cabinet)
        session.commit()

    marker = f"P9-OFFMACHINE-{source_label.upper()}-TO-OTHER-OS"
    with database.engine.begin() as conn:
        conn.exec_driver_sql(
            f"CREATE TABLE IF NOT EXISTS {PROBE_TABLE} "
            "(marker TEXT PRIMARY KEY, source_os TEXT NOT NULL)"
        )
        conn.exec_driver_sql(f"DELETE FROM {PROBE_TABLE}")
        conn.exec_driver_sql(
            f"INSERT INTO {PROBE_TABLE}(marker, source_os) VALUES (?, ?)",
            (marker, source_label),
        )
        conn.exec_driver_sql(f"PRAGMA user_version = {SOURCE_USER_VERSION}")

    media_path = media_root / PROBE_MEDIA_RELATIVE
    media_path.parent.mkdir(parents=True, exist_ok=True)
    media_bytes = f"Digital Crown P9 media proof from {source_label}\n".encode("utf-8")
    media_path.write_bytes(media_bytes)
    return marker, hashlib.sha256(media_bytes).hexdigest()


def source_mode(args: argparse.Namespace) -> int:
    transfer_dir = Path(args.transfer_dir).resolve()
    work_root = Path(args.work_root).resolve()
    data_dir = work_root / "source-cabinet"
    media_root = work_root / "source-media"
    transfer_dir.mkdir(parents=True, exist_ok=False)
    data_dir.mkdir(parents=True, exist_ok=True)
    media_root.mkdir(parents=True, exist_ok=True)

    configure_common(data_dir, media_root, args.port, cabinet=False)
    master, _ = ensure_strong_keys(source=True)
    os.environ["DIGITALCROWN_DR_DESTINATION"] = str(transfer_dir)
    os.environ["DIGITALCROWN_DR_SECRET"] = args.migration_secret
    os.environ["DIGITALCROWN_DR_KEEP"] = "3"

    marker, media_sha = create_source_fixture(data_dir, media_root, args.source_label)

    from backend.core.platform import get_platform_adapter
    from backend.services.disaster_recovery_service import DisasterRecoveryService

    adapter = get_platform_adapter()
    if adapter.kind not in {"windows", "macos"}:
        raise P9CertificationError(f"UNSUPPORTED_SOURCE_OS {adapter.kind}")
    if adapter.kind != args.source_label:
        raise P9CertificationError(
            f"SOURCE_LABEL_MISMATCH expected={args.source_label} actual={adapter.kind}"
        )

    result = DisasterRecoveryService.create_verified_snapshot()
    if result.get("status") != "SUCCESS" or result.get("verified_restore_path") is not True:
        raise P9CertificationError(f"DR_SNAPSHOT_FAILED {result}")

    bundle_name = str(result.get("bundle_filename") or "")
    bundle = transfer_dir / bundle_name
    sidecar = transfer_dir / f"{bundle_name}.sha256"
    if not bundle.is_file() or not sidecar.is_file():
        raise P9CertificationError("DR_BUNDLE_OR_SIDECAR_MISSING")
    actual_sha = sha256_file(bundle)
    if actual_sha != str(result.get("sha256") or ""):
        raise P9CertificationError("DR_RESULT_SHA256_MISMATCH")
    expected_sidecar = f"{actual_sha}  {bundle.name}\n"
    if sidecar.read_text(encoding="utf-8") != expected_sidecar:
        raise P9CertificationError("DR_SIDECAR_MISMATCH")

    proof = {
        "format": "digitalcrown-p9-offmachine-source-proof-v1",
        "source_os": adapter.kind,
        "source_architecture": adapter.architecture,
        "source_label": args.source_label,
        "bundle_filename": bundle.name,
        "bundle_sha256": actual_sha,
        "sidecar_filename": sidecar.name,
        "sidecar_verified": True,
        "verified_restore_path": True,
        "probe_marker": marker,
        "probe_user_version": SOURCE_USER_VERSION,
        "media_relative_path": PROBE_MEDIA_RELATIVE.as_posix(),
        "media_sha256": media_sha,
        "source_master_fingerprint": hashlib.sha256(master.encode("ascii")).hexdigest(),
        "machine_bound_excluded_expected": [
            ".env",
            "backup.key",
            "license_vault.bin",
            "runtime locks",
            "logs",
            "caches",
        ],
    }
    write_json(transfer_dir / "source-proof.json", proof)
    print(
        "P9_SOURCE_SNAPSHOT=SUCCESS "
        f"os={adapter.kind} bundle_sha256={actual_sha} sidecar=verified"
    )
    return 0


def run_checked(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise P9CertificationError(
            f"COMMAND_FAILED rc={result.returncode} cmd={argv} "
            f"stdout={result.stdout[-3000:]} stderr={result.stderr[-3000:]}"
        )
    return result


def run_package_self_test(executable: Path, env: dict[str, str], report: Path) -> dict[str, Any]:
    local_env = env.copy()
    local_env["DIGITALCROWN_PACKAGE_SELF_TEST_REPORT"] = str(report)
    report.unlink(missing_ok=True)
    run_checked([str(executable), "--package-self-test"], cwd=executable.parent, env=local_env, timeout=180)
    if not report.is_file():
        raise P9CertificationError("PACKAGE_SELF_TEST_REPORT_MISSING")
    payload = json.loads(report.read_text(encoding="utf-8"))
    required = (
        payload.get("status") == "ok",
        payload.get("frozen") is True,
        not payload.get("missing"),
        not payload.get("forbidden_present"),
        not payload.get("unqualified_scientific_weights_present"),
        payload.get("scientific_manifest_policy_ok") is True,
        payload.get("scientific_capabilities") == "FAIL_CLOSED_NO_WEIGHTS",
    )
    if not all(required):
        raise P9CertificationError(f"PACKAGE_SELF_TEST_TRUTH_FAILED {payload}")
    return payload


def wait_health(port: int, *, process: subprocess.Popen[bytes] | None = None, timeout: int = 120) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/health"
    last_error = "not_started"
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise P9CertificationError(f"RUNTIME_EXITED_BEFORE_HEALTH rc={process.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if response.status == 200 and payload.get("status") == "ok" and payload.get("db") == "ok":
                return payload
            last_error = f"payload={payload}"
        except (OSError, ValueError, urllib.error.URLError) as exc:
            last_error = f"{type(exc).__name__}:{exc}"
        time.sleep(0.5)
    raise P9CertificationError(f"RUNTIME_HEALTH_TIMEOUT url={url} last={last_error}")


def stop_process_tree(process: subprocess.Popen[bytes] | None) -> None:
    if process is None:
        return
    try:
        import psutil

        root = psutil.Process(process.pid)
        children = root.children(recursive=True)
        for child in children:
            child.terminate()
        root.terminate()
        _, alive = psutil.wait_procs(children + [root], timeout=10)
        for item in alive:
            item.kill()
    except Exception:
        try:
            process.terminate()
            process.wait(timeout=10)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


def stop_matching_executable(executable: Path) -> None:
    try:
        import psutil
    except Exception:
        return
    target = str(executable.resolve()).lower()
    for proc in psutil.process_iter(["pid", "exe", "cmdline"]):
        if proc.pid == os.getpid():
            continue
        try:
            exe = str(proc.info.get("exe") or "").lower()
            cmdline = [str(value).lower() for value in (proc.info.get("cmdline") or [])]
            if exe == target or (cmdline and cmdline[0] == target):
                proc.kill()
        except Exception:
            continue


def start_runtime(executable: Path, env: dict[str, str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [str(executable)],
        cwd=str(executable.parent),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def parse_sidecar(bundle: Path, sidecar: Path) -> str:
    raw = sidecar.read_text(encoding="utf-8")
    suffix = f"  {bundle.name}\n"
    if not raw.endswith(suffix):
        raise P9CertificationError("SIDECAR_FORMAT_INVALID")
    digest = raw[: -len(suffix)]
    if len(digest) != 64:
        raise P9CertificationError("SIDECAR_DIGEST_INVALID")
    return digest


def assert_wrong_secret_rejected(bundle: Path, work_root: Path) -> None:
    from backend.services.cabinet_bundle import CabinetBundleService

    target = work_root / "wrong-secret-guided-restore.zip"
    try:
        CabinetBundleService.to_local_guided_restore_archive(
            bundle,
            "Definitely-Wrong-P9-Migration-Secret-2026",
            target,
        )
    except (ValueError, RuntimeError):
        target.unlink(missing_ok=True)
        return
    raise P9CertificationError("WRONG_MIGRATION_SECRET_ACCEPTED")


def tampered_bundle_copy(bundle: Path, target: Path) -> Path:
    with zipfile.ZipFile(bundle, "r") as source:
        manifest = source.read("manifest.json")
        payload = bytearray(source.read("payload.enc"))
    if not payload:
        raise P9CertificationError("EMPTY_CIPHERTEXT")
    payload[len(payload) // 2] ^= 0x01
    target.unlink(missing_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("manifest.json", manifest)
        archive.writestr("payload.enc", bytes(payload))
    return target


def assert_tamper_rejected(bundle: Path, migration_secret: str, work_root: Path) -> None:
    from backend.services.cabinet_bundle import CabinetBundleService

    tampered = tampered_bundle_copy(bundle, work_root / "tampered.dcbundle")
    target = work_root / "tampered-guided-restore.zip"
    try:
        CabinetBundleService.to_local_guided_restore_archive(tampered, migration_secret, target)
    except (ValueError, RuntimeError):
        target.unlink(missing_ok=True)
        return
    raise P9CertificationError("TAMPERED_BUNDLE_ACCEPTED")


def verify_restored_sqlcipher(data_dir: Path, master_key: str, source_proof: dict[str, Any]) -> dict[str, Any]:
    from sqlcipher3 import dbapi2 as sqlcipher

    db_path = data_dir / "clinical_vault.db"
    if not db_path.is_file():
        raise P9CertificationError("RESTORED_DATABASE_MISSING")
    conn = sqlcipher.connect(str(db_path))
    try:
        safe_key = master_key.replace("'", "''")
        conn.execute(f"PRAGMA key = '{safe_key}'")
        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        if not integrity or str(integrity[0]).lower() != "ok":
            raise P9CertificationError("RESTORED_DATABASE_INTEGRITY_FAILED")
        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        row = conn.execute(f"SELECT marker, source_os FROM {PROBE_TABLE}").fetchone()
        target_only = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='p9_target_only'"
        ).fetchone()
    finally:
        conn.close()
    if user_version != int(source_proof["probe_user_version"]):
        raise P9CertificationError(f"RESTORED_USER_VERSION_MISMATCH {user_version}")
    if not row or str(row[0]) != str(source_proof["probe_marker"]):
        raise P9CertificationError(f"RESTORED_PROBE_MISMATCH {row}")
    if target_only is not None:
        raise P9CertificationError("TARGET_ONLY_SENTINEL_SURVIVED_RESTORE")
    return {"probe_marker": row[0], "source_os": row[1], "user_version": user_version}


def target_mode(args: argparse.Namespace) -> int:
    transfer_dir = Path(args.transfer_dir).resolve()
    work_root = Path(args.work_root).resolve()
    executable = Path(args.executable).resolve()
    data_dir = work_root / "target-cabinet"
    media_root = work_root / "target-media"
    work_root.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    media_root.mkdir(parents=True, exist_ok=True)

    configure_common(data_dir, media_root, args.port, cabinet=True)
    target_master, _ = ensure_strong_keys(source=False)
    os.environ["DIGITALCROWN_RESTORE_RESTART"] = "1"
    env = os.environ.copy()

    if not executable.is_file():
        raise P9CertificationError(f"PACKAGED_EXECUTABLE_MISSING {executable}")

    bundles = list(transfer_dir.glob("*.dcbundle"))
    proofs = list(transfer_dir.glob("source-proof.json"))
    if len(bundles) != 1 or len(proofs) != 1:
        raise P9CertificationError(
            f"TRANSFER_CONTENT_INVALID bundles={len(bundles)} proofs={len(proofs)}"
        )
    bundle = bundles[0]
    sidecar = transfer_dir / f"{bundle.name}.sha256"
    if not sidecar.is_file():
        raise P9CertificationError("TRANSFER_SIDECAR_MISSING")
    source_proof = json.loads(proofs[0].read_text(encoding="utf-8"))
    target_os = "windows" if sys.platform.startswith("win") else "macos" if sys.platform == "darwin" else sys.platform
    if source_proof.get("source_os") == target_os:
        raise P9CertificationError(
            f"CROSS_OS_BOUNDARY_NOT_PROVED source={source_proof.get('source_os')} target={target_os}"
        )
    sidecar_sha = parse_sidecar(bundle, sidecar)
    actual_sha = sha256_file(bundle)
    if actual_sha != sidecar_sha or actual_sha != str(source_proof.get("bundle_sha256") or ""):
        raise P9CertificationError("TRANSFER_SHA256_MISMATCH")
    if hashlib.sha256(target_master.encode("ascii")).hexdigest() == source_proof.get(
        "source_master_fingerprint"
    ):
        raise P9CertificationError("SOURCE_AND_TARGET_MASTER_KEYS_MUST_DIFFER")

    package_self_test = run_package_self_test(
        executable, env, work_root / "package-self-test.json"
    )
    runtime = start_runtime(executable, env)
    try:
        initial_health = wait_health(args.port, process=runtime, timeout=180)
    finally:
        stop_process_tree(runtime)
    time.sleep(1.0)

    from backend import database

    with database.engine.begin() as conn:
        conn.exec_driver_sql(
            "CREATE TABLE IF NOT EXISTS p9_target_only "
            "(marker TEXT PRIMARY KEY)"
        )
        conn.exec_driver_sql("DELETE FROM p9_target_only")
        conn.exec_driver_sql(
            "INSERT INTO p9_target_only(marker) VALUES ('TARGET-MUST-DISAPPEAR')"
        )

    assert_wrong_secret_rejected(bundle, work_root)
    assert_tamper_rejected(bundle, args.migration_secret, work_root)

    from backend.services.cabinet_bundle import CabinetBundleService
    from backend.services.guided_restore import GuidedRestoreService

    local_restore = work_root / "guided-restore-from-offmachine.zip"
    converted = CabinetBundleService.to_local_guided_restore_archive(
        bundle,
        args.migration_secret,
        local_restore,
    )
    if not local_restore.is_file() or local_restore.stat().st_size <= 0:
        raise P9CertificationError("GUIDED_RESTORE_CONVERSION_MISSING")

    preflight = GuidedRestoreService.preflight_file(
        local_restore,
        original_name=bundle.name,
    )
    if preflight.get("status") != "preflight_ready" or not preflight.get("compatible"):
        raise P9CertificationError(f"GUIDED_RESTORE_PREFLIGHT_FAILED {preflight}")
    restore_id = str(preflight["restore_id"])
    prepared = GuidedRestoreService.prepare(restore_id)
    if prepared.get("status") != "prepared":
        raise P9CertificationError(f"GUIDED_RESTORE_PREPARE_FAILED {prepared}")

    database.engine.dispose()

    parent = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(180)"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    worker = subprocess.Popen(
        [
            str(executable),
            "--guided-restore-worker",
            restore_id,
            "--parent-pid",
            str(parent.pid),
        ],
        cwd=str(executable.parent),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(1.0)
        parent.terminate()
        try:
            parent.wait(timeout=10)
        except subprocess.TimeoutExpired:
            parent.kill()
            parent.wait(timeout=10)
        worker_rc = worker.wait(timeout=240)
    finally:
        if parent.poll() is None:
            parent.kill()
        if worker.poll() is None:
            worker.kill()
        try:
            parent.wait(timeout=5)
        except Exception:
            pass
        try:
            worker.wait(timeout=5)
        except Exception:
            pass

    job = GuidedRestoreService.get_job(restore_id)
    if worker_rc != 0:
        raise P9CertificationError(f"FROZEN_RESTORE_WORKER_FAILED rc={worker_rc} job={job}")
    if (
        job.get("status") != "success"
        or job.get("smoke_check") != "passed"
        or job.get("rollback") != "not_needed"
    ):
        raise P9CertificationError(f"FROZEN_RESTORE_TRUTH_FAILED {job}")

    restored_health = wait_health(args.port, timeout=60)
    db_proof = verify_restored_sqlcipher(data_dir, target_master, source_proof)
    media_path = media_root / Path(str(source_proof["media_relative_path"]))
    if not media_path.is_file():
        raise P9CertificationError("RESTORED_MEDIA_MISSING")
    media_sha = sha256_file(media_path)
    if media_sha != str(source_proof["media_sha256"]):
        raise P9CertificationError("RESTORED_MEDIA_SHA256_MISMATCH")

    report = {
        "format": "digitalcrown-p9-offmachine-target-proof-v1",
        "source_os": source_proof.get("source_os"),
        "target_os": target_os,
        "bundle_sha256": actual_sha,
        "off_runner_transfer_sha256_verified": True,
        "wrong_secret_rejected": True,
        "tamper_rejected": True,
        "package_self_test": package_self_test,
        "initial_health": initial_health,
        "guided_restore_source": converted.get("source"),
        "restore_worker": "frozen-packaged-executable",
        "restore_job_status": job.get("status"),
        "restore_smoke_check": job.get("smoke_check"),
        "restore_rollback": job.get("rollback"),
        "restored_health": restored_health,
        "database": db_proof,
        "media_sha256": media_sha,
    }
    write_json(Path(args.report).resolve(), report)
    print(
        "P9_OFFMACHINE_PACKAGED_RESTORE=SUCCESS "
        f"source={source_proof.get('source_os')} target={target_os} "
        f"bundle_sha256={actual_sha}"
    )
    stop_matching_executable(executable)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    source = sub.add_parser("source")
    source.add_argument("--transfer-dir", required=True)
    source.add_argument("--work-root", required=True)
    source.add_argument("--migration-secret", required=True)
    source.add_argument("--source-label", required=True, choices=("windows", "macos"))
    source.add_argument("--port", type=int, default=18910)

    target = sub.add_parser("target")
    target.add_argument("--transfer-dir", required=True)
    target.add_argument("--work-root", required=True)
    target.add_argument("--migration-secret", required=True)
    target.add_argument("--executable", required=True)
    target.add_argument("--report", required=True)
    target.add_argument("--port", required=True, type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.mode == "source":
        return source_mode(args)
    if args.mode == "target":
        try:
            return target_mode(args)
        finally:
            stop_matching_executable(Path(args.executable))
    raise AssertionError(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
