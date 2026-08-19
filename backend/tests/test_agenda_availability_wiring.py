from pathlib import Path


def test_appointment_mutations_use_authoritative_agenda_availability():
    source = Path('backend/routers/appointments.py').read_text()
    assert 'from backend.services.agenda_availability import validate_appointment_availability' in source
    assert source.count('validate_appointment_availability(') >= 3
    assert "any(key in update_data for key in ('datetime_start', 'duration_minutes', 'scheduling_type'))" in source
    assert source.count('raise HTTPException(status_code=422, detail=availability_error)') >= 3
    assert '# Validate the complete batch before any insert' in source
