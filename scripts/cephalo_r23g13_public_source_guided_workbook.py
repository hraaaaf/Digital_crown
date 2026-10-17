"""G13 public study handbook: source-text-grounded guide, no clinical promotion.

Builds *on* G12 offline workbook, does not mutate product runtime or G12.
Six underspecified source points are UI-HOLD, no click accepted before
qualified source-operational annotation protocol / independent adjudication.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.cephalo_r23g12_public_manual_workbook import build_workbook
from scripts.cephalo_r23g10_annotation_intake import G9_REL, PROFILE, load

LEDGER = "docs/audits/schemas/cephalo_r23g13_source_specific_landmark_guides_v1.json"
ALLOWED_STATES = {"SOURCE_DESCRIBED__NOT_EXPERT_VERIFIED",
                  "HOLD__EXPERT_PIXEL_RULE_REQUIRED"}
TOP_KEYS = {"schema_version", "profile_id", "upstream_ledger", "scope",
            "source_edition", "clinical_release", "operator_anatomy_verified",
            "atlas33_measurements_validated", "independent_expert_review",
            "source_text_as_published_in_repo_not_new_primary_verification", "rows"}
ROW_KEYS = {"id", "label_fr", "definition_fr", "source_path", "evidence_excerpt",
            "forbidden_aliases", "annotation_ui_status",
            "clinical_definition_verified", "expert_consensus_complete"}
HOLD_EXPECTED = {"Ba", "FOP_MOLAR_Ricketts", "FOP_PREMOLAR_Ricketts",
                 "GO_Ricketts_PFH", "L6_DISTAL_Ricketts", "PNS_Ricketts"}
INSERT_BEFORE = '</aside></main>'
INJECT_BEFORE = '</body>'

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def validate_guide(guide, matrix, repo_root: Path):
    require(type(guide) is dict and set(guide) == TOP_KEYS, "Guide schema drift")
    require(guide["schema_version"] == "CEPHALO_R23G13_ATLAS33_SOURCE_GUIDE_V1"
            and guide["profile_id"] == PROFILE == matrix["profile_id"]
            and guide["upstream_ledger"] == G9_REL
            and guide["source_edition"] == "Atlas2009"
            and guide["scope"] == "PUBLIC_WORKBOOK_EDUCATIONAL_SOURCE_BOUND_GUIDE_ONLY",
            "Atlas33 source/edition drift")
    require(guide["clinical_release"] is False and
            guide["operator_anatomy_verified"] is False and
            guide["atlas33_measurements_validated"] == 0 and
            type(guide["atlas33_measurements_validated"]) is int and
            guide["independent_expert_review"] is False and
            guide["source_text_as_published_in_repo_not_new_primary_verification"] is True,
            "Unproven clinical authority in source guide")
    rows = guide["rows"]
    ids = matrix["identities_without_strict_mapping"]
    require(type(rows) is list and len(rows) == 21 and
            [r.get("id") if isinstance(r, dict) else None for r in rows] == ids and
            ids == sorted(set(ids)),
            "G13 must retain exact source-specific G9 identity order")
    holds = set()
    for r in rows:
        require(type(r) is dict and set(r) == ROW_KEYS, "Unknown guide fields")
        require(all(isinstance(r[x],str) and len(r[x].strip()) >= 5 for x in
                    ("label_fr", "definition_fr", "evidence_excerpt")),
                "Missing/empty anatomical explanation/evidence anchor")
        require(isinstance(r["source_path"], str) and
                r["source_path"].startswith("docs/audits/") and
                ".." not in Path(r["source_path"]).parts,
                "Unsafe external / cross-root source reference")
        source = repo_root / r["source_path"]
        require(source.is_file() and
                r["evidence_excerpt"] in source.read_text(encoding="utf-8"),
                "Anatomical definition citation is not actually in the file: " + r["id"])
        require(r["annotation_ui_status"] in ALLOWED_STATES and
                r["clinical_definition_verified"] is False and
                r["expert_consensus_complete"] is False,
                "Anatomical source must never be marked clinically verified")
        require(type(r["forbidden_aliases"]) is list and
                len(r["forbidden_aliases"]) >= 1 and
                len(set(r["forbidden_aliases"])) == len(r["forbidden_aliases"]) and
                all(isinstance(x,str) and x != r["id"] and x.strip()
                    for x in r["forbidden_aliases"]),
                "Forbidden alternatives must be meaningful distinct labels")
        if r["annotation_ui_status"].startswith("HOLD"):
            holds.add(r["id"])
    require(holds == HOLD_EXPECTED,
            "Safety gating drift: expert-operational landmark HOLD changed without review")
    return {"source_bound_identifications": 21, "human_protocol_holds": len(holds),
            "hold_ids": sorted(holds), "clinical_release": False,
            "expert_goldset_ready": False}

def overlay_html(original, guide):
    require(original.count(INSERT_BEFORE) == 1 and
            original.count(INJECT_BEFORE) == 1 and
            'id="tracing"' in original and 'id="landmark"' in original,
            "G12 workbook extension anchor missing")
    html = original.replace(INSERT_BEFORE, """<hr>
    <section id="source-guide" data-testid="source-guide" aria-label="Définition du repère">
    <h2>Fiche de repérage source</h2>
    <p id="g13-label" data-testid="guide-label"></p>
    <p id="g13-state" data-testid="guide-status" class="note"></p>
    <p id="g13-meaning" data-testid="guide-meaning"></p>
    <p id="g13-aliases" data-testid="guide-aliases"></p>
    <p id="g13-evidence" data-testid="guide-evidence" class="small"></p>
    <p id="g13-source" data-testid="guide-source" class="small"></p>
    <p class="note">G13 : six placements en HOLD jusqu'à validation du protocole opératoire.
    Aucune fiche source ne prouve la justesse d'un point, la calibration ou l'identité d'un expert.</p>
    </section></aside></main>""")
    safe = json.dumps(guide, ensure_ascii=False, separators=(",", ":")) \
        .replace("<", "\\u003c").replace(">", "\\u003e") \
        .replace("&", "\\u0026")
    addon = """
