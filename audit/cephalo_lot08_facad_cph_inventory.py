#!/usr/bin/env python3
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def direct_text_children(elem):
    out={}
    for child in list(elem):
        if len(list(child)) == 0:
            text=(child.text or "").strip()
            if text:
                out.setdefault(child.tag, []).append(text)
    return out

def measurements(root):
    rows=[]
    def walk(elem,path):
        direct=direct_text_children(elem)
        if "name" in direct and "norm" in direct:
            rows.append({
                "order":len(rows)+1,
                "name":direct["name"][0],
                "norm":direct["norm"][0],
                "unit":direct.get("unit",[None])[0],
                "calc_type":direct.get("calc_type",[None])[0],
                "changeSign":direct.get("changeSign",[None])[0],
                "point_refs":[(x.text or "").strip() for x in elem.iter("point_ref") if (x.text or "").strip()],
                "xml_tag":elem.tag,
                "xml_path":path,
            })
        counts={}
        for child in list(elem):
            counts[child.tag]=counts.get(child.tag,0)+1
            walk(child,f"{path}/{child.tag}[{counts[child.tag]}]")
    walk(root,f"/{root.tag}[1]")
    return rows

def parse_file(path):
    tree=ET.parse(path)
    root=tree.getroot()
    ceph=root.find("cephfile")
    name=ceph.findtext("name") if ceph is not None else None
    analysis_type=ceph.findtext("AnalysisType") if ceph is not None else None
    rows=measurements(root)
    return {
        "filename":path.name,
        "sha256":sha256(path),
        "profile_name":name,
        "analysis_type":analysis_type,
        "facad_file_version":root.findtext("version"),
        "saved":root.findtext("saved"),
        "measurement_count":len(rows),
        "measurements":rows,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--json",required=True)
    ap.add_argument("--markdown",required=True)
    args=ap.parse_args()
    directory=Path(args.directory)
    items=[]
    failures=[]
    for path in sorted(directory.glob("*.cph"), key=lambda p:p.name.lower()):
        try:
            items.append(parse_file(path))
        except Exception as exc:
            failures.append({"filename":path.name,"error":repr(exc)})
    payload={"count":len(items),"failures":failures,"analyses":items}
    Path(args.json).write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=["# Facad 3.14 standard cephalometric analyses","","| # | File | Profile | Type | Measures |","|---:|---|---|---|---:|"]
    for i,item in enumerate(items,1):
        lines.append(f'| {i} | {item["filename"]} | {item["profile_name"] or ""} | {item["analysis_type"] or ""} | {item["measurement_count"]} |')
    if failures:
        lines += ["","## Parse failures",""]+[f'- {x["filename"]}: {x["error"]}' for x in failures]
    Path(args.markdown).write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"CPH_COUNT={len(items)}")
    print(f"PARSE_FAILURES={len(failures)}")
    for i,item in enumerate(items,1):
        names=", ".join(x["name"] for x in item["measurements"])
        print(f'{i:02d}. {item["filename"]} | profile={item["profile_name"]} | type={item["analysis_type"]} | measures={item["measurement_count"]}')
        if names:
            print(f'    measures: {names}')
    if failures:
        for x in failures:
            print(f'FAIL {x["filename"]}: {x["error"]}')
        raise SystemExit(1)

if __name__=="__main__":
    main()
