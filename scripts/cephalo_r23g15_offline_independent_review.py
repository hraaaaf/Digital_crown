"""R23-G15 -- OFFLINE preparation/comparison for actual A/B orthodontist review.

NO clinical verdict can be derived from this script, even from two perfectly
matching reports: credentials, independence, source edition, signatures,
calibration, images and anatomical correctness require separate human proof.
Do not put completed review files (or operator identifiers) in GitHub/CI.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from scripts.cephalo_r23g10_annotation_intake import G9_REL, load
from scripts.cephalo_r23g13_public_source_guided_workbook import LEDGER as G13_LEDGER
from scripts.cephalo_r23g14_six_hold_review_workbook import REVIEW_PACK,verify_packet

SCHEMA = "CEPHALO_R23G15_INDEPENDENT_SOURCE_REVIEW_V1"
PROFILE = "RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1"
G14_SOURCE_HEAD="8bae23324bfd580bcce3b82e30e76874f86f2110"
DECISIONS = ("HOLD_UNRESOLVED", "RULE_PROPOSED_FOR_ADJUDICATION",
             "REJECTED_AS_NON_EQUIVALENT", "NOT_VISIBLE_IN_PUBLIC_IMAGES")
TOP = {"schema_version","profile_id","g14_parent_head_sha","scope","role",
       "reviewer_token","human_credentials_externally_verified","actual_signature_externally_verified",
       "clinical_release","cases"}
ROW = {"id","status","atlas_ch13_page_or_figure","proposed_pixel_rule",
       "ambiguity_and_not_visible_policy","answers_to_three_questions"}
TOKEN = re.compile(r"[A-Za-z0-9_-]{3,48}\Z")
SCHEME_SCOPE = "SIX_HOLD_PRIMARY_ATLAS_SOURCE_RULE_REVIEW__NOT_ANNOTATION"
PLACEHOLDER="REQUIRES_INDEPENDENT_HUMAN_REVIEW"
END_STATUS="STRUCTURE_COMPARISON_ONLY__EXTERNAL_HUMAN_GOVERNANCE_REQUIRED"

def demand(ok,why):
    if not ok:raise ValueError(why)

def exact(value,keys,where):
    demand(type(value) is dict and set(value)==keys,where+" unexpected/missing keys")
    return value

def baseline(repo_root:Path):
    matrix,g13,g14=(load(repo_root/p) for p in (G9_REL,G13_LEDGER,REVIEW_PACK))
    verified=verify_packet(g14,g13,matrix,repo_root)
    demand(verified["review_dossiers"]==6 and verified["clinical_release"] is False
           and verified["independent_orthodontist_signatures_verified"]==0
           and verified["all_six_remaining_hold"] is True,
           "G14 source authority drift")
    return g14

def blank(role,packet):
    demand(role in ("A","B"),"Only blind reviewer roles A/B are supported")
    return {
        "schema_version":SCHEMA,
        "profile_id":PROFILE,
        "g14_parent_head_sha":G14_SOURCE_HEAD,
        "scope":SCHEME_SCOPE,
        "role":role,
        "reviewer_token":"",
        "human_credentials_externally_verified":False,
        "actual_signature_externally_verified":False,
        "clinical_release":False,
        "cases":[{
          "id":card["id"],
          "status":"HOLD_UNRESOLVED",
          "atlas_ch13_page_or_figure":"",
          "proposed_pixel_rule":"",
          "ambiguity_and_not_visible_policy":"",
          "answers_to_three_questions":["","",""],
        } for card in packet["cards"]],
    }

def check_review(review,role,packet):
    exact(review,TOP,"Reviewer document")
    demand(review["schema_version"]==SCHEMA and
           review["profile_id"]==PROFILE and
           review["g14_parent_head_sha"]==G14_SOURCE_HEAD and
           review["scope"]==SCHEME_SCOPE and review["role"]==role,
           "Reviewer A/B scientific source/protocol drift")
    token=review["reviewer_token"]
    demand(type(token) is str and TOKEN.fullmatch(token) is not None,
           "Opaque reviewer token required (no real name/email)")
    demand(review["human_credentials_externally_verified"] is False
           and review["actual_signature_externally_verified"] is False
           and review["clinical_release"] is False,
           "A form cannot certify real identities/signatures/clinical release")
    cases=review["cases"]
    expected=[c["id"] for c in packet["cards"]]
    demand(type(cases) is list and len(cases)==6 and
           all(type(x) is dict for x in cases) and
           [x.get("id") for x in cases]==expected,
           "All six source-locked HOLDs, in fixed order, are required")
    for case in cases:
        exact(case,ROW,"HOLD review")
        demand(case["status"] in DECISIONS,"Unknown reviewer conclusion")
        answers=case["answers_to_three_questions"]
        demand(type(answers) is list and len(answers)==3
               and all(type(s) is str and len(s.strip())>=16 and len(s)<2000
                       for s in answers),
               "Three real explanatory answers per HOLD required")
        rule=case["proposed_pixel_rule"]
        ambiguity=case["ambiguity_and_not_visible_policy"]
        primary=case["atlas_ch13_page_or_figure"]
        demand(all(type(v) is str and len(v)<2000 for v in
                   (rule,ambiguity,primary)) and
               len(ambiguity.strip())>=20,
               "Missing or excessively long pixel ambiguity/not-visible policy")
        # A specific rule requires exact Atlas edition page/figure and an explicit
        # actionable procedure; neither is verified by this structural validator.
        if case["status"]=="RULE_PROPOSED_FOR_ADJUDICATION":
            demand(len(primary.strip())>=8 and
                   primary.strip()!=PLACEHOLDER and
                   len(rule.strip())>=40,
                   "Proposed rule requires Atlas2009 reference and concrete text")
        else:
            demand(len(rule)<2000,"Invalid rule")
    return {c["id"]:c["status"] for c in cases}

def compare(a,b,packet):
    a_status=check_review(a,"A",packet)
    b_status=check_review(b,"B",packet)
    demand(a["reviewer_token"]!=b["reviewer_token"],
           "Same pseudonymous reviewer token cannot play both roles")
    rows=[]
    for card in packet["cards"]:
        id=card["id"]
        x,y=a_status[id],b_status[id]
        rows.append({"id":id,"reviewer_status_agreement":x==y,
          "a_status":x,"b_status":y,
          "both_proposed_procedure_for_future_adjudication":
             x==y=="RULE_PROPOSED_FOR_ADJUDICATION",
          "clinical_rule_approved":False,
          "source_hold_retained":True})
    return {
       "schema_version":"CEPHALO_R23G15_BLINDED_REVIEW_COMPARISON_AGGREGATE_V1",
       "scope":"SOURCE_RULE_METADATA_ONLY__NO_REVIEWER_NAMES_OR_RAW_ANSWERS",
       "six_cases_compared":6,
       "status_agreement_count":sum(r["reviewer_status_agreement"] for r in rows),
       "status_disagreement_count":sum(not r["reviewer_status_agreement"] for r in rows),
       "real_reviewer_qualifications_verified":False,
       "independence_of_actual_people_verified":False,
       "actual_signatures_verified":0,
       "same_image_manual_landmarks_verified":0,
       "image_calibration_verified":False,
       "image_orientation_verified":False,
       "clinically_unlocked_hold_count":0,
       "atlas33_clinical_measurements_validated":0,
       "clinical_release":False,
       "status":END_STATUS,
       "cases":rows,
       "note":"Even matching text is not independent clinical proof; require protected, real signed expert dossier.",
    }

def html_form(role,packet):
    # Only repository-controlled scientific and non-personal strings are embedded;
    # no image/coordinates/real identity is embedded. External network is disabled.
    form=blank(role,packet)
    catalog=[{"id":c["id"],"source_path":c["source_lock_path"],
              "questions":c["provisional_questionnaire_fr"]} for c in packet["cards"]]
    data=json.dumps({"template":form,"catalog":catalog},ensure_ascii=False)\
        .replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
    return r'''<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; form-action 'none'; object-src 'none'; base-uri 'none'">
<title>Digital Crown G15 — Revue aveugle ROLE_PLACEHOLDER</title>
<style>
:root{font-family:system-ui,Arial;color:#17293a;background:#f2f6fa}
*{box-sizing:border-box}body{margin:0}header{background:#15354c;color:white;padding:22px}
main{max-width:960px;margin:auto;padding:16px}h1{margin:0 0 5px;font-size:22px}
p,li{font-size:14px;line-height:1.5}article{background:white;border:1px solid #abc0d0;border-radius:12px;padding:17px;margin:14px 0}
fieldset{border:0;padding:0;margin:0}label{display:block;font-weight:650;margin-top:13px}
input,select,textarea{display:block;width:100%;font:inherit;border:1px solid #7190a5;border-radius:7px;padding:9px;margin-top:6px;background:white;color:#17293a}
textarea{min-height:70px}button{font:inherit;background:#087e92;color:white;padding:12px 20px;border:0;border-radius:7px;cursor:pointer}
.warning{color:#933b00;font-weight:700}header .warning{color:#ffe2a0}
small{font-size:12px}@media(max-width:560px){main{padding:8px}article{padding:12px}}
</style></head><body><header><h1>G15 · Relecture indépendante ROLE_PLACEHOLDER</h1>
<p class="warning">FORMULAIRE HORS-LIGNE · NE PROUVE PAS UNE SIGNATURE NI L'EXPERTISE CLINIQUE</p>
<p>Un seul examinateur pour cette session ; réponses à conserver en espace protégé.
Ne consultez ni réponses de l'autre examinateur, ni exemples de clics CI.</p></header>
<main><p>Références de chapitre et règles anatomiques à confirmer dans l'édition Atlas2009 autorisée.
Aucun patient, aucune image ni coordonnée dans ce fichier. Les six repères restent en HOLD.</p>
<label for="token">Jeton pseudonyme distinct A/B (pas de nom réel)</label>
<input id="token" data-testid="token" autocomplete="off" spellcheck="false" maxlength="48">
<div id="forms"></div>
<button id="save" data-testid="save">Exporter les réponses locales ROLE_PLACEHOLDER (.json)</button>
<p id="status" role="status" data-testid="status"></p>
</main><script>
"use strict";
const PACK=DATA_PLACEHOLDER;
const dest=document.getElementById("forms");
const esc=s=>s;
for(const [i,card] of PACK.catalog.entries()){
 const art=document.createElement("article");art.dataset.id=card.id;
 const head=document.createElement("h2");head.textContent=(i+1)+". "+card.id;art.append(head);
 const cite=document.createElement("p");cite.textContent="Source dépôt : "+card.source_path;art.append(cite);
 const makeField=(caption,tag,field,entries)=>{
   const label=document.createElement("label");label.textContent=caption;
   const el=document.createElement(tag);
   el.dataset.field=field;el.dataset.id=card.id;
   if(tag==="select"){for(const v of entries){const o=document.createElement("option");o.value=v;o.textContent=v;el.append(o);}}
   label.append(el);art.append(label);return el;
 };
 makeField("État de la règle (aucune validation clinique)", "select","status",
   ["HOLD_UNRESOLVED","RULE_PROPOSED_FOR_ADJUDICATION","REJECTED_AS_NON_EQUIVALENT","NOT_VISIBLE_IN_PUBLIC_IMAGES"]);
 makeField("Référence exacte Atlas2009 chapitre 13, page/figure (si proposition)", "input","atlas_ch13_page_or_figure");
 makeField("Règle opératoire candidate, décrite sans ambiguïté (si proposition)", "textarea","proposed_pixel_rule");
 makeField("Politique contours doubles, non visible, exclusions", "textarea","ambiguity_and_not_visible_policy");
 for(const [qidx,q] of card.questions.entries()){
   makeField("Question "+(qidx+1)+" : "+q,"textarea","answer_"+qidx);
 }
 dest.append(art);
}
document.getElementById("save").addEventListener("click",()=>{
 const token=document.getElementById("token").value.trim();
 const status=document.getElementById("status");
 if(!/^[A-Za-z0-9_-]{3,48}$/.test(token)){
   status.textContent="Jeton non valide : 3–48 caractères A-Z/a-z/0-9/_/-.";return;
 }
 const payload=structuredClone(PACK.template);
 payload.reviewer_token=token;
 payload.cases=PACK.catalog.map(card=>{
   const row={...payload.cases.find(c=>c.id===card.id)};
   for(const key of ["status","atlas_ch13_page_or_figure","proposed_pixel_rule","ambiguity_and_not_visible_policy"]){
      row[key]=document.querySelector('[data-id="'+card.id+'"][data-field="'+key+'"]').value.trim();
   }
   row.answers_to_three_questions=[0,1,2].map(i=>
      document.querySelector('[data-id="'+card.id+'"][data-field="answer_'+i+'"]').value.trim());
   return row;
 });
 const incomplete=payload.cases.find(r=>r.answers_to_three_questions.some(s=>s.length<16)
    ||r.ambiguity_and_not_visible_policy.length<20
    ||(r.status==="RULE_PROPOSED_FOR_ADJUDICATION"&&
      (r.atlas_ch13_page_or_figure.length<8||r.proposed_pixel_rule.length<40)));
 if(incomplete){status.textContent="Réponses manquantes pour "+incomplete.id+" ; aucun export.";return;}
 const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)+"\n"],{type:"application/json"}));
 const a=document.createElement("a");a.href=url;a.download="G15_REVIEW_"+PACK.template.role+"_"+token+".json";
 document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);
 status.textContent="Export local créé. Garder ce dossier privé ; validation humaine indépendante toujours requise.";
});
</script></body></html>'''.replace("ROLE_PLACEHOLDER",role).replace("DATA_PLACEHOLDER",data)

def prepare(repo_root:Path,out:Path,packet):
    root=repo_root.resolve();output=out.resolve()
    demand(output!=root and not output.is_relative_to(root),
           "Private output must stay outside Git repository")
    demand(not output.exists() or (output.is_dir() and not any(output.iterdir())),
           "Refuse to overwrite prior private reviewer submissions")
    output.mkdir(parents=True,exist_ok=True)
    for role in ("A","B"):
        sub=output/role
        sub.mkdir()
        (sub/"independent_review.html").write_text(html_form(role,packet),encoding="utf-8")
    (output/"PRIVATE_REVIEW_INSTRUCTIONS.txt").write_text(
        "Keep A and B in distinct access-controlled folders; give ONLY the corresponding HTML to each reviewer.\n"
        "The forms are local and require manual export. Reviewer token is NOT identity or signature proof.\n"
        "Never upload real submissions/credential documents to GitHub Actions, a PR, Notion or a public chat.\n"
        "Do not unlock any six source HOLDs based on self-reported form fields.\n",encoding="utf-8")
    return {"private_review_forms_prepared":2,"hold_ids":[c["id"] for c in packet["cards"]],
            "real_reviews_collected":0,"clinical_release":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1])
    args=p.add_subparsers(dest="mode",required=True)
    prep=args.add_parser("prepare");prep.add_argument("--private-output-dir",type=Path,required=True)
    comp=args.add_parser("compare");comp.add_argument("--review-a",type=Path,required=True)
    comp.add_argument("--review-b",type=Path,required=True)
    comp.add_argument("--aggregate-out",type=Path)
    a=p.parse_args()
    packet=baseline(a.repo_root)
    if a.mode=="prepare":
        result=prepare(a.repo_root,a.private_output_dir,packet)
    else:
        result=compare(load(a.review_a),load(a.review_b),packet)
        if a.aggregate_out:
            path=a.aggregate_out.resolve()
            demand(not path.is_relative_to(a.repo_root.resolve()),
                   "Cannot write even aggregate review to tracked repo")
            demand(not path.exists(),"Do not overwrite existing review aggregate")
            path.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                            encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=="__main__":main()
