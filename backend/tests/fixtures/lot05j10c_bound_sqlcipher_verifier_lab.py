"""J10C offline verification of RSA order bound to fake SQLCipher generation."""
import base64, binascii, hashlib, json, os, re, shutil, time
from cryptography.exceptions import UnsupportedAlgorithm
from pathlib import Path
from contextlib import closing
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from backend.tests.fixtures import lot05j10b_sqlcipher_multicomponent_lab as cipher_lab

class Denied(PermissionError): pass
def digest_pointer(record):
    return hashlib.sha256(json.dumps(record,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")).hexdigest()
def verify_ticket(ticket,pin,*,owner,job,generation,manifest):
    if (type(ticket) is not dict or set(ticket)!={"body","signature","signer_pid"} or
        type(owner) is not int or owner<=0 or type(job) is not str or
        re.fullmatch("[0-9a-f]{32}",job) is None or
        re.fullmatch("g_[0-9a-f]{32}",generation) is None or
        re.fullmatch("[0-9a-f]{64}",manifest) is None):
        raise Denied("J10C_SIGNED_SCOPE_INVALID")
    body=ticket["body"]
    signature=ticket["signature"]
    if type(body) is not str or len(body)>512 or type(signature) is not str or len(signature)>400:
        raise Denied("J10C_TICKET_FORMAT_INVALID")
    fields=body.split("|")
    wanted=["owner="+str(owner),"audience=LOT05J10C_SQLCIPHER_FAKE","job="+job,
            "generation="+generation,"manifest="+manifest]
    if len(fields)!=7 or fields[:5]!=wanted or not fields[5].startswith("nonce=") or not fields[6].startswith("expires="):
        raise Denied("J10C_TICKET_MISMATCH")
    nonce=fields[5][6:]
    if re.fullmatch("[0-9a-f]{32}",nonce) is None: raise Denied("J10C_NONCE_INVALID")
    try:
        exp=int(fields[6][8:])
        if str(exp)!=fields[6][8:] or exp<=int(time.time()) or exp>int(time.time())+120:
            raise Denied("J10C_EXPIRED")
        public_lines=pin.splitlines()
        if len(public_lines)!=3 or public_lines[2]!=str(owner):
            raise Denied("J10C_PIN_OWNER_MISMATCH")
        mod=base64.b64decode(public_lines[0],validate=True)
        exponent=base64.b64decode(public_lines[1],validate=True)
        if len(mod)!=256 or not (1<=len(exponent)<=8): raise Denied("J10C_BAD_PIN")
        key=rsa.RSAPublicNumbers(int.from_bytes(exponent,"big"),int.from_bytes(mod,"big")).public_key()
        raw=base64.b64decode(signature,validate=True)
        key.verify(raw,body.encode("ascii"),padding.PKCS1v15(),hashes.SHA256())
    except (ValueError,TypeError,binascii.Error,InvalidSignature,UnsupportedAlgorithm) as exc:
        raise Denied("J10C_RSA_DENY") from exc
    return nonce
def authorized_fake_copy(root,*,ticket,pin,owner,job,key,generation,manifest):
    directory,record=cipher_lab.verify(root,key)
    actual=digest_pointer(record)
    if record["generation"]!=generation or actual!=manifest: raise Denied("J10C_SQLCIPHER_MANIFEST_MISMATCH")
    nonce=verify_ticket(ticket,pin,owner=owner,job=job,generation=generation,manifest=manifest)
    output=root/"isolated-recovery"
    if output.exists() or output.is_symlink(): raise Denied("J10C_OUTPUT_EXISTS")
    ledger=root/"j10c-used"
    if ledger.is_symlink(): raise Denied("J10C_LEDGER_LINK")
    ledger.mkdir(mode=0o700,exist_ok=True)
    if ledger.is_symlink() or not ledger.is_dir(): raise Denied("J10C_LEDGER_DENY")
    # Catch a CURRENT pointer change before nonce consumption. Still not
    # handle-anchored against privileged TOCTOU, so NOT a product guarantee.
    latest_dir,latest_record=cipher_lab.verify(root,key)
    if latest_record!=record or latest_dir!=directory:
        raise Denied("J10C_CURRENT_CHANGED_BEFORE_CONSUMPTION")
    try:
        fd=os.open(str(ledger/(nonce+".nonce")),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError as exc: raise Denied("J10C_REPLAY_DENIED") from exc
    with os.fdopen(fd,"wb") as f:
        f.write(hashlib.sha256(ticket["body"].encode("ascii")).hexdigest().encode("ascii"))
        f.flush(); os.fsync(f.fileno())
    try:
        shutil.copytree(directory,output)
        for name in cipher_lab.COMPONENTS:
            if cipher_lab.digest(output/name)!=record["manifest"][name]:
                raise Denied("J10C_COPY_TAMPERED")
        with closing(cipher_lab.dbopen(output/"snapshot.db",key)) as db:
            if db.execute("PRAGMA integrity_check").fetchone()!=("ok",):
                raise Denied("J10C_COPY_CORRUPTED")
    except Exception:
        if output.exists(): shutil.rmtree(output)
        raise
    return {"owner":owner,"job":job,"generation":generation,"manifest":manifest,
            "clinical_restore_permitted":False}
