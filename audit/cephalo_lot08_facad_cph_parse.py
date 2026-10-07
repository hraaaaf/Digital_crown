#!/usr/bin/env python3
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def direct_text_children(elem):
    out = {}
    for child in list(elem):
        if len(list(child)) == 0:
            text = (child.text or "").strip()
            if text:
                out.setdefault(child.tag, []).append(text)
    return out

def find_measurement_candidates(root):
    candidates = []
    for elem in root.iter():
        direct = direct_text_children(elem)
        if "name" not in direct or "norm" not in direct:
            continue
        refs = [(x.text or "").strip() for x in elem.iter("point_ref") if (x.text or "").strip()]
        record = {
            "xml_tag": elem.tag,
            "name": direct["name"][0],
            "norm": direct["norm"][0],
            "unit": direct.get("unit", [None])[0],
            "calc_type": direct.get("calc_type", [None])[0],
            "changeSign": direct.get("changeSign", [None])[0],
            "point_refs": refs,
            "direct_fields": direct,
        }
        candidates.append(record)
    return candidates

def summarize(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    ceph = root.find("cephfile")
    profile_name = ceph.findtext("name") if ceph is not None else None
    analysis_type = ceph.findtext("AnalysisType") if ceph is not None else None
    version = root.findtext("version")
    saved = root.findtext("saved")

    candidates = find_measurement_candidates(root)
    tags = {}
    for x in root.iter():
        tags[x.tag] = tags.get(x.tag, 0) + 1

    return {
        "source_filename": path.name,
        "sha256": sha256_file(path),
        "facad_file_version": version,
        "saved": saved,
        "profile_name": profile_name,
        "analysis_type": analysis_type,
        "measurement_candidate_count": len(candidates),
        "measurement_candidates": candidates,
        "xml_tag_counts": dict(sorted(tags.items())),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data = [summarize(Path(f)) for f in args.files]
    Path(args.out).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for item in data:
        print(f'{item["profile_name"]}: {item["measurement_candidate_count"]} norm-bearing measurement candidates')
        for i, m in enumerate(item["measurement_candidates"], start=1):
            print(f'{i:02d}. {m["name"]} | norm={m["norm"]} | unit={m["unit"]} | calc={m["calc_type"]} | sign={m["changeSign"]} | refs={",".join(m["point_refs"])}')

if __name__ == "__main__":
    main()
