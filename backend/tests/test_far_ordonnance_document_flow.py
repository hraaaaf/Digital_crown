import inspect

from backend.routers import documents


def test_far_derivation_runs_only_after_source_archive_contract():
    source = inspect.getsource(documents.generate_document)
    source_archive = source.index("archive_service.archive_document(")
    far_call = source.index("archive_far_ordonnance_from_source(")
    assert source_archive < far_call
    assert 'if req.type == "ordonnance" and far_required:' in source
    assert 'far_source_ordonnance_document_id = int(doc.id)' in source
    assert 'ordonnance=schemas.OrdonnanceData(**req.data)' in source


def test_far_preview_does_not_claim_generated_output():
    source = inspect.getsource(documents.generate_document)
    assert 'far_status = "pending_archive" if far_required else "not_required"' in source
    assert "if should_archive:" in source
    assert source.index("if should_archive:") < source.index("archive_far_ordonnance_from_source(")


def test_far_admin_failure_is_explicit_without_reclassifying_clinical_source():
    source = inspect.getsource(documents.generate_document)
    assert 'far_status = "blocked"' in source
    assert 'warnings.append(f"FAR: {far_error}")' in source
    assert '"far_required": far_required' in source
    assert '"far_status": far_status' in source
    assert '"far_source_ordonnance_document_id": far_source_ordonnance_document_id' in source
