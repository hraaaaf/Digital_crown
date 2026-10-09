"""Synthetic-only test of Facad vendor-storage topology fail-closed contract."""
import copy
import importlib.util
import unittest
from pathlib import Path

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("d3_vendor_gap", HERE/"facad_314_d3_storage_authority_gap_gate.py")
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

COLLECTOR=(HERE/"facad_314_d3_windows_snapshot.ps1").read_text(encoding="utf-8")
OBSERVER=(HERE/"facad_314_d3_process_io_observer.ps1").read_text(encoding="utf-8")
COMPARATOR=(HERE/"facad_314_d3_snapshot_diff_gate.py").read_text(encoding="utf-8")

class VendorTopologyFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.result=gate.inspect(COLLECTOR,OBSERVER,COMPARATOR)

    def test_existing_collector_not_confused_with_isolation(self):
        self.assertEqual(self.result["verdict"],"BLOCKED_INCOMPLETE_VENDOR_STORAGE_SCOPE")
        self.assertIs(self.result["d3_isolation_verified"],False)
        self.assertIs(self.result["clinical_edit_allowed"],False)

    def test_exact_required_categories_and_no_unexpected_green(self):
        self.assertEqual(self.result["required_category_count"],9)
        self.assertEqual(set(self.result["missing_category_ids"]),set(gate.REQUIRED_CATEGORIES))
        self.assertEqual(self.result["documented_coverage_category_count"],0)

    def test_vendor_roaming_ilexis_not_alias_roaming_facad(self):
        self.assertIn("facad_appdata_roaming=TreeScope (Join-Path $env:APPDATA 'Facad') $false",COLLECTOR)
        self.assertIn("FACAD_ROAMING_ILEXIS_SETTINGS",self.result["missing_category_ids"])

    def test_patient_data_root_and_node_not_equivalent_to_fcd_clone(self):
        self.assertTrue(self.result["patient_data_root_may_be_network_shared"])
        self.assertIn("FACAD_PATIENT_DATA_ROOT_CONFIGURED",self.result["missing_category_ids"])
        self.assertIn("FACAD_PATIENT_DATA_NODE_CONFIGURED",self.result["missing_category_ids"])

    def test_license_scope_must_not_involve_license_read(self):
        self.assertIn("FACAD_LICENSE_ROOT_PROTECTED",self.result["missing_category_ids"])
        self.assertTrue(self.result["no_patient_files_or_settings_read"])

    def test_process_counters_not_write_path_attribution(self):
        self.assertIn("path_attribution_available=$false",OBSERVER)
        self.assertIn("PROCESS_AND_CHILD_WRITE_PATH_ATTRIBUTION",self.result["missing_category_ids"])

    def test_registry_key_only_does_not_prove_value_change(self):
        self.assertIn("FACAD_REGISTRY_VALUES_CHANGE_DETECTED",self.result["missing_category_ids"])

    def test_added_root_without_comparator_scope_is_still_missing(self):
        altered=COLLECTOR+"\nfacad_patient_data_root=TreeScope $testRoot $false\n"
        self.assertIn("FACAD_PATIENT_DATA_ROOT_CONFIGURED",gate.inspect(altered,OBSERVER,COMPARATOR)["missing_category_ids"])

    def test_added_comparator_without_real_collector_is_still_missing(self):
        altered=COMPARATOR+"\n# 'facad_patient_data_node': 'filetree'\n"
        self.assertIn("FACAD_PATIENT_DATA_NODE_CONFIGURED",gate.inspect(COLLECTOR,OBSERVER,altered)["missing_category_ids"])

    def test_a_forged_all_green_metadata_never_certifies_machine(self):
        c=COLLECTOR+"\n"
        cmp=COMPARATOR+"\n"
        fields={
          "FACAD_PATIENT_DATA_ROOT_CONFIGURED":("facad_patient_data_root=TreeScope x","'facad_patient_data_root': 'filetree'"),
          "FACAD_PATIENT_DATA_NODE_CONFIGURED":("facad_patient_data_node=TreeScope x","'facad_patient_data_node': 'filetree'"),
          "FACAD_WORK_LIST_AND_IMPORT_TARGET":("facad_work_list=TreeScope x","'facad_work_list': 'filetree'"),
          "FACAD_ROAMING_ILEXIS_SETTINGS":("facad_appdata_roaming_ilexis=TreeScope (Join-Path $env:APPDATA 'Ilexis') $false","'facad_appdata_roaming_ilexis': 'filetree'"),
        }
        for col,com in fields.values():
            c+="\n"+col
            cmp+="\n"+com
        c+="\nFACAD_ADMIN_SETTINGS_METADATA_OBSERVED=true\nFacad.Administrator.settings"
        c+="\nFACAD_LICENSE_ROOT_PROTECTED_METADATA_ONLY=true\nLICENSE_CONTENT_READ=false"
        c+="\nFACAD_CONFIGURED_UNC_ROOTS_RESOLVED=true\nFACAD_REGISTRY_VALUES_CHANGE_DETECTED=true"
        o=OBSERVER+"\npath_attribution_available=$true\ncomplete_child_process_coverage=$true"
        result=gate.inspect(c,o,cmp)
        self.assertEqual(result["documented_coverage_category_count"],9)
        self.assertEqual(result["verdict"],"INCONCLUSIVE_STATIC_COVERAGE_NOT_RUNTIME_ISOLATION")
        self.assertIs(result["d3_isolation_verified"],False)
        self.assertIs(result["facad_numerical_parity_certified"],False)

    def test_source_output_has_no_machine_paths(self):
        self.assertTrue(self.result["source_release_notes"].startswith("https://www.facad.com/"))
        self.assertNotIn("C:\\Users\\",str(self.result))
        self.assertNotIn("license.fcl",str(self.result))

    def test_malformed_sources_rejected(self):
        for texts in (("",OBSERVER,COMPARATOR),(COLLECTOR,"",COMPARATOR),(COLLECTOR,OBSERVER,"")):
            with self.assertRaises(ValueError):
                gate.inspect(*texts)

if __name__=="__main__":
    unittest.main()
