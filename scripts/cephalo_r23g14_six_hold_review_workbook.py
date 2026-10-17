"""G14 independent-review *preparation*, NOT an independent expert review.

Reads source-locked G13 guides, G14 six immutable HOLD dossiers and original
two public G11 JPEGs; builds a local read-only review panel. It must NEVER
release clinical references, unlock a point, or claim two signed experts.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from scripts.cephalo_r23g10_annotation_intake import G9_REL, load
from scripts.cephalo_r23g13_public_source_guided_workbook import (
    LEDGER as G13_LEDGER, HOLD_EXPECTED, build as build_g13, validate_guide,
)

REVIEW_PACK="docs/audits/schemas/cephalo_r23g14_six_hold_expert_adjudication_v1.json"
TOP_KEYS={
    "schema_version","source_profile_id","upstream_g13_ledger","scientific_status",
    "local_atlas_primary_source_chapter_manually_checked",
    "independent_reviewer_credentials_verified","independent_reviewer_a_signed",
    "independent_reviewer_b_signed","image_calibration_verified",
    "image_orientation_verified","clinical_release","atlas33_clinical_measurements_validated",
    "external_sources_are_scope_limited_general_evidence","hold_count",
    "unlockable_hold_ids","cards"
}
CARD_KEYS={"id","source_lock_path","source_lock_excerpt","current_definition_fr",
           "interpretation_status","proposed_annotation_rule_is_not_authoritative",
           "provisional_questionnaire_fr","candidate_rule_for_expert_discussion_only_fr",
           "unresolved_reason_en","external_corroboration_not_atlas_authority",
           "extra_forbidden_aliases","reviewer_a_independent_source_check",
           "reviewer_b_independent_source_check","illustrated_example_source_locked",
           "ambiguity_and_not_visible_policy_accepted","interobserver_consensus_verified",
           "clinical_use_authorized","decision"}
EXTERNAL_KEYS={"url","kind","scope"}
ALLOWED_DOMAINS={"pubmed.ncbi.nlm.nih.gov","www.ncbi.nlm.nih.gov","pmc.ncbi.nlm.nih.gov"}
HOLD_STATUS="HOLD__EXTERNAL_HUMAN_ADJUDICATION_REQUIRED"

def require(condition,reason):
    if not condition:raise ValueError(reason)

def exact(value,keys,reason):
    require(type(value) is dict and set(value)==keys,reason+" keys drift")
    return value

def verify_packet(packet,g13,matrix,repo_root:Path):
    exact(packet,TOP_KEYS,"G14")
    require(packet["schema_version"]=="CEPHALO_R23G14_ATLAS33_SIX_HOLD_REVIEW_PACK_V1"
            and packet["source_profile_id"]==matrix["profile_id"]==g13["profile_id"]
            and packet["upstream_g13_ledger"]==G13_LEDGER
            and packet["scientific_status"]=="DOCUMENTARY_CORROBORATION_ONLY__NO_ATLAS_PIXEL_CONVERGENCE",
            "Profile/status edition drift")
    for key in ("local_atlas_primary_source_chapter_manually_checked",
                "independent_reviewer_credentials_verified",
                "independent_reviewer_a_signed","independent_reviewer_b_signed",
                "image_calibration_verified","image_orientation_verified","clinical_release"):
        require(packet[key] is False,"Cannot self-assert "+key)
    require(type(packet["atlas33_clinical_measurements_validated"]) is int and
            packet["atlas33_clinical_measurements_validated"]==0 and
            packet["external_sources_are_scope_limited_general_evidence"] is True and
            type(packet["hold_count"]) is int and packet["hold_count"]==6 and
            packet["unlockable_hold_ids"]==[],
            "Clinical authority, HOLD membership or source scope drift")
    ids=matrix["identities_without_strict_mapping"]
    require(len(ids)==21 and matrix["clinical_release"] is False
            and matrix["semantic_aliasing_authorized"] is False,
            "G9 source authority drift")
    validate_guide(g13,matrix,repo_root)
    guides={r["id"]:r for r in g13["rows"]}
    require(type(packet["cards"]) is list and len(packet["cards"])==6
            and [c.get("id") for c in packet["cards"] if type(c) is dict]==sorted(HOLD_EXPECTED),
            "Six source-specific HOLD identities must remain exact, unique, sorted")
    for c in packet["cards"]:
        exact(c,CARD_KEYS,"Review card")
        guide=guides[c["id"]]
        require(guide["annotation_ui_status"]=="HOLD__EXPERT_PIXEL_RULE_REQUIRED"
                and c["source_lock_path"]==guide["source_path"]
                and c["source_lock_excerpt"]==guide["evidence_excerpt"]
                and c["current_definition_fr"]==guide["definition_fr"]
                and c["interpretation_status"]=="ANATOMICAL_CONCEPT_ONLY__PIXEL_RULE_UNPROVEN"
                and c["proposed_annotation_rule_is_not_authoritative"] is True
                and c["decision"]==HOLD_STATUS,
                "G13 baseline/source lock/annotation clinical equivalence drift")
        require(all(c[k] is False for k in (
            "reviewer_a_independent_source_check","reviewer_b_independent_source_check",
            "illustrated_example_source_locked","ambiguity_and_not_visible_policy_accepted",
            "interobserver_consensus_verified","clinical_use_authorized")),
            "False approval of a source-specific landmark")
        require(type(c["provisional_questionnaire_fr"]) is list
                and len(c["provisional_questionnaire_fr"])==3
                and all(type(q) is str and len(q.strip())>25 for q in c["provisional_questionnaire_fr"])
                and type(c["candidate_rule_for_expert_discussion_only_fr"]) is str
                and len(c["candidate_rule_for_expert_discussion_only_fr"])>50
                and type(c["unresolved_reason_en"]) is str
                and len(c["unresolved_reason_en"])>40,
                "Missing concrete human tasks or explicit uncertainty")
        aliases=c["extra_forbidden_aliases"]
        require(type(aliases) is list and len(aliases)>=3
                and all(type(x) is str and x!=c["id"] and len(x)>1 for x in aliases)
                and len(set(aliases))==len(aliases),
                "Forbidden alias explanations incomplete")
        source=repo_root/c["source_lock_path"]
        require(source.is_file() and c["source_lock_excerpt"] in source.read_text(encoding="utf8"),
                "Source citation no longer present at exact checkout")
        sources=c["external_corroboration_not_atlas_authority"]
        require(type(sources) is list and len(sources)>=1,
                "At least one scoped corroboration source required")
        for external in sources:
            exact(external,EXTERNAL_KEYS,"External evidence")
            url=external["url"]
            parsed=urlsplit(url)
            require(parsed.scheme=="https" and parsed.hostname in ALLOWED_DOMAINS
                    and parsed.username is None and parsed.password is None and parsed.port is None
                    and parsed.query=="" and parsed.fragment=="" and
                    len(external["scope"])>45 and len(external["kind"])>12,
                    "Untrusted or inadequately scoped external evidence URL")
    return {"schema_version":"CEPHALO_R23G14_SIX_HOLD_QA_V1",
            "source_guides_cross_checked":21,"review_dossiers":6,
            "operational_rules_human_approved":0,
            "independent_orthodontist_signatures_verified":0,
            "atlas33_clinical_measurements_validated":0,
            "clinical_release":False,"all_six_remaining_hold":True}

def add_review_cards(html,packet):
    marker="</aside></main>"
    insertion='''<hr><section id="g14-arbitration" data-testid="g14-arbitration">
<h2>Dossier d’arbitrage G14 — validation humaine requise</h2>
<p class="note">Six repères restent en HOLD. Sources générales ≠ définition Atlas2009
exacte ; aucune validation de position ou de calibration.</p>
<p id="g14-status" data-testid="g14-status"></p>
<p id="g14-question" data-testid="g14-question"></p>
<ul id="g14-questions" data-testid="g14-questions"></ul>
<p id="g14-references" data-testid="g14-references"></p>
<p class="small">Candidats destinés aux 2 orthodontistes indépendants — pas un bouton d’approbation.</p>
</section></aside></main>'''
    require(html.count(marker)==1 and html.count('id="source-guide"')==1,
            "G13 generated HTML not present")
    html=html.replace(marker,insertion)
    safe=json.dumps(packet,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
    script=r'''<script>
"use strict";
const G14_PACK=/*__G14_PACKET__*/;
function renderG14(){
 const id=document.getElementById("landmark").value;
 const c=G14_PACK.cards.find(c=>c.id===id);
 const status=document.getElementById("g14-status"),
       question=document.getElementById("g14-question"),
       questions=document.getElementById("g14-questions"),
       references=document.getElementById("g14-references");
 questions.replaceChildren();
 if(!c){
  status.textContent="Ce point est décrit en G13, mais n'appartient pas aux 6 règles en HOLD G14.";
  question.textContent="Pas d'arbitrage G14 applicable; le statut du clic reste DRAFT.";
  references.textContent="";
  return;
 }
 status.textContent="HOLD explicite — 0/2 validations expertes indépendantes.";
 question.textContent="Hypothèse de discussion NON AUTORITATIVE : "+c.candidate_rule_for_expert_discussion_only_fr;
 for(const q of c.provisional_questionnaire_fr){
   const li=document.createElement("li");li.textContent=q;questions.append(li);
 }
 references.textContent="Sources externes limitées à leur périmètre : "+
   c.external_corroboration_not_atlas_authority.map(e=>e.url+" ["+e.scope+"]").join(" | ");
}
document.getElementById("landmark").addEventListener("change",renderG14);
renderG14();
</script>'''.replace("/*__G14_PACKET__*/",safe)
    require(html.count("</body>")==1,"Malformed HTML body boundary")
    return html.replace("</body>",script+"</body>")

def build(repo_root:Path,input_dir:Path,output_dir:Path):
    g13=load(repo_root/G13_LEDGER)
    matrix=load(repo_root/G9_REL)
    pack=load(repo_root/REVIEW_PACK)
    proof=verify_packet(pack,g13,matrix,repo_root)
    from scripts.cephalo_r23g13_public_source_guided_workbook import build as build_g13_inner
    g13_report=build_g13_inner(repo_root,input_dir,output_dir)
    require(g13_report["operative_pixel_definition_holds"]==6,
            "G13 source HOLD gate unverified")
    page=output_dir/"index.html"
    page.write_text(add_review_cards(page.read_text(encoding="utf-8"),pack),encoding="utf-8")
    (output_dir/"G14_HUMAN_REVIEW_PACK_QA_ONLY.json").write_text(
       json.dumps(proof,indent=2,sort_keys=True,ensure_ascii=False)+"\n",
       encoding="utf-8")
    return proof

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--input-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build(a.repo_root,a.input_dir,a.output_dir),indent=2,ensure_ascii=False))
if __name__=="__main__":main()
