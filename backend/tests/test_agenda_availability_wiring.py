import ast
from pathlib import Path


def test_appointment_mutations_use_authoritative_agenda_availability():
    source = Path('backend/routers/appointments.py').read_text()
    tree = ast.parse(source)
    agenda_imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == 'backend.services.agenda_availability'
    ]
    assert any(
        alias.name == 'validate_appointment_availability'
        for node in agenda_imports
        for alias in node.names
    )
    assert source.count('validate_appointment_availability(') >= 3
    assert 'any(key in update_data for key in ("datetime_start", "duration_minutes", "scheduling_type", "praticien_id"))' in source
    assert source.count('raise HTTPException(status_code=422, detail=availability_error)') >= 3

    # Bulk validation, including practitioner conflicts, must finish before inserts start.
    validation_loop = source.index('for index, item in enumerate(payload.appointments):')
    insert_loop = source.index('for prepared_item in prepared:')
    first_bulk_add = source.index('db.add(db_appt)', insert_loop)
    assert validation_loop < insert_loop < first_bulk_add
