#!/usr/bin/env python3
"""Retrieve a strictly limited number of technical label neighbors from original SHA-pinned vendor PDFs.

Publisher source bytes remain on a disposable GitHub-hosted Windows runner.
Only short label-context snippets are emitted; never PDF files, patient data, or whole pages.
"""
import argparse, hashlib, json, re
from pathlib import Path

SOURCES = {
    "Ricketts (32 F).pdf": ("PM'", "Mand len", "PFH", "Cranium ant len"),
    "Ricketts (13 F).pdf": ("PFH", "InterIncisal"),
    "C01_Lateral Cephalometry Library - Lines and Contructed markers.pdf": ("Xi", "PtV", "CF"),
}
MAX_WORDS_PER_DOCUMENT = 20
MAX_SNIPPETS_PER_DOCUMENT = 5
MAX_SNIPPET_CHARS = 50

def term_match(text, term):
    # Marker Xi must NOT match the interior of the word 'Maxillary'.
    return re.search(r"(?<![a-zA-Z0-9])" + re.escape(term) +
                     r"(?![a-zA-Z0-9])", text, flags=re.IGNORECASE)

def extract(root,manifest):
    from pypdf import PdfReader
    out=[]
    for name,terms in SOURCES.items():
        entries=[x for x in manifest["priority_sources"] if x["relative_pdf_path"].endswith("/"+name)]
        if len(entries)!=1: raise ValueError("No unique vendor scientific PDF")
        pin=entries[0]
        p=(root/pin["relative_pdf_path"]).resolve()
        if not p.is_relative_to(root.resolve()) or p.suffix.lower()!=".pdf": raise ValueError("Path outside official read-only installation")
        if hashlib.sha256(p.read_bytes()).hexdigest()!=pin["sha256"]: raise ValueError("Original scientific PDF SHA mismatch")
        pdf=PdfReader(p,strict=False)
        if len(pdf.pages)!=pin["pages_pdf_1_based"]: raise ValueError("Vendor PDF page drift")
        snippets=[]
        budget=MAX_WORDS_PER_DOCUMENT
        observed_terms=set()
        for page_no,page in enumerate(pdf.pages,1):
            for line in (page.extract_text() or "").splitlines():
                if len(snippets)>=MAX_SNIPPETS_PER_DOCUMENT or budget<=0: break
                for term in terms:
                    if term in observed_terms or not term_match(line,term): continue
                    normalized=" ".join(line.split())
                    result=term_match(normalized,term)
                    if result is None: continue
                    at=result.start()
                    fragment=normalized[max(0,at-8):at+MAX_SNIPPET_CHARS-8][:MAX_SNIPPET_CHARS]
                    words=fragment.split()
                    fragment=" ".join(words[:budget])
                    consumed=len(fragment.split())
                    if not fragment: continue
                    snippets.append({"page":page_no,"term":term,"brief_label_context":fragment})
                    observed_terms.add(term)
                    budget-=consumed
                    break
        out.append({"filename":name,"sha256":pin["sha256"],"pages":len(pdf.pages),"snippets":snippets,
                    "derived_word_budget_used":MAX_WORDS_PER_DOCUMENT-budget,
                    "clinical_geometry_parity_verified":False})
    return {"schema":"FACAD_F01_13_PROPRIETARY_PDF_BRIEF_LABEL_CONTEXT_V1",
            "scope":"QUOTATION_LIMITED_METADATA_ONLY",
            "documents":out,"clinical_parity_certified":False,"original_atlas_publisher_authority":False,
            "full_vendor_document_embedded":False}

def selftest():
    assert MAX_WORDS_PER_DOCUMENT<=20 and MAX_SNIPPETS_PER_DOCUMENT<=5
    assert len(SOURCES)==3
    assert term_match("Xi", "Xi") is not None
    assert term_match("OLmx Maxillary occlusal line", "Xi") is None
    assert term_match("PtV Pterygoid Vertical", "PtV") is not None
    assert term_match("Mand len", "Mand len") is not None
    print("VENDOR_BRIEF_CONTEXT_OFFLINE_SELFTEST=6")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--manifest",type=Path)
    p.add_argument("--root",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    if a.self_test:selftest()
    else:
        if not(a.manifest and a.root and a.out):raise ValueError("Missing args")
        result=extract(a.root.resolve(),json.loads(a.manifest.read_text(encoding="utf-8")))
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        for item in result["documents"]:
            print("OFFICIAL_VENDOR_BRIEF_LABEL_SOURCE="+item["filename"])
            for row in item["snippets"]:
                print("LABEL_CONTEXT="+item["filename"]+"|"+str(row["page"])+"|"+row["term"]+"|"+row["brief_label_context"])
        print("SOURCE_DOCUMENTS_EXAMINED="+str(len(result["documents"])))
        print("FACAD_CLINICAL_PARITY_CERTIFIED=false")
