import base64
import os
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def get_master_key_bytes() -> bytes:
    master_key_hex = os.getenv("CABINET_MASTER_KEY_HEX")
    if not master_key_hex:
        raise ValueError("CABINET_MASTER_KEY_HEX non défini dans .env")
    return bytes.fromhex(master_key_hex)

def encrypt_payload(data: dict) -> dict:
    """
    Chiffre un payload JSON avec AES-256-GCM et la clé maître.
    Retourne { "payload": "base64(iv + ciphertext + tag)" }
    """
    key = get_master_key_bytes()
    iv = os.urandom(12)
    
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()
    
    plaintext = json.dumps(data).encode("utf-8")
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    
    # Structure compatible Web Crypto API: IV (12) + Ciphertext + Tag (16)
    combined = iv + ciphertext + encryptor.tag
    b64 = base64.b64encode(combined).decode("utf-8")
    
    return {"payload": b64}

def decrypt_payload(b64_payload: str) -> dict:
    """
    Déchiffre un payload JSON provenant du mobile avec AES-256-GCM.
    b64_payload = base64(iv + ciphertext + tag)
    """
    key = get_master_key_bytes()
    combined = base64.b64decode(b64_payload)
    
    iv = combined[:12]
    tag = combined[-16:]
    ciphertext = combined[12:-16]
    
    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        backend=default_backend()
    ).decryptor()
    
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return json.loads(plaintext.decode("utf-8"))
