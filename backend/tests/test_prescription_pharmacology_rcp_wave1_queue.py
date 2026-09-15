import json
from pathlib import Path


QUEUE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "audits"
    / "PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_WAVE1_QUEUE.json"
)

EXPECTED_MOLECULES = {
    "paracetamol",
    "ibuprofen",
    "amoxicillin",
    "penicillin_v",
    "metronidazole",
    "clarithromycin",
    "clindamycin",
}

ALLOWED_STATES = {
    "READY_FOR_CAPTURE_TRANSPORT",
    "PENDING_RCP_LINK_CONFIRMATION",
    "PENDING_CURRENT_PAGE_CONFIRMATION",
    "PENDING_CURRENT_PRESENTATION_DISCOVERY",
}


def _load_queue():
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def test_wave1_queue_has_exact_required_molecule_universe():
    queue = _load_queue()
    entries = queue["entries"]

    assert len(entries) == len(EXPECTED_MOLECULES)
    assert {entry["molecule_id"] for entry in entries} == EXPECTED_MOLECULES


def test_wave1_queue_is_documentary_and_every_gap_is_explicit():
    queue = _load_queue()
    assert queue["runtime_behavior_change"] is False

    for entry in queue["entries"]:
        assert entry["state"] in ALLOWED_STATES
        assert isinstance(entry["gap"], str) and entry["gap"].strip()
        assert isinstance(entry["source_urls"], list)
        assert all(url.startswith("https://") for url in entry["source_urls"])


def test_ready_for_capture_requires_official_ammps_source():
    queue = _load_queue()
    ready = [
        entry
        for entry in queue["entries"]
        if entry["state"] == "READY_FOR_CAPTURE_TRANSPORT"
    ]

    assert ready
    for entry in ready:
        assert entry["source_urls"]
        assert all("ammps.gov.ma" in url for url in entry["source_urls"])


def test_missing_source_cannot_be_marked_ready():
    queue = _load_queue()
    for entry in queue["entries"]:
        if not entry["source_urls"]:
            assert entry["state"] == "PENDING_CURRENT_PRESENTATION_DISCOVERY"


def test_ibuprofen_ready_state_is_grounded_in_current_ammps_search_page():
    queue = _load_queue()
    ibuprofen = next(
        entry for entry in queue["entries"] if entry["molecule_id"] == "ibuprofen"
    )

    assert ibuprofen["state"] == "READY_FOR_CAPTURE_TRANSPORT"
    assert "https://www.ammps.gov.ma/recherche-medicaments?page=27" in ibuprofen["source_urls"]
    assert "exact download target" in ibuprofen["gap"].lower()
