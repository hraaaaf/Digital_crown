"""Real disk SQLCipher and fresh-process regression; all data are fictitious."""
import os
from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]

def run(script, env):
    result = subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT, env=env,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-2000:]

def environment(tmp_path, *, legacy=False):
    env = os.environ.copy()
    for name in list(env):
        if name.startswith("DIGITALCROWN_") or name in ("DATABASE_URL", "ENVIRONMENT",
                "CABINET_MASTER_KEY_HEX", "SQLCIPHER_KEY_HEX", "MOBILE_PAIRING_KEY_HEX", "SECRET_KEY", "MEDIA_ROOT"):
            env.pop(name, None)
    env.update(ENVIRONMENT="cabinet", SECRET_KEY="a"*64, CABINET_MASTER_KEY_HEX="b"*64,
               DATABASE_URL="sqlite:///"+str(tmp_path/"clinical_vault.db").replace("\\","/"),
               DIGITALCROWN_ENV_FILE=str(tmp_path/".env"),
               DIGITALCROWN_USER_DATA_DIR=str(tmp_path/"data"),
               DIGITALCROWN_CONFIG_DIR=str(tmp_path/"config"),
               DIGITALCROWN_RUNTIME_DIR=str(tmp_path/"runtime"),
               DIGITALCROWN_LOG_DIR=str(tmp_path/"logs"), MEDIA_ROOT=str(tmp_path/"media"))
    if not legacy:
        env.update(SQLCIPHER_KEY_HEX="c"*64, MOBILE_PAIRING_KEY_HEX="d"*64)
    Path(env["DIGITALCROWN_ENV_FILE"]).write_text("ENVIRONMENT=cabinet\n",encoding="utf-8")
    return env

@pytest.mark.parametrize('legacy', [False, True])
def test_persistent_patient_survives_successive_revocations_and_fresh_process(tmp_path, legacy):
    env = environment(tmp_path, legacy=legacy)
    before = Path(env["DIGITALCROWN_ENV_FILE"]).read_bytes()
    run("""
from alembic import command
from alembic.config import Config
config=Config('alembic.ini')
command.upgrade(config,'head')
from backend import database,models
from backend.security import token_blacklist
from datetime import date,datetime
with database.SessionLocal() as db:
 owner=models.User(email='fictitious-owner@cabinet.ma',hashed_password='fixture',role=models.UserRole.DENTISTE,is_active=True)
 db.add(owner);db.flush()
 db.add(models.Patient(nom='FICTITIOUS',prenom='PERSISTENCE',date_naissance=date(1990,1,1),sexe='M',employer_id=owner.id))
 db.commit()
 for n in range(2):
  db.add(models.MobilePairedDevice(device_id='fiction-'+str(n),user_id=owner.id,employer_id=owner.id,client_public_key_hex='fiction',refresh_jti='fiction-'+str(n)))
  db.commit()
  token_blacklist.revoke_mobile_access(owner.id,db)
  assert db.query(models.MobilePairedDevice).filter(models.MobilePairedDevice.revoked_at.is_(None)).count()==0
 assert db.query(models.Patient).count()==1
database.engine.dispose()
""", env)
    assert Path(env["DIGITALCROWN_ENV_FILE"]).read_bytes()==before
    assert not (tmp_path/"clinical_vault.db").read_bytes().startswith(b"SQLite format 3")
    run("""
from backend import database,models
from backend.security import TokenBlacklist
from backend.services.backup_service import BackupService
from pathlib import Path
with database.SessionLocal() as db:
 assert db.query(models.Patient).filter_by(nom='FICTITIOUS').count()==1
 assert db.query(models.MobilePairedDevice).filter(models.MobilePairedDevice.revoked_at.is_(None)).count()==0
 assert TokenBlacklist()._mobile_cutoff(1,db) is not None
passphrase=BackupService._sqlcipher_passphrase(database.engine)
snapshot=Path(database.engine.url.database).parent/'snapshot.db'
BackupService._export_sqlcipher_snapshot(Path(database.engine.url.database),snapshot,passphrase)
BackupService._verify_sqlcipher_file(snapshot,passphrase)
status=BackupService.backup_active_database()
assert status['status']=='SUCCESS', status['error_code']
from backend.core.paths import AppPaths
encrypted=AppPaths.get_user_data_dir()/'backups'/status['backup_filename']
clone=snapshot.parent/'restored-clone.db'
BackupService.restore_backup(encrypted,clone,verify_sqlcipher=True,passphrase=passphrase)
from sqlcipher3 import dbapi2
conn=dbapi2.connect(str(clone))
conn.execute("PRAGMA key = '"+passphrase+"'")
assert conn.execute("SELECT count(*) FROM patients WHERE nom='FICTITIOUS'").fetchone()[0]==1
assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
conn.close()
wrong=dbapi2.connect(str(clone))
wrong.execute("PRAGMA key = 'wrong-fictitious-key'")
try: wrong.execute('SELECT count(*) FROM patients').fetchone()
except dbapi2.DatabaseError: pass
else: raise AssertionError('database accepted wrong key')
finally: wrong.close()
database.engine.dispose()
""", env)

