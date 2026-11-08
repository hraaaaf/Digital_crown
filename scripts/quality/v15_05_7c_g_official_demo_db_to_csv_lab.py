"""LOT05.7C-G experimental REAL vendor-demo database-to-CSV LAB (no GUI).

Download only the SHA-pinned, previously Authenticode-verified official
Open Dental 25.3.48 trial, extract only its fictional demo.patient MyISAM
table, open in an isolated MariaDB 10.11 socket-only instance, and produce
a private ephemeral CSV. The CSV is never uploaded or printed. Metadata only.

Not Open Dental's own Patients-Raw GUI export. Not vendor format certification.
Not a Digital Crown importer, patient migration, clinic DB, deploy or API.
"""
from __future__ import annotations

import csv
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET


TRIAL_URL = "https://www.opendental.com/TrialDownload-25-3-48.exe"
EXPECTED_SHA256 = "b892db0d3b2fc0947fa25fe4fc07c2e81815d70119f72e7abf1f8b9b0671bcb9"
TRIPLE = re.compile(r"(?:^|[/\\])demo[/\\]patient\.(frm|MYD|MYI)$", re.I)
REPORT_NAME = "lot05-7c-g-vendor-demo-csv-evidence-only.json"


class LabRefused(Exception):
    """Stable error code only. No raw file paths, SQL errors or row values."""


def run(args: list[str], code: str, timeout: int = 100) -> bytes:
    try:
        result = subprocess.run(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise LabRefused(code) from None
    if result.returncode != 0:
        raise LabRefused(code)
    return result.stdout


def fetch_signed_pinned_exe(path: Path) -> None:
    digest = hashlib.sha256()
    size = 0
    try:
        req = urllib.request.Request(
            TRIAL_URL, headers={"User-Agent": "DigitalCrown-DemoEvidenceLab/1"}
        )
        with urllib.request.urlopen(req, timeout=60) as response, path.open("wb") as out:
            while data := response.read(1024 * 1024):
                size += len(data)
                if size > 400_000_000:
                    raise LabRefused("SIGNED_TRIAL_SIZE_LIMIT")
                digest.update(data)
                out.write(data)
    except LabRefused:
        raise
    except (OSError, TimeoutError, ValueError):
        raise LabRefused("SIGNED_TRIAL_DOWNLOAD_FAILED") from None
    if size != 149781424 or digest.hexdigest() != EXPECTED_SHA256:
        raise LabRefused("SIGNED_TRIAL_SHA256_OR_SIZE_MISMATCH")


def find_demo_patient_triplet(manifest: str) -> dict[str, str]:
    groups: dict[str, dict[str, str]] = {}
    for line in manifest.splitlines():
        if not line.startswith("Path = "):
            continue
        original = line[7:].strip()
        match = TRIPLE.search(original)
        if match is None:
            continue
        safe_path = original.replace("\\", "/").lower()
        if not re.fullmatch(r"[a-z0-9_./ -]{1,220}", safe_path) or ".." in safe_path:
            raise LabRefused("UNSAFE_SIGNED_ARCHIVE_MEMBER_PATH")
        prefix = safe_path.rsplit("/patient.", 1)[0]
        ext = match.group(1).lower()
        group = groups.setdefault(prefix, {})
        if ext in group:
            raise LabRefused("DUPLICATE_VENDOR_DEMO_TABLE_MEMBER")
        group[ext] = original
    candidates = [g for g in groups.values() if set(g) == {"frm", "myd", "myi"}]
    if not candidates:
        raise LabRefused("SIGNED_TRIAL_DEMO_PATIENT_TRIPLET_MISSING")
    if len(candidates) != 1:
        raise LabRefused("SIGNED_TRIAL_DEMO_PATIENT_TRIPLET_AMBIGUOUS")
    return candidates[0]


def start_private_mariadb(data: Path, socket: Path, log: Path) -> subprocess.Popen:
    cmd = [
        "mariadbd", "--no-defaults", f"--datadir={data}",
        f"--socket={socket}", f"--pid-file={data.parent / 'mariadb.pid'}",
        f"--log-error={log}", "--skip-networking",
        f"--user={getpass.getuser()}",
    ]
    try:
        server = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        raise LabRefused("PRIVATE_MARIADB_PROCESS_START_FAILED") from None
    for _ in range(80):
        if server.poll() is not None:
            raise LabRefused("PRIVATE_MARIADB_TERMINATED_EARLY")
        if socket.exists():
            try:
                sql(socket, "SELECT 1", timeout=3)
                return server
            except LabRefused:
                pass
        time.sleep(0.25)
    raise LabRefused("PRIVATE_MARIADB_SOCKET_READY_TIMEOUT")


def sql(socket: Path, query: str, *, xml: bool = False, timeout: int = 30) -> bytes:
    args = [
        "mariadb", "--no-defaults", "--protocol=socket", f"--socket={socket}",
        f"--user={getpass.getuser()}", "--default-character-set=utf8mb4",
    ]
    args += ["--xml"] if xml else ["--batch", "--skip-column-names"]
    return run(args + ["-e", query], "VENDOR_DEMO_READ_ONLY_SQL_FAILED", timeout)


def stop_private_mariadb(server: subprocess.Popen | None, socket: Path) -> None:
    if server is None or server.poll() is not None:
        return
    try:
        run(
            ["mariadb-admin", "--no-defaults", "--protocol=socket",
             f"--socket={socket}", f"--user={getpass.getuser()}", "shutdown"],
            "PRIVATE_MARIADB_SHUTDOWN_FAILED", 15,
        )
        server.wait(timeout=10)
    except (LabRefused, subprocess.TimeoutExpired):
        server.terminate()
        try:
            server.wait(timeout=4)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=4)


