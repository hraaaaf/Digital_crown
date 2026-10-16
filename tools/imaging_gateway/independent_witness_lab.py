"""LOT06-N: synthetic loopback witness, separate process, no physical trust domain.

This is a TEST-ONLY transport around LOT06-M disposable SQLite CAS. It never
binds a LAN interface, exposes a clinical API, or provisions real keys.
Test bootstrap owns witness key: NOT independent custody/anti-rollback proof.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import tempfile
import time
import re
import socket
import socketserver
import sys
import threading
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from tools.imaging_gateway.durable_cas_lab import (
    AUTHORITY, EPOCH, CasRefusal, apply, audit, canonical, event_bytes, lookup,
    signer_pub, verify_receipt, _require_lab_path,
)

REQ_DOMAIN = b"DC06N|client|synthetic-v1\0"
RESP_DOMAIN = b"DC06N|witness|synthetic-v1\0"
CHALLENGE = re.compile(r"[0-9a-f]{32}\Z")
MAX_WIRE = 8192
METHODS = {"APPLY", "DROP_AFTER_COMMIT", "LOOKUP", "HEAD"}


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def unb64(value: str, length: int | None = None) -> bytes:
    if type(value) is not str or len(value) > MAX_WIRE:
        raise CasRefusal("WIRE_BASE64_REFUSE")
    try:
        data = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise CasRefusal("WIRE_BASE64_REFUSE") from exc
    if length is not None and len(data) != length:
        raise CasRefusal("WIRE_BYTES_REFUSE")
    return data


def request_shape(req: dict) -> None:
    if type(req) is not dict or set(req) != {"protocol", "method", "scope", "challenge", "op_id", "event"}:
        raise CasRefusal("CLIENT_REQUEST_SHAPE_REFUSE")
    if (req["protocol"] != "DC06N_SYNTHETIC_V1" or req["method"] not in METHODS
            or type(req["scope"]) is not str or not CHALLENGE.fullmatch(req["scope"])
            or type(req["challenge"]) is not str or not CHALLENGE.fullmatch(req["challenge"])
            or type(req["op_id"]) is not str or not CHALLENGE.fullmatch(req["op_id"])):
        raise CasRefusal("CLIENT_REQUEST_REFUSE")
    if req["method"] in ("APPLY", "DROP_AFTER_COMMIT"):
        raw = event_bytes(req["event"])
        if req["event"]["scope"] != req["scope"] or req["event"]["op_id"] != req["op_id"] or len(raw) > 2048:
            raise CasRefusal("CLIENT_BINDING_REFUSE")
    elif req["event"] is not None:
        raise CasRefusal("NO_EVENT_FOR_READ_REFUSE")


def auth_request(req: dict, signer: Ed25519PrivateKey) -> dict:
    request_shape(req)
    return {"request": req, "signature_b64": b64(signer.sign(REQ_DOMAIN + canonical(req)))}


def verify_request(packet: dict, enrolled_pub: bytes) -> dict:
    if type(packet) is not dict or set(packet) != {"request", "signature_b64"}:
        raise CasRefusal("SIGNED_REQUEST_REFUSE")
    req = packet["request"]
    request_shape(req)
    try:
        Ed25519PublicKey.from_public_bytes(enrolled_pub).verify(
            unb64(packet["signature_b64"], 64), REQ_DOMAIN + canonical(req))
    except (InvalidSignature, ValueError) as exc:
        raise CasRefusal("CLIENT_IDENTITY_REFUSE") from exc
    return req


def proof_bytes(proof: dict) -> bytes:
    if (type(proof) is not dict
            or set(proof) != {"protocol", "authority_id", "epoch", "scope",
                             "challenge", "method", "op_id", "seq", "mac",
                             "status", "receipt_b64"}):
        raise CasRefusal("PROOF_SHAPE_REFUSE")
    return RESP_DOMAIN + canonical(proof)


def verify_response(packet: dict, pinned_pub: bytes, req: dict) -> dict:
    """Validate signer and *this* challenge; cannot detect rolled-back witness itself."""
    request_shape(req)
    if type(packet) is not dict or set(packet) != {"proof", "signature_b64"}:
        raise CasRefusal("RESPONSE_SHAPE_REFUSE")
    proof = packet["proof"]
    try:
        msg = proof_bytes(proof)
        Ed25519PublicKey.from_public_bytes(pinned_pub).verify(
            unb64(packet["signature_b64"], 64), msg)
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise CasRefusal("RESPONSE_SIGNATURE_REFUSE") from exc
    if (proof["protocol"] != "DC06N_SYNTHETIC_V1" or proof["authority_id"] != AUTHORITY
            or proof["epoch"] != EPOCH or proof["scope"] != req["scope"]
            or proof["challenge"] != req["challenge"]
            or proof["method"] != req["method"] or proof["op_id"] != req["op_id"]
            or type(proof["seq"]) is not int or not 0 <= proof["seq"] <= 256
            or type(proof["mac"]) is not str or not re.fullmatch("[0-9a-f]{64}", proof["mac"])
            or proof["status"] not in ("DECIDED_LAB_ONLY", "HISTORICAL_ONLY", "HEAD_ONLY", "UNKNOWN_OP")):
        raise CasRefusal("RESPONSE_BINDING_REFUSE")
    if proof["status"] in ("DECIDED_LAB_ONLY", "HISTORICAL_ONLY"):
        receipt = unb64(proof["receipt_b64"])
        body = verify_receipt(receipt, pinned_pub)
        if (body["scope"] != req["scope"] or body["op_id"] != req["op_id"]
                or (req["event"] is not None and
                    body["request_sha256"] != hashlib.sha256(event_bytes(req["event"])).hexdigest())):
            raise CasRefusal("RESPONSE_RECEIPT_BINDING_REFUSE")
        if proof["status"] == "DECIDED_LAB_ONLY" and (
                body["after_seq"] != proof["seq"] or body["after_mac"] != proof["mac"]):
            raise CasRefusal("RESPONSE_FRESH_HEAD_REFUSE")
        if proof["status"] == "HISTORICAL_ONLY" and body["after_seq"] >= proof["seq"]:
            raise CasRefusal("RESPONSE_HISTORICAL_REFUSE")
    elif proof["receipt_b64"] != "":
        raise CasRefusal("RESPONSE_UNEXPECTED_RECEIPT")
    return proof


def send_request(port: int, req: dict, client_signer: Ed25519PrivateKey,
                 pinned_witness_pub: bytes, timeout: float = 3.0) -> dict:
    """Any network uncertainty is UNKNOWN, never an accepted decision."""
    try:
        packet = auth_request(req, client_signer)
        wire = canonical(packet) + b"\n"
        if len(wire) > MAX_WIRE:
            raise CasRefusal("WIRE_TOO_LARGE")
        with socket.create_connection(("127.0.0.1", port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(wire)
            buf = bytearray()
            while b"\n" not in buf and len(buf) <= MAX_WIRE:
                chunk = sock.recv(2048)
                if not chunk:
                    break
                buf.extend(chunk)
        if not buf or b"\n" not in buf or len(buf) > MAX_WIRE:
            raise CasRefusal("MISSING_OR_TRUNCATED_ACK")
        response = json.loads(bytes(buf).split(b"\n", 1)[0])
        return verify_response(response, pinned_witness_pub, req)
    except (OSError, TimeoutError, ValueError, UnicodeError, json.JSONDecodeError, CasRefusal) as exc:
        return {"status": "UNKNOWN_NO_AUTHORITY", "reason": type(exc).__name__}


class LoopbackWitness(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = False
    daemon_threads = True

    def __init__(self, db: Path, witness_signer: Ed25519PrivateKey, enrolled_pub: bytes):
        _require_lab_path(db)
        self.db, self.signer, self.enrolled_pub = db, witness_signer, enrolled_pub
        super().__init__(("127.0.0.1", 0), Handler)


class Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        try:
            self.request.settimeout(3.0)
            buf = bytearray()
            while b"\n" not in buf and len(buf) <= MAX_WIRE:
                chunk = self.request.recv(2048)
                if not chunk:
                    return
                buf.extend(chunk)
            if len(buf) > MAX_WIRE or b"\n" not in buf:
                return
            req = verify_request(json.loads(bytes(buf).split(b"\n", 1)[0]),
                                 self.server.enrolled_pub)
            if req["method"] in ("APPLY", "DROP_AFTER_COMMIT"):
                receipt = apply(self.server.db, req["event"], self.server.signer)
                if req["method"] == "DROP_AFTER_COMMIT":
                    return  # durable decision but no ACK; caller must rejoin by same op_id
            elif req["method"] == "LOOKUP":
                receipt = lookup(self.server.db, req["scope"], req["op_id"],
                                 signer_pub(self.server.signer))
            else:
                receipt = None
            seq, mac, _ = audit(self.server.db, req["scope"],
                                signer_pub(self.server.signer))
            if receipt:
                body = verify_receipt(receipt, signer_pub(self.server.signer))
                status = "DECIDED_LAB_ONLY" if body["after_seq"] == seq else "HISTORICAL_ONLY"
            else:
                status = "HEAD_ONLY" if req["method"] == "HEAD" else "UNKNOWN_OP"
            proof = {"protocol": "DC06N_SYNTHETIC_V1", "authority_id": AUTHORITY,
                     "epoch": EPOCH, "scope": req["scope"], "challenge": req["challenge"],
                     "method": req["method"], "op_id": req["op_id"], "seq": seq, "mac": mac,
                     "status": status, "receipt_b64": b64(receipt) if receipt else ""}
            payload = proof_bytes(proof)
            packet = {"proof": proof, "signature_b64": b64(self.server.signer.sign(payload))}
            self.request.sendall(canonical(packet) + b"\n")
        except (CasRefusal, OSError, ValueError, TypeError, KeyError, UnicodeError):
            # No success reply on invalid caller, failed transaction or corrupt ledger.
            return


def cli() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lab-server", action="store_true")
    group.add_argument("--lab-client", action="store_true")
    parser.add_argument("--db", type=Path)
    parser.add_argument("--port", type=int)
    parser.add_argument("--gate", type=Path)
    args = parser.parse_args()
    bootstrap = json.load(sys.stdin)  # synthetic secrets via pipe, not environment/log/file
    if args.lab_server:
        if args.db is None:
            raise SystemExit(2)
        signer = Ed25519PrivateKey.from_private_bytes(unb64(bootstrap["witness_private_b64"], 32))
        enrolled = unb64(bootstrap["client_pub_b64"], 32)
        with LoopbackWitness(args.db, signer, enrolled) as server:
            print(json.dumps({"status": "READY_LAB_ONLY", "port": server.server_address[1]}),
                  flush=True)
            server.serve_forever(poll_interval=0.1)
    else:
        if args.port is None:
            raise SystemExit(2)
        client = Ed25519PrivateKey.from_private_bytes(unb64(bootstrap["client_private_b64"], 32))
        pub = unb64(bootstrap["witness_pub_b64"], 32)
        if args.gate is not None:
            if (not args.gate.is_absolute()
                    or not args.gate.parent.name.startswith("dc06m-cas-synthetic-")
                    or not args.gate.parent.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())):
                raise SystemExit(2)
            (args.gate.parent / ("ready-" + str(os.getpid()))).touch()
            deadline = time.monotonic() + 10.0
            while not args.gate.exists():
                if time.monotonic() > deadline:
                    raise SystemExit(2)
                time.sleep(0.01)
        result = send_request(args.port, bootstrap["request"], client, pub)
        print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    cli()