def test_legacy_passphrase_stable_and_mobile_domain_separated(tmp_path):
    env=environment(tmp_path,legacy=True)
    run("""
from backend.core.key_material import sqlcipher_passphrase,mobile_pairing_key_hex
from backend.services.zka_crypto import encrypt_payload,decrypt_payload
from backend.services.zka_service import ZKAService
import os
assert sqlcipher_passphrase()==os.environ['CABINET_MASTER_KEY_HEX']
assert mobile_pairing_key_hex()!=sqlcipher_passphrase()
assert decrypt_payload(encrypt_payload({'fictitious':True})['payload'])=={'fictitious':True}
try: ZKAService().rotate_master_key(os.environ['DIGITALCROWN_ENV_FILE'])
except RuntimeError: pass
else: raise AssertionError('implicit rotation accepted')
assert sqlcipher_passphrase()==os.environ['CABINET_MASTER_KEY_HEX']
""",env)

def test_explicit_mobile_key_cannot_equal_database_key(tmp_path):
    env=environment(tmp_path)
    env['MOBILE_PAIRING_KEY_HEX']=env['SQLCIPHER_KEY_HEX']
    run("""
from backend.core.key_material import mobile_pairing_key_hex
try: mobile_pairing_key_hex()
except ValueError: pass
else: raise AssertionError('shared database/mobile key accepted')
""",env)


def test_revocation_commit_failure_rolls_back_without_changing_keys(tmp_path):
    env=environment(tmp_path)
    run("""
from alembic import command
from alembic.config import Config
command.upgrade(Config('alembic.ini'),'head')
from backend import database,models
from backend.security import TokenBlacklist
from backend.core.key_material import sqlcipher_passphrase,mobile_pairing_key_hex
before=(sqlcipher_passphrase(),mobile_pairing_key_hex())
with database.SessionLocal() as db:
 owner=models.User(email='fictitious-failure@cabinet.ma',hashed_password='fixture',role=models.UserRole.DENTISTE,is_active=True)
 db.add(owner);db.flush()
 owner_id=owner.id
 db.add(models.MobilePairedDevice(device_id='failure-fiction',user_id=owner.id,employer_id=owner.id,client_public_key_hex='fiction',refresh_jti='failure-fiction'))
 db.commit()
 original_commit=db.commit
 def fail_commit(): raise RuntimeError('injected test commit failure')
 db.commit=fail_commit
 blacklist=TokenBlacklist()
 try: blacklist.revoke_mobile_access(owner_id,db)
 except RuntimeError: pass
 else: raise AssertionError('failure concealed')
 db.commit=original_commit
 assert db.query(models.MobilePairedDevice).filter(models.MobilePairedDevice.revoked_at.is_(None)).count()==1
 assert blacklist._mobile_cutoff(owner_id,db) is None
 blacklist.revoke_mobile_access(owner_id,db)
 assert db.query(models.MobilePairedDevice).filter(models.MobilePairedDevice.revoked_at.is_(None)).count()==0
assert (sqlcipher_passphrase(),mobile_pairing_key_hex())==before
database.engine.dispose()
""",env)

def test_explicit_new_cabinet_owner_schema_and_patient_persist(tmp_path):
    env=environment(tmp_path)
    env["DIGITALCROWN_INSTANCE_ID"]="fictitious-fue-g04-instance"
    env["DATABASE_URL"]="sqlite:///"+str(tmp_path/"data"/"clinical_vault.db").replace("\\","/")
    run("""
from backend.core.new_cabinet_setup import provision_new_cabinet
provision_new_cabinet('fictitious-setup@cabinet.ma','Fictitious-test-passphrase-04')
from backend import database,models
from backend.security import verify_password
from datetime import date
with database.SessionLocal() as db:
 owner=db.query(models.User).one()
 assert owner.is_active and not owner.is_licensed
 assert verify_password('Fictitious-test-passphrase-04',owner.hashed_password)
 assert db.query(models.CabinetConfig).one().owner_id==owner.id
 db.add(models.Patient(nom='FICTITIOUS',prenom='FIRSTBOOT',date_naissance=date(1990,1,1),sexe='M',employer_id=owner.id))
 db.commit()
database.engine.dispose()
try: provision_new_cabinet('other-fiction@cabinet.ma','Fictitious-test-passphrase-04')
except RuntimeError: pass
else: raise AssertionError('existing cabinet setup accepted')
""",env)
    run("""
from backend import database,models
with database.SessionLocal() as db:
 assert db.query(models.User).count()==1
 assert db.query(models.Patient).filter_by(prenom='FIRSTBOOT').count()==1
database.engine.dispose()
""",env)
