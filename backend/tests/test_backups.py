import os
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend import models
from backend.services.backup_service import backup_service

# Configuration of test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    models.Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        models.Base.metadata.drop_all(bind=engine)

def test_key_derivation():
    # Verify that key derivation produces a valid base64 key
    key = backup_service._derive_fernet_key("3a5b6c7d8e9f0112131415161718192021222324252627282930313233343536")
    assert isinstance(key, bytes)
    assert len(key) == 44 # Standard Fernet key base64 length

def test_encryption_and_decryption_cycle(tmp_path):
    # 1. Create a dummy file with sensitive patient data
    sample_file = tmp_path / "sensitive_patient_data.db"
    sample_content = b"Patient zero: John Doe, implants: 2, ceb-angle: 25.6"
    sample_file.write_bytes(sample_content)

    encrypted_file = tmp_path / "encrypted_archive.enc"
    decrypted_file = tmp_path / "restored_patient_data.db"

    # 2. Encrypt sample file
    success_enc = backup_service.encrypt_file(str(sample_file), str(encrypted_file))
    assert success_enc is True
    assert encrypted_file.exists()
    assert encrypted_file.read_bytes() != sample_content # Assert it is encrypted

    # 3. Decrypt sample file
    success_dec = backup_service.decrypt_file(str(encrypted_file), str(decrypted_file))
    assert success_dec is True
    assert decrypted_file.exists()
    assert decrypted_file.read_bytes() == sample_content # Byte-by-byte parity check

def test_decryption_with_bad_key(tmp_path):
    # 1. Encrypt file with standard service key
    sample_file = tmp_path / "secret.txt"
    sample_file.write_bytes(b"Top secret data")
    encrypted_file = tmp_path / "secret.enc"
    backup_service.encrypt_file(str(sample_file), str(encrypted_file))

    # 2. Tamper with the encrypted file
    bad_encrypted_file = tmp_path / "bad_secret.enc"
    bad_encrypted_file.write_bytes(b"corrupted payload data")

    # 3. Attempt decryption should fail
    restored_file = tmp_path / "restored_secret.txt"
    success_dec = backup_service.decrypt_file(str(bad_encrypted_file), str(restored_file))
    assert success_dec is False

def test_run_automated_backup(db, tmp_path):
    # 1. Setup a fake database file
    db_file = tmp_path / "digital_crown_local.db"
    db_file.write_bytes(b"SQLite format 3\x00...")
    
    backups_dir = tmp_path / "backups"

    # 2. Run the automated backup service
    success = backup_service.run_automated_backup(db, str(db_file), str(backups_dir))
    assert success is True

    # 3. Check that local encrypted file exists
    local_backups = os.listdir(str(backups_dir))
    assert len(local_backups) == 1
    assert local_backups[0].endswith(".enc")

    # 4. Check AuditLog database registration
    logs = db.query(models.AuditLog).filter(models.AuditLog.action == "BACKUP_CLOUD").all()
    assert len(logs) == 1
    assert "Sauvegarde cloud" in logs[0].details
    assert local_backups[0] in logs[0].details
