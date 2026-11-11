"""J1.B1-S3: audit 38 FR/EN terminology equivalents, not model clinical accuracy.

No patient data, model weights, clinical inference, image processing, database, or
runtime mutations. Every row is explicitly NOT certified for clinical automation.
"""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import re
import sys

DOCUMENT = Path("docs/audits/CEPHALO_J1B1_S3_38_LANDMARK_TERMINOLOGY.json")
RUNTIME = Path("backend/services/srpose38_contract.py")
REGISTRY = Path("backend/scientific_assets.json")
HISTORIC = Path("docs/SRPOSE38_LANDMARK_CONTRACT.md")
PIN = "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
PAPER_PAIRS = {5:"A",10:"Go",17:"PNS",25:"Co",26:"Prn",27:"Ba",29:"Bo"}
SOURCE_COMMIT = "18d17d1934970016e7610c4849311900b8d1f191"
PAPER = "https://arxiv.org/html/2409.15834v1"

class GuardFailure(RuntimeError):
    pass

def guard(cond, code):
    if not cond:
        raise GuardFailure(code)

def literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(x, ast.Name) and x.id == name for x in node.targets):
                values.append(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            values.append(node.value)
    guard(len(values)==1,"RUNTIME_PIN_OR_MAPPING_NOT_UNIQUE_"+name)
    return ast.literal_eval(values[0])

def validate_crosswalk(doc, mapping, asset):
    guard(doc.get("schema_version")==1 and doc.get("status")=="NONCLINICAL_38_TERM_CROSSWALK",
          "CROSSWALK_NOT_REVIEW_ONLY")
    guard(doc.get("model_sha256")==PIN and doc.get("model_source_commit")==SOURCE_COMMIT,
          "MODEL_PROVENANCE_DRIFT")
    guard(doc.get("clinical_activation_authorized") is False
          and doc.get("model_to_anatomy_certified") is False
          and doc.get("gate")=="SOURCE_LOCK_REQUIRED","CLINICAL_PROMOTION_REJECTED")
    guard(doc.get("numbered_source_matches")==7 and doc.get("author_paper_pos16_lexical_only")==1
          and doc.get("other_numbers_without_primary_named_pair")==30,"SOURCE_PROOF_COUNTS_DRIFT")
    guard(doc.get("nomenclature_entries")==38, "NOMENCLATURE_ENTRY_COUNT_DRIFT")
    guard(isinstance(mapping,dict) and set(mapping)==set(range(38))
          and len(set(mapping.values()))==38,"RUNTIME_MAPPING_NOT_COMPLETE_UNIQUE")
    guard(asset.get("sha256")==PIN
          and asset.get("anatomical_mapping_validation")=="SOURCE_LOCK_REQUIRED"
          and asset.get("clinical_activation_authorized") is False
          and asset.get("provenance",{}).get("source_commit")==SOURCE_COMMIT,
          "SOURCE_REGISTRY_INTEGRITY_OR_CLINICAL_GATE_DRIFT")
    sources=doc.get("sources")
    guard(isinstance(sources,dict) and sources.get("author2024")==PAPER,
          "AUTHOR_PAPER_NOT_PINNED_V1")
    sourceset=set(sources.values())
    rows=doc.get("landmarks")
    guard(isinstance(rows,list) and len(rows)==38,"CROSSWALK_NOT_38_ROWS")
    for index, item in enumerate(rows):
        guard(item.get("index")==index and item.get("challenge_number")==index+1,
              "ROW_INDEX_DRIFT_"+str(index))
        guard(item.get("legacy_runtime_id")==mapping[index],"LEGACY_RUNTIME_ALIAS_DRIFT_"+str(index))
        guard(all(isinstance(item.get(k),str) and item[k].strip()
                  for k in ("term_fr","term_en","term_equivalence_level","protocol_specific_definition")),
              "MISSING_TERMINOLOGY_"+str(index))
        equivalents=item.get("terminology_equivalents")
        guard(isinstance(equivalents,list) and equivalents
              and len(equivalents)==len(set(equivalents))
              and all(isinstance(v,str) and v.strip() for v in equivalents),
              "MISSING_OR_DUPLICATE_SYNONYM_"+str(index))
        refs=item.get("nomenclature_evidence_refs")
        guard(isinstance(refs,list) and refs and set(refs)<=sourceset,
              "UNTRUSTED_OR_EMPTY_TERMINOLOGY_SOURCE_"+str(index))
        guard(item.get("validated_model_output_identity") is False
              and item.get("automated_clinical_use_allowed") is False,
              "SINGLE_CHANNEL_CLINICAL_LAUNDERING_"+str(index))
        number=index+1
        if number in PAPER_PAIRS:
            guard(item.get("challenge_numbered_evidence")=="AUTHOR_PAPER_EXPLICIT"
                  and item.get("paper_abbreviation")==PAPER_PAIRS[number]
                  and PAPER in refs,
                  "AUTHOR_NUMBERED_ATTESTATION_DRIFT_"+str(number))
        elif number==16:
            guard(item.get("challenge_numbered_evidence")=="AUTHOR_PAPER_POS16_ONLY"
                  and item.get("paper_abbreviation")=="Pos"
                  and item.get("legacy_runtime_id")=="Pog_soft"
                  and item.get("protocol_specific_definition")==
                      "EXTERNAL_POS_EQUIVALENCE_BUT_DATASET_ATTESTATION_PENDING"
                  and PAPER in refs,
                  "POS16_FALSE_CLINICAL_EQUIVALENCE")
        else:
            guard(item.get("challenge_numbered_evidence")=="NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE"
                  and item.get("paper_abbreviation") is None,
                  "UNSUPPORTED_AUTHOR_NUMBERED_PROOF_"+str(number))
    guard(len([i for i in rows if i["challenge_numbered_evidence"]=="AUTHOR_PAPER_EXPLICIT"])==7,
          "EXPLICIT_PAIR_COUNT_DRIFT")
    guard(len([i for i in rows if i["challenge_numbered_evidence"]=="NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE"])==30,
          "UNRESOLVED_PAIR_COUNT_DRIFT")
    return rows

def verify_actual():
    mapping=literal_assignment(RUNTIME,"SOTA_LANDMARKS_MAPPING")
    guard(literal_assignment(RUNTIME,"SRPOSE38_MODEL_SHA256")==PIN,"CONTRACT_PIN_CHANGED")
    doc=json.loads(DOCUMENT.read_text(encoding="utf-8"))
    reg=json.loads(REGISTRY.read_text(encoding="utf-8"))
    assets=[x for x in reg.get("assets",[]) if x.get("id")=="cephalo_sota"]
    guard(len(assets)==1,"NO_UNIQUE_SCIENTIFIC_ASSET")
    rows=validate_crosswalk(doc,mapping,assets[0])
    original=HISTORIC.read_text(encoding="utf-8")
    table=re.findall(r"^\|(\d+)\|(\d+)\|([^|]+)\|([^|]+)\|$",original,flags=re.M)
    guard(len(table)==38,"HISTORIC_ANATOMICAL_TABLE_NOT_38")
    for index, (idx,ch_num,_,id_) in enumerate(table):
        guard(int(idx)==index and int(ch_num)==index+1 and id_.strip()==rows[index]["legacy_runtime_id"],
              "HISTORICAL_SOURCE_CROSSWALK_DRIFT_"+str(index))
    guard("SOURCE_LOCK_REQUIRED" in original and "NON CERTIFIÉS" in original,
          "HISTORIC_HUMAN_GATE_REMOVED")
    print("J1B1_S3_COMPLETE_38_FR_EN_EQUIVALENT_NOMENCLATURE_CHECK_PASS")
    print("J1B1_S3_SEVEN_SOURCE_NAMED_PLUS_POS16_LEXICAL_NO_CLINICAL_PROMOTION")
    print("J1B1_S3_ALL_38_LEGACY_IDS_STABLE_CLINICAL_SOURCE_LOCK_PASS")
    print(json.dumps({"total":len(rows),"explicit_numbered":7,"ambiguous_pos":1,
                      "remaining_without_primary_numbered_name":30,
                      "all_38_model_anatomy_certified":False,
                      "clinical_activation_authorized":False,
                      "source_lock":"SOURCE_LOCK_REQUIRED",
                      "patient_data_used":False,"inference_performed":False},sort_keys=True))
    return doc,mapping,assets[0]

def negative_tests(doc,mapping,asset):
    for label, mutate in [
        ("SWAPPED_ANATOMY_INDEX",lambda x:x["landmarks"][2].update(legacy_runtime_id="N")),
        ("FAKE_AUTHOR_NUMERIC_CLAIM",lambda x:x["landmarks"][1].update(challenge_numbered_evidence="AUTHOR_PAPER_EXPLICIT")),
        ("FAKE_POS_EQUALS_CLINICAL",lambda x:x["landmarks"][15].update(protocol_specific_definition="CONFIRMED_CLINICAL")),
        ("FAKE_ONE_POINT_CLINICAL",lambda x:x["landmarks"][0].update(automated_clinical_use_allowed=True)),
        ("MISSING_ONE_ENTRY",lambda x:x["landmarks"].pop()),
    ]:
        edited=copy.deepcopy(doc)
        mutate(edited)
        try:
            validate_crosswalk(edited,mapping,asset)
        except GuardFailure:
            pass
        else:
            raise GuardFailure("NEGATIVE_CASE_UNDETECTED_"+label)
    print("J1B1_S3_FIVE_ADVERSARIAL_FAKE_PROVENANCE_AND_CLINICAL_GATES_PASS")

if __name__=="__main__":
    try:
        document,ids,scientific=verify_actual()
        negative_tests(document,ids,scientific)
    except (GuardFailure,ValueError,KeyError,TypeError,UnicodeError,FileNotFoundError) as exc:
        print(f"J1B1_S3_FAIL_CLOSED: {exc}",file=sys.stderr)
        sys.exit(2)
