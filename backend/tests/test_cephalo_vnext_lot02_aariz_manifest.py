from pathlib import Path
import importlib.util, json

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"scripts"/"build_cephalo_vnext_lot02_aariz_manifest.py"
spec=importlib.util.spec_from_file_location("lot02_aariz",SCRIPT)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def test_source_identity_is_frozen():
    src=json.loads((ROOT/"docs/audits/schemas/cephalo_vnext_lot02_aariz_source.json").read_text())
    assert src["source"]["doi"]=="10.6084/m9.figshare.27986417.v1"
    assert src["source"]["figshare_file_id"]==51041642
    assert src["source"]["archive_size_bytes"]==2098209792
    assert src["source"]["archive_md5"]=="e0bd645bca6759abdae4f199d841bda6"
    assert src["source"]["license"]=="CC BY 4.0"
    assert src["expected"]["cases"]==1000
    assert src["expected"]["landmarks_per_annotation"]==29
    assert src["policy"]["junior_senior_kept_separate"] is True

def test_mapping_is_conservative_and_closed():
    assert len(m.AARIZ_TO_DC)==24
    assert m.AARIZ_TO_DC["Pn"]=="Prn"
    assert m.HOLD=={"UMT":"U6","LMT":"L6"}
    assert "UMT" not in m.AARIZ_TO_DC and "LMT" not in m.AARIZ_TO_DC
    assert set(m.AARIZ_TO_DC).isdisjoint(m.HOLD)
    assert len(m.EXPECTED_SYMBOLS)==29

def test_srpose_only_points_are_not_invented():
    forbidden={"D_point","Cm","Ptm","Ba","PT_point","Bo","Ls2","Li2","Gn_soft","Me_soft","G_soft","C_point"}
    assert forbidden.isdisjoint(set(m.AARIZ_TO_DC.values()))