def private_csv_from_xml(xml: bytes, destination: Path) -> int:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        raise LabRefused("VENDOR_DEMO_XML_INVALID") from None
    rows = []
    seen = set()
    for record in root.findall("row"):
        values = {
            item.attrib.get("name"): item.text or ""
            for item in record.findall("field")
        }
        if set(values) != {"PatNum", "FName", "LName"}:
            raise LabRefused("VENDOR_DEMO_PATIENT_COLUMNS_UNEXPECTED")
        num = values["PatNum"]
        if not re.fullmatch(r"[1-9][0-9]{0,14}", num) or num in seen:
            raise LabRefused("VENDOR_DEMO_PATNUM_INVALID")
        seen.add(num)
        if any(not values[k].strip() or len(values[k]) > 255 for k in ("FName", "LName")):
            raise LabRefused("VENDOR_DEMO_NAME_INVALID")
        rows.append((num, values["FName"], values["LName"]))
    if not 1 <= len(rows) <= 30:
        raise LabRefused("VENDOR_DEMO_PATIENT_SAMPLE_COUNT_UNSAFE")
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["PatNum", "FName", "LName"])
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    report_dir = Path(os.environ.get("RUNNER_TEMP", "/tmp"))
    report = {
        "evidence_kind": "SIGNED_VENDOR_DEMO_PHYSICAL_MYISAM_TO_PRIVATE_CSV_NOT_GUI_EXPORT",
        "source_installer_sha256": EXPECTED_SHA256,
        "demo_file_triplet_verified": False,
        "candidate_csv_generated_privately": False,
        "candidate_csv_sha256": None,
        "candidate_csv_sample_rows": None,
        "publisher_gui_csv_export_verified": False,
        "source_provenance_verified_for_clinical_use": False,
        "vendor_format_compatible": False,
        "mapping_human_approved": False,
        "target_rows_written": 0,
        "import_permitted": False,
        "status": "NOT_RUN",
        "failure_code": None,
    }
    server = None
    with tempfile.TemporaryDirectory(prefix="lot05_7c_g_signed_demo_") as directory:
        lab = Path(directory)
        os.chmod(lab, 0o700)
        exe = lab / "signed_vendor_trial.exe"
        data = lab / "private_maria_data"
        sock = lab / "demo.sock"
        try:
            if sys.platform != "linux":
                raise LabRefused("ISOLATED_LINUX_GHA_REQUIRED")
            version = run(["mariadbd", "--version"], "PRIVATE_MARIADB_UNAVAILABLE")
            if not re.search(rb"10\.11\.", version):
                raise LabRefused("PRIVATE_MARIADB_10_11_REQUIRED")
            fetch_signed_pinned_exe(exe)
            raw = run(["7z", "l", "-slt", "-bd", str(exe)],
                      "VENDOR_SIGNED_ARCHIVE_MANIFEST_FAILED", 90)
            entries = find_demo_patient_triplet(raw.decode("utf-8", "replace"))
            report["demo_file_triplet_verified"] = True
            extracted = lab / "extracted_vendor_table"
            extracted.mkdir()
            run(
                ["7z", "e", "-y", "-bd", f"-o{extracted}", str(exe),
                 entries["frm"], entries["myd"], entries["myi"]],
                "VENDOR_TABLE_EXTRACTION_FAILED", 180,
            )
            table = {}
            for ext in ("frm", "myd", "myi"):
                matches = list(extracted.glob(f"patient.{ext}"))
                matches += list(extracted.glob(f"patient.{ext.upper()}"))
                matches = sorted(set(matches))
                if len(matches) != 1:
                    raise LabRefused("VENDOR_DEMO_PATIENT_FILE_UNAVAILABLE")
                f = matches[0]
                if not f.is_file() or not 0 < f.stat().st_size < 64 * 1024 * 1024:
                    raise LabRefused("VENDOR_DEMO_PATIENT_FILE_SIZE_UNSAFE")
                table[ext] = f
            run(
                ["mariadb-install-db", "--no-defaults", f"--datadir={data}",
                 "--auth-root-authentication-method=socket",
                 f"--auth-root-socket-user={getpass.getuser()}",
                 "--skip-test-db"],
                "PRIVATE_MARIADB_BOOTSTRAP_FAILED", 100,
            )
            server = start_private_mariadb(data, sock, lab / "mariadb.log")
            sql(sock, "CREATE DATABASE dc_vendor_demo")
            stop_private_mariadb(server, sock)
            server = None
            for ext, file in table.items():
                suffix = "frm" if ext == "frm" else ext.upper()
                shutil.copyfile(file, data / "dc_vendor_demo" / f"patient.{suffix}")
            server = start_private_mariadb(data, sock, lab / "mariadb.log")
            private_xml = sql(
                sock, "SELECT PatNum,FName,LName FROM dc_vendor_demo.patient ORDER BY PatNum LIMIT 30",
                xml=True,
            )
            csv_path = lab / "PRIVATE_VENDOR_DEMO_CSV_NEVER_UPLOAD.csv"
            nrows = private_csv_from_xml(private_xml, csv_path)
            report["candidate_csv_sha256"] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
            report["candidate_csv_sample_rows"] = nrows
            report["candidate_csv_generated_privately"] = True
            report["status"] = "VENDOR_DEMO_PHYSICAL_DB_CSV_CANDIDATE_ONLY_NOT_GUI_EXPORT"
            print("PINNED_VENDOR_DEMO_DB_TO_CSV_LOCAL_PROOF_SUCCESS")
        except LabRefused as exc:
            report["status"] = "REFUSED"
            report["failure_code"] = str(exc)
            print("VENDOR_DEMO_DB_LOCAL_CSV_REFUSED: " + str(exc))
        except Exception:
            report["status"] = "REFUSED"
            report["failure_code"] = "UNEXPECTED_ISOLATED_LAB_FAILURE"
            print("VENDOR_DEMO_DB_LOCAL_CSV_REFUSED: UNEXPECTED_ISOLATED_LAB_FAILURE")
        finally:
            stop_private_mariadb(server, sock)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / REPORT_NAME).write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8",
    )
    return 0 if report["candidate_csv_generated_privately"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
