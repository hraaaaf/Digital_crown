"""J19 owner-private read-only J16 source geometry and target collision gate."""
import json,os,sys
from collections import Counter,defaultdict
from pathlib import Path
from lot05_j17_private_manifest_preflight import check
from lot05_j13_private_clinician_corrections import labels_inventory,parse_text,locate_once,FDI
def audit(manifest,root,original=None):
    base=check(manifest,original)
    inventory=labels_inventory(root)
    grouped=defaultdict(list)
    for r in manifest["active_permanent"]:
        d=r["decision"];key=(d["split"],d["stem"])
        if key not in inventory:raise ValueError("missing_source")
        grouped[key].append(d)
    collisions=0
    for key,records in grouped.items():
        rows=parse_text(inventory[key].read_text(encoding="utf8"))[2]
        planned=[cls for cls,_ in rows];seen=set()
        for d in records:
            idx=locate_once(rows,d["from_fdi"],d["expected_bbox"])
            if idx in seen:raise ValueError("repeated_source_box")
            seen.add(idx);planned[idx]=FDI[d["to_fdi"]]
        totals=Counter(planned)
        collisions+=int(any(totals[FDI[d["to_fdi"]]]>1 for d in records))
    return {"schema":"digital-crown-lot05-j19-private-source-qa-v1",
        "status":"READ_ONLY_GEOMETRY_CHECKED_STAGING_BLOCKED",
        "source_label_files":len(inventory),"active_witnesses_checked":sum(map(len,grouped.values())),
        "source_target_collision_files":collisions,
        "pending_clinical_collisions":len(manifest["pending_collision_adjudications"]),
        "pending_dedupe_review":len(manifest["exact_duplicate_deletions_pending_review"]),
        "primary_excluded":len(manifest["primary_out_of_ontology"]),
        "source_manifest_hash_verified":base["source_hash_verified"],
        "source_labels_modified":False,"staging_performed":False,
        "training_authorized":False,"clinical_use_authorized":False}
def main():
    if os.getenv("GITHUB_ACTIONS","").lower()=="true" or len(sys.argv) not in (3,4):
        print('{"status":"FAIL_CLOSED_PRIVATE_INPUT_FORBIDDEN_OR_ARGUMENTS"}');return 1
    try:
        p=Path(sys.argv[1]);root=Path(sys.argv[2])
        if p.is_symlink() or not p.is_file() or p.stat().st_size>500000:raise ValueError("unsafe_manifest")
        original=None
        if len(sys.argv)==4:
            o=Path(sys.argv[3])
            if o.is_symlink() or not o.is_file() or o.stat().st_size>500000:raise ValueError("unsafe_original")
            original=o.read_bytes()
        print(json.dumps(audit(json.loads(p.read_text()),root,original),sort_keys=True));return 0
    except (OSError,ValueError,TypeError,KeyError):
        print('{"status":"FAIL_CLOSED_PRIVATE_SOURCE_QA"}');return 1
if __name__=="__main__":raise SystemExit(main())