<script>
"use strict";
const G13_GUIDE = /*__G13_GUIDE_DATA__*/;
const G13_MAP = new Map(G13_GUIDE.rows.map(r => [r.id,r]));
function g13Render(){
 const row=G13_MAP.get(document.getElementById("landmark").value);
 if(!row)throw Error("G13 missing source-specific landmark guide");
 document.getElementById("g13-label").textContent=row.label_fr+" ("+row.id+")";
 const hold=row.annotation_ui_status==="HOLD__EXPERT_PIXEL_RULE_REQUIRED";
 document.getElementById("g13-state").textContent=hold
  ?"HOLD — règle de clic clinique insuffisante, placement désactivé."
  :"Description documentée dans le dépôt — placement de recherche NON VÉRIFIÉ.";
 document.getElementById("g13-meaning").textContent=row.definition_fr;
 document.getElementById("g13-aliases").textContent="Substitutions interdites : "+row.forbidden_aliases.join(", ");
 document.getElementById("g13-evidence").textContent="Passage probant : "+row.evidence_excerpt;
 document.getElementById("g13-source").textContent="Source dépôt : "+row.source_path;
 document.getElementById("g13-state").dataset.hold=String(hold);
}
document.getElementById("landmark").addEventListener("change",g13Render);
document.getElementById("tracing").addEventListener("click",e=>{
 const row=G13_MAP.get(document.getElementById("landmark").value);
 if(!row||row.annotation_ui_status!=="SOURCE_DESCRIBED__NOT_EXPERT_VERIFIED"){
   e.stopImmediatePropagation();
   e.preventDefault();
   document.getElementById("status").textContent=
    "HOLD source G13 : annotation de ce repère interdite sans règle opératoire approuvée.";
 }
},true);
g13Render();
</script>
""".replace("/*__G13_GUIDE_DATA__*/",safe)
    html = html.replace(INJECT_BEFORE, addon + INJECT_BEFORE)
    return html

def build(repo_root:Path,input_dir:Path,output_dir:Path):
    guide = load(repo_root/LEDGER)
    matrix = load(repo_root/G9_REL)
    source_check = validate_guide(guide,matrix,repo_root)
    _,g12_proof=build_workbook(repo_root,input_dir,output_dir)
    index = output_dir/"index.html"
    index.write_text(overlay_html(index.read_text(encoding="utf-8"),guide),
                     encoding="utf-8")
    report = {"schema_version":"CEPHALO_R23G13_SOURCE_GUIDED_PUBLIC_WORKBOOK_BUILD_V1",
              "real_public_originals_verified":g12_proof["case_count"]==2,
              "identity_count":source_check["source_bound_identifications"],
              "operative_pixel_definition_holds":source_check["human_protocol_holds"],
              "held_source_identities":source_check["hold_ids"],
              "annotations_by_actual_qualified_clinicians":0,
              "image_calibration_verified":False,
              "image_orientation_verified":False,
              "clinical_release":False,
              "atlas33_measurements_validated":0,
              "note":"Source-bound definitions are repo-grounded; not independently assessed by orthodontists."}
    (output_dir/"G13_SOURCE_GUIDE_ONLY_REPORT.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n",
        encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--input-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build(a.repo_root,a.input_dir,a.output_dir),indent=2,
                     ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    main()
