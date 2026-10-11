#!/usr/bin/env python3
"""Research-only Git-blob-pinned static provenance audit for legacy ANB.

This does not start a clinical service, authenticate a patient, or certify FACAD
operator equivalence. Fail closed if any source or route assumption changes.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
PINS = {
 "backend/services/cephalo_engine.py": "240e938a6618557c9630fee8b5e9b49e18b6403c",
 "backend/services/cephalo_safe_engine.py": "9b0957f298d1cb3b98e38889bac813c34db4ee04",
 "backend/services/cephalo_service.py": "2e3c05d38d380d3f486d742281374272346b9a5b",
 "backend/services/cephalo_runtime_evidence.py": "ee82322369291d85b0f93338292196cb61f4b6e5",
 "backend/services/cephalo_runtime_chain.py": "2d35d68173e0b3571e88a045ce3722b4cdd98a5a",
 "backend/services/cephalo_typed_read.py": "4a241dcd22e27c63f4c459282aa685bf94fd9889",
 "backend/routers/cephalo_analysis_read.py": "3917e73bb9092a6d6d23273cf22c94032f9aaa68",
 "backend/routers/__init__.py": "bf11bafccf432a0e52310ab2178c59cff4545d96",
 "backend/main.py": "7d1eb7c6865213f6ed669429aa4ea05a51a4ba2f",
 "frontend/src/features/ortho/stores/useOrthoStore.ts": "5dd1373bb4d756d9dc0e085c965b584738106fdc",
 "frontend/src/features/ortho/cephaloRepository.ts": "ac0724c462aace7bb04697ac745f2e6eb998f766",
 "frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx": "c2b3b3337bd6aa99cd6b977811749fce561a5b22",
 "frontend/src/features/ortho/cephaloSteinerProtocol.ts": "9f98d71ead8599bc0587ddbb6e90fe0091800082",
}
def blob_sha(data: bytes) -> str:
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def read_verified():
 found={}
 for path,pin in PINS.items():
  file=(ROOT/path).resolve(strict=True)
  if not file.is_relative_to(ROOT.resolve()):
   raise ValueError("Source escaped checkout")
  raw=file.read_bytes()
  actual=blob_sha(raw)
  if actual!=pin: raise ValueError("Source drift at "+path)
  if path.endswith(".py"): ast.parse(raw.decode("utf-8"),filename=path)
  found[path]=raw.decode("utf-8")
 return found

def craniom_fields(source):
 tree=ast.parse(source)
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="_CRANIOM_METHOD_TO_LEGACY_FIELD" for t in node.targets):
   fields=ast.literal_eval(node.value)
   if not isinstance(fields,dict): raise ValueError("Invalid fields shape")
   return fields
 raise ValueError("Missing CRANIOM map")

def assertions_of(src):
 def checked(path,needle):
  if needle not in src[path]: raise ValueError("Lost source chain link: "+path+" :: "+needle[:60])
  return path+":"+needle[:50]
 out=[]
 def ok(path,needle):out.append(checked(path,needle))
 ok("backend/services/cephalo_engine.py",'skeletal["ANB"] = self._raw_measurement(')
 ok("backend/services/cephalo_engine.py",'sna - snb if sna is not None and snb is not None else None')
 ok("backend/services/cephalo_engine.py","math.acos(cosine)")
 ok("backend/services/cephalo_safe_engine.py","_legacy_cephalo_engine.calculate_metrics(*args, **kwargs)")
 ok("backend/services/cephalo_service.py","result = cephalo_engine.calculate_metrics(")
 ok("backend/services/cephalo_runtime_evidence.py",'"legacy_angles_data_role": "COMPATIBILITY_OUTPUT"')
 ok("backend/services/cephalo_runtime_chain.py","project_typed_craniom_read_path(angles_data, patient_id=patient_id)")
 ok("backend/services/cephalo_runtime_chain.py",'"active_chain": "VERIFIED"')
 ok("backend/services/cephalo_typed_read.py","projected = deepcopy(dict(angles_data))")
 ok("backend/routers/cephalo_analysis_read.py","out.angles_data = project_runtime_chain_read_path(")
 ok("backend/routers/cephalo_analysis_read.py","status_code=409")
 ok("backend/routers/__init__.py","ia.router.include_router(cephalo_analysis_read.router)")
 ok("backend/main.py",'app.include_router(ia.router, prefix="/api/ia"')
 ok("frontend/src/features/ortho/cephaloRepository.ts","api.get(\`/ia/analyses/\${analysisId}\`)")
 ok("frontend/src/features/ortho/stores/useOrthoStore.ts","anglesData: { ...refreshedAngles, __calibrationData: authoritativeRead.calibration_data || null }")
 ok("frontend/src/features/ortho/stores/useOrthoStore.ts","set({ anglesData: data.results })")
 ok("frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx","all: ['SNA','SNB','ANB'")
 ok("frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx","steiner: ['M_SNA_DEG_V1','M_SNB_DEG_V1','M_ANB_DEG_V1'")
 ok("frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx","const metrics = anglesData?.metrics ?? anglesData?.result?.metrics ?? {};")
 ok("frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx","return section?.[definition.key];")
 ok("frontend/src/features/ortho/cephaloSteinerProtocol.ts","scientific?.active_chain !== 'VERIFIED'")
 return out

def audit():
 src=read_verified()
 fields=craniom_fields(src["backend/services/cephalo_typed_read.py"])
 if len(fields)!=4 or "ANB" in fields.values():
  raise ValueError("ANB unexpectedly promoted to typed CRANIOM legacy override")
 if set(fields.values())!={"Situation_A","Situation_B","Decalage_A_B","Profondeur_Faciale"}:
  raise ValueError("CRANIOM override list changed")
 out=assertions_of(src)
 return {
  "schema":"FACAD_F01_13_ANB_LEGACY_SOURCE_PROVENANCE_V1",
  "verified_git_blob_pins":PINS,
  "source_assertions":out,
  "typed_craniom_legacy_overrides":fields,
  "anb_part_of_typed_craniom_override":False,
  "legacy_anb_origin":"CephaloEngine.calculate_metrics -> SNA-SNB rounded unsigned acos source",
  "safe_engine":"delegates to legacy geometric engine; removes normative metadata",
  "repository":"stores angles_data with evidence graph; read path projects typed chain",
  "http_get":"GET /api/ia/analyses/{analysisId} maps to canonical typed-read router (static route inspection)",
  "canonical_read":"project_runtime_chain_read_path verifies persisted active evidence; does not replace legacy ANB",
  "frontend_legacy_mode":"All reads anglesData.metrics.analyse_osseuse.ANB directly",
  "frontend_steiner_mode":"Steiner M_ANB_DEG_V1 reads source-gated protocol projection",
  "legacy_role_in_evidence_graph":"COMPATIBILITY_OUTPUT",
  "real_api_login_and_db_tested":False,
  "facad_numeric_parity_tested":False,
  "clinical_defect_confirmed":False,
  "f01_13":"OPEN","fac03_d3":"OPEN_RED","fac05":"NOT_TESTED","clinical_edit_allowed":False,
 }
class ProvenanceTests(unittest.TestCase):
 def test_pin_verification(self): self.assertEqual(len(read_verified()),13)
 def test_override_scope(self): self.assertFalse(audit()["anb_part_of_typed_craniom_override"])
 def test_source_path_assertions(self): self.assertEqual(len(audit()["source_assertions"]),21)
 def test_anti_source_tamper(self):
  self.assertNotEqual(blob_sha(b"tampered"),next(iter(PINS.values())))
 def test_source_missing_legacy_endpoint_fails(self):
  s=read_verified();p="frontend/src/features/ortho/cephaloRepository.ts"
  s[p]=s[p].replace("api.get(\`/ia/analyses/\${analysisId}\`)","api.get('/alternate')")
  with self.assertRaises(ValueError): assertions_of(s)
 def test_anti_false_vendor_claim(self):
  a=audit();self.assertFalse(a["facad_numeric_parity_tested"]);self.assertFalse(a["clinical_edit_allowed"])
 def test_source_map_explicit(self):
  fields=craniom_fields(read_verified()["backend/services/cephalo_typed_read.py"])
  self.assertFalse("ANB" in fields.values())
 def test_report_only_withheld(self):
  self.assertFalse(audit()["real_api_login_and_db_tested"])

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--self-test",action="store_true");ap.add_argument("--report",type=Path)
 args=ap.parse_args()
 if not args.self_test and not args.report:ap.error("provide --self-test or --report")
 if args.self_test:
  s=unittest.defaultTestLoader.loadTestsFromTestCase(ProvenanceTests)
  res=unittest.TextTestRunner(verbosity=1).run(s)
  if not res.wasSuccessful():raise SystemExit(1)
  print("ANB_LEGACY_PROVENANCE_TESTS="+str(res.testsRun))
 if args.report:
  a=audit();args.report.parent.mkdir(parents=True,exist_ok=True)
  args.report.write_text(json.dumps(a,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
  print("ANB_PROVENANCE_SOURCE_PINS="+str(len(PINS)))
  print("ANB_CRANIOM_FIELD_COUNT="+str(len(a["typed_craniom_legacy_overrides"])))
  print("ANB_FACAD_PARITY_NOT_TESTED=true")

if __name__=="__main__":main()
