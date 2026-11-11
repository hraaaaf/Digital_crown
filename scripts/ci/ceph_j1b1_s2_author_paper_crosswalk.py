"""J1.B1-S2: primary-author paper explicitly names a SMALL subset of numbered
CL-Detection2023 landmarks. NEVER treat that as medical/ONNX validation.

Read-only metadata proof, zero images, patients, weights, inference, or clinical
activation. Requires an exact versioned paper, local pinned numeric source contract,
and rejects cross-paper or guessed aliases.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

PAPER_URL = "https://arxiv.org/html/2409.15834v1"
PAPER_ID = "2409.15834v1"
SOURCE_COMMIT = "18d17d1934970016e7610c4849311900b8d1f191"
MODEL_SHA256 = "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"

# Claims cited literally by the challenge coauthors' research paper.
# Tuple = 1-based challenge category, abbreviation printed by the paper,
# exact Digital Crown 0-based legacy alias (to check for numerical agreement).
# These are NOMENCLATURE EVIDENCE ONLY, NOT ANATOMICAL/MODEL CERTIFICATION.
EXPLICIT_TEXTUAL_PAIRS = (
    (5, "A", "A"),
    (10, "Go", "Go"),
    (17, "PNS", "PNS"),
    (25, "Co", "Co"),
    (26, "Prn", "Prn"),
    (27, "Ba", "Ba"),
    (29, "Bo", "Bo"),
)

# "Pos (No. 16)" is written in the paper; without an author-signed
# glossary, Pos -> Pog_soft would be a scientifically unsafe guess.
AMBIGUOUS_PAPER_PAIR = (16, "Pos", "Pog_soft")

class EvidenceError(RuntimeError):
    pass

def require(value: bool, code: str) -> None:
    if not value:
        raise EvidenceError(code)

class TextOnlyHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

def plain_text(raw: bytes) -> str:
    require(len(raw) > 20_000, "PAPER_HTML_TOO_SHORT")
    parser = TextOnlyHTML()
    parser.feed(raw.decode("utf-8-sig"))
    return re.sub(r"\s+", " ", unescape(" ".join(parser.parts))).strip()

def paper_pairs(text: str, entries=EXPLICIT_TEXTUAL_PAIRS) -> set[int]:
    require("Deep Learning Techniques for Automatic Lateral X-ray Cephalometric Landmark Detection" in text,
            "PAPER_IDENTITY_TITLE_MISSING")
    require("Ching-Wei Wang" in text and "Hongyuan Zhang" in text,
            "PAPER_ORGANIZER_AUTHOR_PROVENANCE_MISSING")
    verified: set[int] = set()
    for number, label, _ in entries:
        pattern = r"\b" + re.escape(label) + r"\s*\(\s*No\.\s*" + str(number) + r"\s*\)"
        require(re.search(pattern, text, flags=re.I) is not None,
                f"PAPER_NUMBERED_EXPLICIT_PAIR_MISSING_{number}_{label}")
        require(number not in verified, "DUPLICATE_AUTHOR_PAPER_NUMBER")
        verified.add(number)
    return verified

def literal_module_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    matches = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
                matches.append(node.value)
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name:
                matches.append(node.value)
    require(len(matches) == 1, f"LOCAL_ASSIGNMENT_AMBIGUOUS_{name}")
    return ast.literal_eval(matches[0])

def check_local_contract() -> dict[int, str]:
    registry = json.loads(Path("backend/scientific_assets.json").read_text(encoding="utf-8"))
    entries = [a for a in registry.get("assets", []) if a.get("id") == "cephalo_sota"]
    require(len(entries) == 1, "REGISTRY_CEPHALO_MODEL_NOT_UNIQUE")
    asset = entries[0]
    require(
        asset.get("sha256") == MODEL_SHA256
        and asset.get("provenance", {}).get("source_commit") == SOURCE_COMMIT
        and asset.get("anatomical_mapping_validation") == "SOURCE_LOCK_REQUIRED"
        and asset.get("clinical_activation_authorized") is False,
        "MODEL_PIN_OR_CLINICAL_GATE_DRIFT",
    )
    path = Path("backend/services/srpose38_contract.py")
    require(literal_module_assignment(path, "SRPOSE38_MODEL_SHA256") == MODEL_SHA256,
            "RUNTIME_MODEL_SHA_MISMATCH")
    mapping = literal_module_assignment(path, "SOTA_LANDMARKS_MAPPING")
    require(isinstance(mapping, dict) and set(mapping) == set(range(38)),
            "LEGACY_MAPPING_NOT_38_NUMERIC_INDICES")
    rows = Path("docs/SRPOSE38_LANDMARK_CONTRACT.md").read_text(encoding="utf-8")
    require("SOURCE_LOCK_REQUIRED" in rows and "NON CERTIFIÉS" in rows,
            "LOCAL_SOURCE_LOCK_DOCUMENTATION_MISSING")
    for number, label, legacy in EXPLICIT_TEXTUAL_PAIRS:
        require(mapping[number - 1] == legacy,
                f"LOCAL_MAPPING_DISAGREES_WITH_PAPER_{number}_{label}")
    require(mapping[AMBIGUOUS_PAPER_PAIR[0] - 1] == AMBIGUOUS_PAPER_PAIR[2],
            "LOCAL_AMBIGUOUS_ALIAS_DRIFT")
    return mapping

def validate_ambiguity(text: str) -> None:
    n, name, _ = AMBIGUOUS_PAPER_PAIR
    require(
        re.search(r"\b"+re.escape(name)+r"\s*\(\s*No\.\s*"+str(n)+r"\s*\)", text, flags=re.I) is not None,
        "PAPER_AMBIGUOUS_POS_LABEL_MISSING",
    )
    # 'Pos' is not an attestation for local 'Pog_soft', no alias promotion.

def run(report_path: Path) -> None:
    mapping = check_local_contract()
    req = Request(PAPER_URL, headers={"User-Agent":"DigitalCrown-J1B1-S2-primary-source-readonly/1.0"})
    try:
        with urlopen(req, timeout=30) as response:
            resolved = response.geturl()
            require(resolved.startswith("https://arxiv.org/html/2409.15834v1"),
                    "UNEXPECTED_PAPER_REDIRECT_OR_VERSION")
            raw = response.read(6_000_001)
    except EvidenceError:
        raise
    except Exception as exc:
        raise EvidenceError(f"PRIMARY_PAPER_UNAVAILABLE_FAIL_CLOSED: {exc}") from exc
    require(len(raw) <= 6_000_000, "PAPER_HTML_SIZE_LIMIT")
    content = plain_text(raw)
    verified = paper_pairs(content)
    validate_ambiguity(content)
    require(verified == {5, 10, 17, 25, 26, 27, 29}, "PAPER_EXPLICIT_NUMBER_SET_DRIFT")
    entries = []
    for i in range(38):
        number = i + 1
        source_pair = next(((n, label, local) for n,label,local in EXPLICIT_TEXTUAL_PAIRS if n==number),None)
        status = (
            "PAPER_TEXT_EXPLICIT_NUMERIC_NOMENCLATURE_ONLY"
            if source_pair else "AMBIGUOUS_POS_NOT_EQUIVALENT_TO_POG_SOFT"
            if number == 16 else "NO_EXPLICIT_AUTHOR_PAPER_NUMBERED_NAME_IN_AUDITED_PASSAGES"
        )
        entries.append({
            "onnx_channel_index": i,
            "challenge_number": number,
            "legacy_local_alias": mapping[i],
            "explicit_author_paper_abbreviation": source_pair[1] if source_pair else ("Pos" if number==16 else None),
            "nomenclature_evidence_status": status,
            "scientific_index_to_anatomy_validation": "SOURCE_LOCK_REQUIRED",
            "clinical_use_authorized": False,
        })
    report = {
        "lot": "CEPH-J1.B1-S2",
        "paper": PAPER_URL,
        "paper_version": PAPER_ID,
        "raw_paper_html_sha256_at_execution": hashlib.sha256(raw).hexdigest(),
        "runtime_source_commit": SOURCE_COMMIT,
        "onnx_sha256_from_contract_not_rehashed": MODEL_SHA256,
        "channel_count": 38,
        "explicit_paper_numbered_abbreviation_matches_local": len(verified),
        "ambiguous_paper_numbered_abbreviations_not_promoted": 1,
        "not_explicitly_named_in_audited_paper_prose": 30,
        "validated_for_anatomical_accuracy": 0,
        "clinical_release": False,
        "clinical_activation_authorized": False,
        "dataset_downloaded": False,
        "model_downloaded": False,
        "medical_images_or_patient_data_used": False,
        "inference_executed": False,
        "note": "Seven explicit author-paper abbreviations match legacy channel slots. This is not 7 clinically validated landmarks. Pos (16) remains ambiguous.",
        "channels": entries,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+"\n",encoding="utf-8")
    print("J1B1_S2_SEVEN_AUTHOR_PAPER_NUMBERED_NAMES_VERIFIED_NONCLINICAL")
    print("J1B1_S2_POS16_UNRESOLVED_NO_ANATOMICAL_ALIAS_PROMOTION")
    print("J1B1_S2_ALL_38_CLINICAL_MAPPING_AND_INFERENCE_HOLD")
    print(json.dumps({k:v for k,v in report.items() if k!="channels"},sort_keys=True))

def selftest() -> None:
    intro="Deep Learning Techniques for Automatic Lateral X-ray Cephalometric Landmark Detection Ching-Wei Wang Hongyuan Zhang "
    paper=intro+" ".join(f"{label} (No. {n})" for n,label,_ in EXPLICIT_TEXTUAL_PAIRS)
    paper+=" Pos (No. 16)"
    require(paper_pairs(paper) == {5, 10, 17, 25, 26, 27, 29}, "SELFTEST_SEVEN_MISMATCH")
    validate_ambiguity(paper)
    modified=paper.replace("Prn (No. 26)", "Prn (No. 28)")
    try:
        paper_pairs(modified)
    except EvidenceError as exc:
        require("PAPER_NUMBERED_EXPLICIT_PAIR_MISSING_26_Prn" in str(exc),
                "SELFTEST_WRONG_FAIL_REASON")
    else:
        raise EvidenceError("SELFTEST_UNDETECTED_PAPER_NUMBER_CHANGE")
    try:
        validate_ambiguity(paper.replace("Pos (No. 16)", "Pog_soft (No. 16)"))
    except EvidenceError as exc:
        require("PAPER_AMBIGUOUS_POS_LABEL_MISSING" in str(exc),
                "SELFTEST_WRONG_AMBIGUITY_FAIL_REASON")
    else:
        raise EvidenceError("SELFTEST_AMBIGUITY_GUESS_PROMOTED")
    print("J1B1_S2_NEGATIVE_NUMBER_AND_UNPROVEN_POS_ALIAS_REJECTION_PASS")

if __name__=="__main__":
    try:
        parser=argparse.ArgumentParser()
        parser.add_argument("action", choices=("selftest","verify"))
        parser.add_argument("--report",default="j1b1-s2-paper-nomenclature-metadata.json")
        args=parser.parse_args()
        selftest()
        if args.action=="verify":
            run(Path(args.report))
    except (EvidenceError, OSError, SyntaxError, ValueError, UnicodeError) as exc:
        print(f"J1B1_S2_FAIL_CLOSED: {exc}",file=sys.stderr)
        sys.exit(2)
