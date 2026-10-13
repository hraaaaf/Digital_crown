#!/usr/bin/env python3
"""LOT04.8-C LAB: physical spool protocol, virtual printer only.

NO patient records, archive downloads, clinical API, print endpoints, print
permissions or physical printer are used. GitHub runner sends a one-page
synthetic PostScript to CUPS-PDF and proves the resulting PDF was processed
by the virtual printer (not just created by the test script).
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

VIRTUAL_QUEUE = "DC_VIRTUAL_PDF"
ABSENT_QUEUE = "DC_NOT_INSTALLED_NO_FALLBACK"
SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
RUN_PATTERN = re.compile(r"[0-9]{1,24}\Z")
JOB_PATTERN = re.compile(r"request id is (DC_VIRTUAL_PDF-[0-9]+) \(1 file\(s\)\)")


def command(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, capture_output=True, text=True, timeout=30)


def pdf_roots() -> list[Path]:
    return [
        Path.home() / "PDF",
        Path("/var/spool/cups-pdf/ANONYMOUS"),
        Path("/var/spool/cups-pdf/runner"),
    ]


def pdf_files() -> set[Path]:
    files: set[Path] = set()
    for root in pdf_roots():
        if root.is_dir():
            try:
                files.update(p.resolve() for p in root.rglob("*.pdf") if p.is_file())
                files.update(p.resolve() for p in root.rglob("*.PDF") if p.is_file())
            except PermissionError:
                # The test cannot certify a file it has no permission to read.
                pass
    return files


def check_spool_identity() -> str:
    output = command("lpstat", "-v", VIRTUAL_QUEUE).stdout
    # Do not fall back to a default, network or real printer.
    if "cups-pdf:/" not in output or VIRTUAL_QUEUE not in output:
        raise AssertionError(f"printer is not a CUPS-PDF virtual queue: {output!r}")
    return output.strip()


def render_synthetic_ps(path: Path, marker: str) -> None:
    # Marker has a strictly validated ASCII alphabet, safe in PostScript
    # parentheses. The proof contains no PHI or real names.
    assert re.fullmatch(r"[A-Z0-9_]+", marker), marker
    path.write_text(
        "%!PS-Adobe-3.0\n"
        "%%Pages: 1\n"
        "%%DocumentData: Clean7Bit\n"
        "%%EndComments\n"
        "<< /PageSize [595 842] >> setpagedevice\n"
        "/Courier findfont 14 scalefont setfont\n"
        "64 740 moveto (DIGITAL CROWN SYNTHETIC PRINT LAB) show\n"
        f"64 700 moveto ({marker}) show\n"
        "64 670 moveto (NO PATIENT DATA - NOT A REAL PRINTER) show\n"
        "showpage\n"
        "%%EOF\n",
        encoding="ascii",
    )


def main() -> int:
    sha = os.environ.get("GITHUB_SHA_SOURCE", "").lower()
    run = os.environ.get("GITHUB_RUN_ID", "")
    if not SHA_PATTERN.fullmatch(sha) or not RUN_PATTERN.fullmatch(run):
        raise AssertionError("exact GitHub HEAD/run identity required")
    marker = f"DC048_VIRTUAL_{run}_{sha[:12].upper()}"
    workspace = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
    artifacts = workspace / "print-lab-artifacts"
    artifacts.mkdir(exist_ok=True)
    ps_file = artifacts / "synthetic-source.ps"
    render_synthetic_ps(ps_file, marker)
    virtual_uri = check_spool_identity()
    before = pdf_files()

    # A missing target must be rejected; never send a job to the OS default.
    missing = command("lp", "-d", ABSENT_QUEUE, str(ps_file), check=False)
    if missing.returncode == 0:
        raise AssertionError("unknown printer was unexpectedly accepted")

    submitted = command(
        "lp", "-d", VIRTUAL_QUEUE, "-t", marker,
        "-o", "job-sheets=none", str(ps_file),
    )
    job = JOB_PATTERN.search(submitted.stdout)
    if not job:
        raise AssertionError(f"no CUPS job id returned: {submitted.stdout!r}")
    job_id = job.group(1)

    created: list[Path] = []
    deadline = time.monotonic() + 50
    while time.monotonic() < deadline:
        created = sorted(pdf_files() - before)
        valid = [
            file for file in created
            if file.stat().st_size > 100
            and file.read_bytes().startswith(b"%PDF-")
        ]
        if valid:
            break
        time.sleep(0.5)
    else:
        raise AssertionError(
            "CUPS accepted job but no PDF emitted by the virtual printer; "
            "this is NOT a proven print"
        )

    if len(valid) != 1:
        raise AssertionError(f"expected exactly one virtual output, found {len(valid)}")
    printed = valid[0]
    info = command("pdfinfo", str(printed)).stdout
    pages = re.search(r"^Pages:\s+(\d+)\s*$", info, flags=re.M)
    if not pages or pages.group(1) != "1":
        raise AssertionError(f"wrong page count from real CUPS-PDF output: {info!r}")
    text = command("pdftotext", "-layout", str(printed), "-").stdout
    if marker not in text or "NO PATIENT DATA" not in text:
        raise AssertionError(f"virtual spool PDF content mismatch: {text[:300]!r}")

    proof_pdf = artifacts / "spooler-output.pdf"
    shutil.copyfile(printed, proof_pdf)
    digest = hashlib.sha256(proof_pdf.read_bytes()).hexdigest()
    proof = {
        "scope": "GITHUB_ACTIONS_SYNTHETIC_CUPS_PDF_ONLY",
        "exact_head_sha": sha,
        "run_id": run,
        "queue": VIRTUAL_QUEUE,
        "device": virtual_uri,
        "rejected_unknown_queue": True,
        "cups_job_id": job_id,
        "spool_output_created": True,
        "pdf_pages": 1,
        "expected_marker": marker,
        "marker_verified_in_spool_output": True,
        "spool_pdf_sha256": digest,
        "physical_paper_certified": False,
        "windows_spool_certified": False,
        "cabinet_print_api_certified": False,
        "secure_release_certified": False,
    }
    (artifacts / "evidence.json").write_text(
        json.dumps(proof, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("VIRTUAL_PRINTER_LAB_PASS")
    print(json.dumps(proof, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"VIRTUAL_PRINTER_LAB_FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
