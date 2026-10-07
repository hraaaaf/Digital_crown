#!/usr/bin/env python3
import argparse, json, xml.etree.ElementTree as ET
from pathlib import Path

def direct_text_children(elem):
    out={}
    for child in list(elem):
        if len(list(child))==0:
            txt=(child.text or "").strip()
            if txt:
                out.setdefault(child.tag,[]).append(txt)
    return out

def measurements(path):
    root=ET.parse(path).getroot()
    rows=[]
    for elem in root.iter():
        d=direct_text_children(elem)
        if "name" in d and "norm" in d:
            rows.append(d["name"][0])
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ceph-dir",required=True)
    ap.add_argument("--registry",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--dc-contract",required=True)
    ap.add_argument("--protocol-profile",action="append",default=[])
    args=ap.parse_args()
    reg=json.loads(Path(args.registry).read_text(encoding="utf-8"))
    contract=json.loads(Path(args.dc_contract).read_text(encoding="utf-8"))
    valid_dc_ids={m["measurement_id"] for m in contract.get("measurements",[]) if isinstance(m,dict) and m.get("measurement_id")}
    valid_relationship_ids=set()
    def collect_relationship_ids(node):
        if isinstance(node,dict):
            rid=node.get("relationship_id")
            if isinstance(rid,str) and rid:
                valid_relationship_ids.add(rid)
            for value in node.values():
                collect_relationship_ids(value)
        elif isinstance(node,list):
            for value in node:
                collect_relationship_ids(value)
    for profile_path in args.protocol_profile:
        collect_relationship_ids(json.loads(Path(profile_path).read_text(encoding="utf-8")))
    out={"schema_version":"FACAD_DC_PROTOCOL_MAPPING_RESULT_V1","profiles":{}}
    for profile,cfg in reg["profiles"].items():
        path=Path(args.ceph_dir)/cfg["facad_filename"]
        names=measurements(path)
        rows=[]
        counts={"CANONICAL_LABEL_MATCH":0,"CANDIDATE_GEOMETRY_REVIEW":0,"EXISTING_DERIVED_RELATIONSHIP":0,"BLOCKED_EXACT_LANDMARK":0,"UNMAPPED":0}
        for order,name in enumerate(names,1):
            m=cfg["mappings"].get(name)
            if m is None:
                row={"order":order,"facad_label":name,"dc_id":None,"status":"UNMAPPED"}
            else:
                status=m.get("status")
                if status in {"CANONICAL_LABEL_MATCH","CANDIDATE_GEOMETRY_REVIEW"}:
                    if m.get("dc_id") not in valid_dc_ids:
                        raise SystemExit(f"Unknown dc_id in mapping registry: {m.get('dc_id')}")
                elif status=="EXISTING_DERIVED_RELATIONSHIP":
                    if m.get("dc_relationship_id") not in valid_relationship_ids:
                        raise SystemExit(f"Unknown dc_relationship_id in mapping registry: {m.get('dc_relationship_id')}")
                elif status=="BLOCKED_EXACT_LANDMARK":
                    if not m.get("required_identity"):
                        raise SystemExit(f"Blocked mapping missing required_identity: {name}")
                    aliases=m.get("forbidden_aliases")
                    if not isinstance(aliases,list) or not aliases:
                        raise SystemExit(f"Blocked mapping missing forbidden_aliases: {name}")
                else:
                    raise SystemExit(f"Unknown mapping status: {status}")
                row={"order":order,"facad_label":name,**m}
            counts[row["status"]]+=1
            rows.append(row)
        out["profiles"][profile]={
            "facad_filename":cfg["facad_filename"],
            "facad_measurement_count":len(names),
            "counts":counts,
            "rows":rows,
        }
    Path(args.out).write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    for profile,data in out["profiles"].items():
        c=data["counts"]
        print(f'{profile}: total={data["facad_measurement_count"]} label={c["CANONICAL_LABEL_MATCH"]} candidate={c["CANDIDATE_GEOMETRY_REVIEW"]} relationship={c["EXISTING_DERIVED_RELATIONSHIP"]} blocked={c["BLOCKED_EXACT_LANDMARK"]} unmapped={c["UNMAPPED"]}')
        for r in data["rows"]:
            target=r.get("dc_id") or r.get("dc_relationship_id") or (f'BLOCKED:{r.get("required_identity")}' if r.get("required_identity") else "-")
            print(f'  {r["order"]:02d}. {r["facad_label"]} -> {target} [{r["status"]}]')

if __name__=="__main__":
    main()
