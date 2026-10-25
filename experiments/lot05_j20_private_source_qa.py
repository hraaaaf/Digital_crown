"""J20 owner-private source availability and immutable 333-label QA gate.

No private data on GitHub Actions. No staging, labels rewrite or clinical release.
"""
import hashlib,json,os,sys
from pathlib import Path
from lot05_j19_private_source_geometry_preflight import audit
from lot05_j13_private_clinician_corrections import labels_inventory,inventory_preflight
from lot05_j17_private_manifest_preflight import check

def verify(manifest,root,original=None):
    base=check(manifest,original)
    if root is None or not Path(root).is_dir():
        return {"schema":"digital-crown-lot05-j20-private-qa-v1",
                "status":"BLOCKED_ACADEMIC_SOURCE_LABELS_UNAVAILABLE",
                "active_permanent_count":base["active_permanent_count"],
                "primary_blocked_count":base["primary_blocked_count"],
                "pending_collision_count":base["pending_collision_count"],
                "pending_dedupe_count":base["pending_dedupe_count"],
                "source_geometry_verified":False,"staging_performed":False,
                "training_authorized":False}
    root=Path(root)
    inventory=labels_inventory(root)
    before={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in inventory.items()}
    census=inventory_preflight(root)
    result=audit(manifest,root,original)
    after={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in inventory.items()}
    if before!=after:raise ValueError("source_mutated_during_audit")
    result["academic_duplicate_census_pass"]=census["status"]=="PINNED_ACADEMIC_TEXT_ONLY_PREFLIGHT_PASS"
    result["all_333_source_hashes_unchanged"]=True
    result["status"]="READ_ONLY_QA_COMPLETE_STAGING_BLOCKED"
    return result

def main():
    if os.environ.get("GITHUB_ACTIONS","").lower()=="true" or len(sys.argv) not in (3,4):
        print('{"status":"FAIL_CLOSED_PRIVATE_INPUT_FORBIDDEN"}');return 1
    try:
        manifest_path=Path(sys.argv[1]);source_root=Path(sys.argv[2])
        if manifest_path.is_symlink() or not manifest_path.is_file() or manifest_path.stat().st_size>500000:
            raise ValueError("unsafe_private_manifest")
        original=None
        if len(sys.argv)==4:
            p=Path(sys.argv[3])
            if p.is_symlink() or not p.is_file() or p.stat().st_size>500000:raise ValueError("unsafe_original")
            original=p.read_bytes()
        result=verify(json.loads(manifest_path.read_text()),source_root,original)
        print(json.dumps(result,sort_keys=True))
        return 0 if result["status"]=="READ_ONLY_QA_COMPLETE_STAGING_BLOCKED" else 2
    except (OSError,ValueError,KeyError,TypeError):
        print('{"status":"FAIL_CLOSED_PRIVATE_J20_QA"}');return 1
if __name__=="__main__":raise SystemExit(main())
