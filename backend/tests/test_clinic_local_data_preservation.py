from datetime import datetime
from hashlib import sha256

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from backend import models
from backend.core.media_paths import get_media_root
from backend.core.paths import AppPaths
from backend.models_clinic_p2 import PatientPractitionerAssignment


def test_canonical_local_paths_stay_under_same_user_data_root(tmp_path, monkeypatch):
    user_data = tmp_path / "DigitalCrown-realistic"
    monkeypatch.setenv("DIGITALCROWN_USER_DATA_DIR", str(user_data))
    monkeypatch.delenv("MEDIA_ROOT", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "cabinet")

    assert AppPaths.get_db_url() == f"sqlite:///{user_data / 'clinical_vault.db'}"
    assert get_media_root() == user_data / "media"


def test_p2_additive_startup_preserves_existing_patient_archive_and_file(tmp_path):
    """Rehearse a P2-style upgrade over an already-populated local vault.

    The pre-upgrade state is represented by the full current schema minus the
    additive P2 assignment table. Existing Patient and DocumentArchive rows plus
    the real archived file are created first. Running SQLAlchemy create_all(), as
    cabinet startup does, must only recreate the missing additive table and must
    leave the pre-existing clinical data byte-for-byte intact.
    """
    db_path = tmp_path / "clinical_vault.db"
    media_dir = tmp_path / "media" / "documents"
    media_dir.mkdir(parents=True)
    historic_file = media_dir / "historic-certificat.pdf"
    historic_bytes = b"%PDF-1.4\nDIGITAL-CROWN-HISTORIC-DOCUMENT\n%%EOF\n"
    historic_file.write_bytes(historic_bytes)
    historic_digest = sha256(historic_bytes).hexdigest()

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    models.Base.metadata.create_all(bind=engine)

    # Simulate the immediately pre-P2 schema: everything already exists except
    # the new additive patient_practitioner_assignments table.
    PatientPractitionerAssignment.__table__.drop(bind=engine, checkfirst=True)
    assert "patient_practitioner_assignments" not in inspect(engine).get_table_names()

    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    with Session() as db:
        owner = models.User(
            email="historic-owner@cabinet.local",
            hashed_password="historic-hash",
            role=models.UserRole.DENTISTE,
            nom_complet="Dr Historique",
            is_active=True,
            is_licensed=True,
        )
        db.add(owner)
        db.flush()

        patient = models.Patient(
            numero_dossier="HIST-001",
            nom="BENSAID",
            prenom="Nadia",
            date_naissance=datetime(1986, 4, 12),
            sexe="F",
            employer_id=owner.id,
            telephone="0600000000",
            assurance="AUCUNE",
        )
        db.add(patient)
        db.flush()

        archive = models.DocumentArchive(
            patient_id=patient.id,
            document_type=models.DocumentType.CERTIFICAT,
            filename=historic_file.name,
            original_filename="certificat-historique.pdf",
            document_group_id="historic-group-001",
            version_number=1,
            is_latest_version=True,
            file_hash=historic_digest,
            file_size=len(historic_bytes),
            file_path=str(historic_file),
            title="Certificat historique",
            status=models.DocumentStatus.ACTIF,
        )
        db.add(archive)
        db.commit()

        patient_id = patient.id
        archive_id = archive.id

    before_db_digest = sha256(db_path.read_bytes()).hexdigest()
    before_file_digest = sha256(historic_file.read_bytes()).hexdigest()

    # Equivalent of the additive metadata portion of cabinet startup after update.
    models.Base.metadata.create_all(bind=engine)

    assert "patient_practitioner_assignments" in inspect(engine).get_table_names()

    with Session() as db:
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).one()
        archive = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == archive_id).one()

        assert db.query(models.Patient).count() == 1
        assert db.query(models.DocumentArchive).count() == 1
        assert patient.numero_dossier == "HIST-001"
        assert patient.nom == "BENSAID"
        assert patient.prenom == "Nadia"
        assert archive.patient_id == patient.id
        assert archive.file_path == str(historic_file)
        assert archive.file_hash == historic_digest
        assert archive.status == models.DocumentStatus.ACTIF

    assert historic_file.exists()
    assert sha256(historic_file.read_bytes()).hexdigest() == before_file_digest == historic_digest

    # The DB file is expected to change because the new table is created. The
    # preserved row/file assertions above are the safety contract; an unchanged DB
    # byte hash would be the wrong expectation for an additive schema upgrade.
    assert sha256(db_path.read_bytes()).hexdigest() != before_db_digest
