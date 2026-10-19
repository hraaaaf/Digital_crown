"""LOT05.7-J10B: disposable native SQLCipher encrypted WAL/media/vault snapshot lab ONLY."""
import hashlib, json, os, re, shutil, stat, sys, tempfile, uuid
from pathlib import Path
from contextlib import closing
from sqlcipher3 import dbapi2 as cipher
FLAG="LOT05J10B_SQLCIPHER_FAKE_ONLY"
COMPONENTS=("snapshot.db","media-fake/scan.fake","media-fake/invoice.fake","license_fake.bin")
class Refused(PermissionError): pass
def check(root,key):
    if (os.getenv(FLAG)!="1" or not isinstance(root,Path) or not root.is_absolute()
        or root.is_symlink() or not root.is_dir() or not root.name.startswith("lot05j10b_fake_")
        or root.parent.resolve()!=Path(tempfile.gettempdir()).resolve()
        or type(key) is not str or re.fullmatch("[0-9a-f]{64}",key) is None):
        raise Refused("FAKE_TEMP_SQLCIPHER_ONLY")
    if (root/"inputs").is_symlink() or not (root/"inputs").is_dir(): raise Refused("INPUT_ROOT_DENIED")
def regular(p):
    if p.is_symlink() or not p.is_file() or p.stat().st_nlink!=1 or not stat.S_ISREG(p.stat().st_mode):
        raise Refused("UNTRUSTED_COMPONENT")
def digest(p):
    regular(p)
    if p.stat().st_size==0 or p.stat().st_size>128*1048576: raise Refused("INVALID_COMPONENT_SIZE")
    return {"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"size":p.stat().st_size}
def dbopen(p,key):
    c=cipher.connect(str(p))
    c.execute("PRAGMA key = '"+key+"'")
    if not c.execute("PRAGMA cipher_version").fetchone()[0]: raise Refused("REAL_SQLCIPHER_REQUIRED")
    return c
def verify(root,key):
    check(root,key)
    p=root/"CURRENT.json"; regular(p)
    try:
        d=json.loads(p.read_text("ascii"))
        if (type(d) is not dict or set(d)!={"generation","manifest","v"} or d["v"]!=1
            or re.fullmatch("g_[0-9a-f]{32}",d["generation"]) is None
            or type(d["manifest"]) is not dict or set(d["manifest"])!=set(COMPONENTS)):
            raise Refused("MANIFEST_INVALID")
    except (ValueError,TypeError,KeyError) as e: raise Refused("MANIFEST_INVALID") from e
    rootgen=root/"generations"; dest=rootgen/d["generation"]
    if rootgen.is_symlink() or dest.is_symlink() or not dest.is_dir(): raise Refused("GENERATION_REDIRECTED")
    if dest.resolve().parent!=rootgen.resolve(): raise Refused("GENERATION_REDIRECTED")
    seen=set()
    for q in dest.rglob("*"):
        if q.is_symlink(): raise Refused("LINKED_FILE")
        if q.is_file(): seen.add(q.relative_to(dest).as_posix())
    if seen!=set(COMPONENTS): raise Refused("INCOMPLETE_GENERATION")
    for name in COMPONENTS:
        if digest(dest/name)!=d["manifest"][name]: raise Refused("CHANGED_COMPONENT")
    try:
        with closing(dbopen(dest/"snapshot.db",key)) as c:
            if c.execute("PRAGMA integrity_check").fetchone()!=("ok",): raise Refused("CORRUPTED_CIPHER_DB")
    except cipher.DatabaseError as e: raise Refused("CORRUPTED_CIPHER_DB") from e
    return dest,d
def publish(root,key,fail_at=None):
    check(root,key)
    source=root/"inputs"/"clinical_fake.db"; regular(source)
    for name in COMPONENTS[1:]:
        p=root/"inputs"/name
        if p.parent.is_symlink(): raise Refused("SOURCE_PARENT_SYMLINK")
        regular(p)
    gens=root/"generations"
    if gens.is_symlink(): raise Refused("GENERATION_LINK")
    gens.mkdir(exist_ok=True)
    nonce=uuid.uuid4().hex; stage=gens/(".stage_"+nonce); final=gens/("g_"+nonce)
    stage.mkdir(mode=0o700); (stage/"media-fake").mkdir()
    try:
        with closing(dbopen(source,key)) as src:
            with closing(dbopen(stage/"snapshot.db",key)) as dst:
                src.backup(dst)
                if dst.execute("PRAGMA integrity_check").fetchone()!=("ok",): raise Refused("BAD_SQLCIPHER_BACKUP")
                mode=dst.execute("PRAGMA journal_mode=DELETE").fetchone()
                if not mode or mode[0].lower()!="delete": raise Refused("UNSETTLED_WAL")
        if any(Path(str(stage/"snapshot.db")+s).exists() for s in ("-wal","-shm")): raise Refused("UNSETTLED_WAL")
        with (stage/"snapshot.db").open("r+b") as f: os.fsync(f.fileno())
        if fail_at=="after_db": raise Refused("FAULT_AFTER_DB")
        for name in COMPONENTS[1:]:
            a=root/"inputs"/name; old=digest(a); b=stage/name
            shutil.copyfile(a,b)
            if digest(a)!=old or digest(b)!=old: raise Refused("SOURCE_CHANGED")
            with b.open("r+b") as f: os.fsync(f.fileno())
        if fail_at=="after_media": raise Refused("FAULT_AFTER_MEDIA")
        if fail_at=="hard_exit": os._exit(73)
        record={"v":1,"generation":final.name,"manifest":{name:digest(stage/name) for name in COMPONENTS}}
        os.rename(stage,final)
        if fail_at=="after_generation": raise Refused("FAULT_AFTER_GENERATION")
        if (root/"CURRENT.json").exists(): verify(root,key)
        tmp=root/(".current_"+nonce+".tmp")
        try:
            with tmp.open("xb") as f:
                f.write(json.dumps(record,sort_keys=True).encode("ascii")); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,root/"CURRENT.json")
        finally: tmp.unlink(missing_ok=True)
        return record
    finally:
        if stage.exists(): shutil.rmtree(stage)
if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit(2)
    publish(Path(sys.argv[1]),sys.argv[2],"hard_exit")
