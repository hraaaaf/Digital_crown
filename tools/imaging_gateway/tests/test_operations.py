"""LOT06-F synthetic operator UX: no clinical writes, no PHI, no unsafe success."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.imaging_gateway import Config, HotFolder
from tools.imaging_gateway.operations import (
    OperationsRejected, project_operations, render_operations_json,
    render_operations_text, render_operations_html,
)


SYNTHETIC = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91Jpz"
    "AAAAFklEQVR4nGPkEpFjYGBgYmBgYGBgAAAC5gBAXKUgWwAAAABJRU5ErkJggg=="
)


def sample(**changes):
    data = {
        "state": "READY",
        "queued_items": 0,
        "states": {},
        "orphan_files": 0,
        "orphan_bytes": 0,
        "spool_bytes": 0,
        "free_bytes": 1024,
        "max_spool_bytes": 2000,
        "max_queue_items": 100,
        "min_free_bytes": 10,
        "last_capacity_issue": None,
    }
    data.update(changes)
    return data


class OperatorContractTests(unittest.TestCase):
    def test_idle_never_looks_like_clinically_confirmed(self):
        view = project_operations(sample())
        self.assertEqual(view["mode"], "READ_ONLY")
        self.assertEqual(view["clinical_status"], "NOT_CONNECTED")
        self.assertFalse(view["upload_permitted"])
        self.assertFalse(view["patient_confirmation_permitted"])
        self.assertFalse(view["server_confirmed"])
        self.assertEqual([n["code"] for n in view["notices"]],
                         ["CLINICAL_INTEGRATION_PENDING"])

    def test_all_known_states_get_distinct_nonclinical_instructions(self):
        states = {"PENDING_CONFIRMATION": 2, "QUARANTINED": 1,
                  "RETRY_PENDING": 3, "BLOCKED": 1}
        view = project_operations(sample(states=states, queued_items=7))
        codes = [n["code"] for n in view["notices"]]
        self.assertEqual(codes, ["RETRY_EXHAUSTED", "QUARANTINE_REVIEW",
                                 "RETRY_PENDING", "HUMAN_LINK_REQUIRED",
                                 "CLINICAL_INTEGRATION_PENDING"])
        self.assertFalse(view["patient_confirmation_permitted"])
        self.assertFalse(view["server_confirmed"])

    def test_backpressure_before_ordinary_review_and_no_fake_retry(self):
        view = project_operations(sample(
            state="BACKPRESSURE", last_capacity_issue="DISK_FULL",
            queued_items=1, states={"PENDING_CONFIRMATION": 1},
        ))
        self.assertEqual(view["notices"][0]["code"], "LOCAL_BACKPRESSURE")
        self.assertEqual(view["notices"][0]["severity"], "STOP")
        self.assertEqual(view["notices"][-1]["code"], "CLINICAL_INTEGRATION_PENDING")

    def test_orphan_alert_preserves_original_and_requires_manual_review(self):
        view = project_operations(sample(orphan_files=2, orphan_bytes=50,
                                         spool_bytes=75))
        notice = next(n for n in view["notices"] if n["code"] == "ORPHAN_SPOOL")
        self.assertIn("Ne pas effacer", notice["instruction"])

    def test_unknown_local_queue_state_fails_closed(self):
        view = project_operations(sample(
            state="BACKPRESSURE", queued_items=1,
            states={"UNRECOGNIZED_STATE": 1},
        ))
        self.assertEqual(view["notices"][0]["code"], "LOCAL_BACKPRESSURE")
        self.assertEqual(view["notices"][1]["code"], "UNKNOWN_QUEUE_STATE")

    def test_bad_totals_keys_and_provenance_are_rejected(self):
        inputs = [
            sample(states={"PENDING_CONFIRMATION": 2}, queued_items=1),
            sample(states={"patient_xyz": 1}, queued_items=1),
            sample(states={"BLOCKED": True}, queued_items=1),
            sample(states={"BLOCKED": -1}, queued_items=-1),
            sample(last_capacity_issue="leak-patient-123"),
            sample(state="SERVER_CONFIRMED"),
            sample(orphan_files=-1),
            sample(orphan_bytes=99, spool_bytes=10),
            sample(free_bytes=True),
        ]
        for bad in inputs:
            with self.subTest(bad=bad), self.assertRaises(OperationsRejected):
                project_operations(bad)

    def test_never_echoes_a_filename_or_patient_identity(self):
        states = {"QUARANTINED": 1, "PENDING_CONFIRMATION": 1}
        view = project_operations(sample(queued_items=2, states=states))
        text = render_operations_text(view)
        json_text = render_operations_json(view)
        for output in (text, json_text):
            self.assertNotIn("patient_id", output)
            self.assertNotIn("appointment_id", output)
            self.assertNotIn("receipt_id", output)
            self.assertNotIn("sha256", output)
            self.assertNotIn("capture.png", output)
            self.assertNotIn("CONFIRMED", output)
        self.assertIn("en cours de construction", text)

    def test_renderers_require_contract_not_arbitrary_text(self):
        for render in (render_operations_json, render_operations_text):
            with self.assertRaises(OperationsRejected):
                render({"contract": "FAKE_CONFIRMED"})

    def test_live_spool_snapshot_requires_patient_link_but_not_attach(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            watch = root / "watch"
            watch.mkdir()
            agent = HotFolder(Config("cabinet1", "device1", watch,
                                     root / "private", b"k" * 32))
            (watch / "not-a-patient-name.png").write_bytes(SYNTHETIC)
            agent.scan_once()
            self.assertEqual(agent.scan_once()["staged"], 1)
            view = project_operations(agent.storage_health())
            self.assertEqual(view["queued_items"], 1)
            codes = [n["code"] for n in view["notices"]]
            self.assertIn("HUMAN_LINK_REQUIRED", codes)
            self.assertNotIn("not-a-patient-name", render_operations_json(view))
            self.assertEqual(agent.items()[0]["state"], "PENDING_CONFIRMATION")

    def test_corrupt_state_name_is_aggregated_without_echoing_secret(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            watch = root / "watch"
            watch.mkdir()
            agent = HotFolder(Config("cabinet1", "device1", watch,
                                     root / "private", b"k" * 32))
            (watch / "fixture.png").write_bytes(SYNTHETIC)
            agent.scan_once()
            agent.scan_once()
            with agent._db() as db:
                db.execute("UPDATE items SET state=?",
                           ("SECRET_PATIENT_IDENTIFIER",))
            health = agent.storage_health()
            self.assertEqual(health["state"], "BACKPRESSURE")
            self.assertEqual(health["states"], {"UNRECOGNIZED_STATE": 1})
            output = render_operations_json(project_operations(health))
            self.assertNotIn("SECRET_PATIENT_IDENTIFIER", output)
            self.assertIn("UNKNOWN_QUEUE_STATE", output)

    def test_cli_operations_json_is_read_only_and_no_phi(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            watch = root / "watch"
            watch.mkdir()
            private = root / "private"
            env = dict(os.environ, DC_IMAGING_SPOOL_KEY_HEX="6b" * 32)
            cmd = [
                sys.executable, "-m", "tools.imaging_gateway.cli",
                "--watch-dir", str(watch), "--state-dir", str(private),
                "--cabinet", "cabinet1", "--workstation", "device1",
                "--operations-json",
            ]
            proc = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[3],
                                  env=env, text=True, capture_output=True,
                                  check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads(proc.stdout)
            self.assertFalse(data["upload_permitted"])
            self.assertEqual(data["clinical_status"], "NOT_CONNECTED")
            self.assertEqual(data["queued_items"], 0)
            self.assertNotIn(str(watch), proc.stdout)
            self.assertNotIn("6b" * 32, proc.stdout)

    def test_cli_operator_view_is_concise_and_no_confirmation_button(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            watch = root / "watch"
            watch.mkdir()
            env = dict(os.environ, DC_IMAGING_SPOOL_KEY_HEX="6b" * 32)
            cmd = [sys.executable, "-m", "tools.imaging_gateway.cli",
                   "--watch-dir", str(watch),
                   "--state-dir", str(root / "private"),
                   "--cabinet", "cabinet1", "--workstation", "device1",
                   "--operations"]
            proc = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[3],
                                  env=env, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("LECTURE SEULE", proc.stdout)
            self.assertIn("en cours de construction", proc.stdout)
            self.assertNotIn(str(watch), proc.stdout)

    def test_responsive_html_stays_static_read_only(self):
        view = project_operations(sample(
            state="BACKPRESSURE", queued_items=1,
            states={"PENDING_CONFIRMATION": 1},
            last_capacity_issue="QUEUE_ITEM_LIMIT",
        ))
        markup = render_operations_html(view)
        self.assertIn('name="viewport" content="width=device-width, initial-scale=1"', markup)
        self.assertIn('@media (max-width: 600px)', markup)
        self.assertIn('data-imaging-operations="read-only"', markup)
        self.assertIn('aria-label="Actions de vérification"', markup)
        self.assertIn("en cours de construction", markup)
        self.assertIn("LOCAL", markup.upper())
        self.assertNotIn("<script", markup)
        self.assertNotIn("<form", markup)
        self.assertNotIn("<button", markup)
        self.assertNotIn("fetch(", markup)
        self.assertNotIn("patient_id", markup)
        self.assertNotIn("receipt_id", markup)
        self.assertNotIn("http://", markup)
        self.assertNotIn("https://", markup)

    def test_render_html_rejects_untrusted_contract_and_escapes_attacks(self):
        with self.assertRaises(OperationsRejected):
            render_operations_html({"contract": "CLINICAL_SUCCESS"})
        view = project_operations(sample())
        view["notices"][0]["title"] = '<img src=x onerror=alert(1)>'
        markup = render_operations_html(view)
        self.assertNotIn("<img", markup)
        self.assertIn("&lt;img", markup)

    def test_html_cli_outputs_no_patient_data_and_does_not_create_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            watch = root / "watch"
            watch.mkdir()
            env = dict(os.environ, DC_IMAGING_SPOOL_KEY_HEX="6b" * 32)
            cmd = [sys.executable, "-m", "tools.imaging_gateway.cli",
                   "--watch-dir", str(watch), "--state-dir", str(root / "private"),
                   "--cabinet", "cabinet1", "--workstation", "device1",
                   "--operations-html"]
            proc = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[3],
                                  env=env, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("<!doctype html>", proc.stdout.lower())
            self.assertNotIn(str(watch), proc.stdout)
            self.assertNotIn("6b" * 32, proc.stdout)
            self.assertNotIn("server_confirmed", proc.stdout)
            self.assertNotIn("patient_id", proc.stdout)
            self.assertFalse((root / "private" / "spool" / "receipt.json").exists())


if __name__ == "__main__":
    unittest.main()
