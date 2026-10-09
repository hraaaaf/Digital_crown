#!/usr/bin/env python3
"""Read-only validation of scientific term locations in five pinned vendor manuals."""
import argparse, hashlib, json
from pathlib import Path

SEARCH={
"Ricketts (32 F).pdf":["PM'","Mand len","Cranium ant len","Facial height","PFH"],
"Ricketts (13 F).pdf":["PFH","InterIncisal","Facial height","Total Facial Height"],
"C01_Lateral Cephalometry Library - Lines and Contructed markers.pdf":["Xi","PM'","PtV","CF","CC"],
"C02_Lateral Cephalometry Library - Measurements.pdf":["Dist2p","Angle4p","Angle3p","ProjLine"],
"Overview of Landmarks.pdf":["PM","Xi","Pt","Pog"],
}
def index(root,manifest):
    from pypdf import PdfReader
    output=[]
    for name,terms in SEARCH.items():
        source=[x for x in manifest["priority_sources"] if x["relative_pdf_path"].endswith("/"+name)]
        if len(source)!=1: raise ValueError("Missing exact manufacturer reference: "+name)
        pin=source[0]
        path=(root/pin["relative_pdf_path"]).resolve()
        if not path.is_relative_to(root.resolve()) or path.suffix.lower()!=".pdf": raise ValueError("Invalid source location")
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=pin["sha256"]: raise ValueError("Document SHA mismatch")
        pdf=PdfReader(path,strict=False)
        if len(pdf.pages)!=pin["pages_pdf_1_based"]: raise ValueError("Pages changed")
        terms_by_page={}
        for number,page in enumerate(pdf.pages,1):
            text=(page.extract_text() or "").casefold()
            hit=[term for term in terms if term.casefold() in text]
            if hit: terms_by_page[str(number)]=hit
        output.append({"name":name,"sha256":pin["sha256"],"pages":len(pdf.pages),"keyword_pages":terms_by_page})
    return {"schema":"FACAD_F01_13_FIVE_PDF_LEXICAL_EVIDENCE_V1",
            "documents":output,"vendor_science_documents":len(output),
            "scientific_formula_equivalence":"NOT_VERIFIED","clinical_parity":"NOT_TESTED",
            "full_vendor_pdf_redistributed":False,"patient_data_exported":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path)
    p.add_argument("--manifest",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        assert len(SEARCH)==5
        assert all(len(v)>0 for v in SEARCH.values())
        print("SCIENTIFIC_PDF_LEXICAL_SELFTEST=2")
    else:
        if not (a.root and a.manifest and a.out): raise ValueError("Missing CLI argument")
        m=json.loads(a.manifest.read_text(encoding="utf-8"))
        result=index(a.root,m)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print("PINNED_VENDOR_SCIENCE_PDFS=5")
        print("SCIENCE_EQUIVALENCE_CERTIFIED=false")
