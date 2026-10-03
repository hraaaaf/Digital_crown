from backend.services import cephalo_pdf_projection as pdf

def test_pdf_projection_exposes_protocol_profiles(monkeypatch):
    monkeypatch.setattr(pdf,"build_r15_clinical_studio_snapshot",lambda **_: {"stages":[],"blocking_gates":[],"clinical_validation_available":False,"active_runtime_chain_verified":True,"evidence_graph_present":True})
    monkeypatch.setattr(pdf,"project_runtime_chain_read_path",lambda payload,patient_id:{"scientific_read_path":{"canonical_measurements":[],"blocked_method_ids":[],"unmapped_method_ids":[],"protocol_profiles":{"steiner":{"protocol_profile_id":"STEINER_STATIC_PROTOCOL_PROFILE_V1"}}}})
    class G: measurements={}
    monkeypatch.setattr(pdf,"deserialize_evidence_snapshot",lambda payload:object())
    monkeypatch.setattr(pdf,"validate_active_runtime_chain",lambda payload,graph:G())
    out=pdf.build_cephalo_pdf_projection(patient_id=1,analysis_id=2,angles_data={"_evidence_graph_v1":{"schema_version":"CEPHALO_EVIDENCE_V1"}})
    assert out["protocol_profiles"]["steiner"]["protocol_profile_id"]=="STEINER_STATIC_PROTOCOL_PROFILE_V1"
