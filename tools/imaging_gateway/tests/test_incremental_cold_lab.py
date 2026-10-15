"""Incremental compact cold verification: exact J/K MAC + unique media."""
from dataclasses import replace
import hashlib
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from tools.imaging_gateway import compact_cold_lab as c
from tools.imaging_gateway import incremental_cold_lab as inc
from tools.imaging_gateway import migration_lab as m
from tools.imaging_gateway import journal_lab as j
from tools.imaging_gateway import spool_version_lab as codec


class IncrementalColdTests(unittest.TestCase):
    def setUp(self):
        self.legacy=b"L"*32
        self.jkey=b"J"*32
        self.akey=b"A"*32
        self.keys={"ab"*16:b"T"*32}
        self.identity="e"*64

    def build(self, size=29, total=256):
        clear=b"x"*size
        digest=hashlib.sha256(clear).hexdigest()
        nonce=b"synthetic123"
        aad=("DC06A|lab_m|workstation_m|"+self.identity).encode("ascii")
        source=b"DC6A"+nonce+AESGCM(self.legacy).encrypt(nonce,clear,aad)
        snap=m.begin(source,cabinet="lab_m",workstation="workstation_m",
                     identity=self.identity,digest=digest,
                     legacy_key=self.legacy)
        prepared=m.prepare(snap,expected_revision=0,legacy_key=self.legacy,
                           target_key_id="ab"*16,keys=self.keys)
        store=c.VolatileBlobStore()
        sr=store.put(source)
        tr=store.put(prepared.candidate)
        current= c.SnapshotRef(
            snap.cabinet,snap.workstation,snap.identity,snap.digest,
            "SOURCE",0,sr,snap.source_sha256,None,None,None)
        prior_mac=j._ZERO_MAC
        records=[]
        for seq in range(1,total+1):
            if seq>1:
                phase={"SOURCE":"PREPARED","PREPARED":"VERIFIED",
                       "VERIFIED":"COMMITTED","COMMITTED":"ROLLED_BACK",
                       "ROLLED_BACK":"PREPARED"}[current.phase]
                revised=current.revision+1
                if phase=="ROLLED_BACK":
                    current=replace(current,phase=phase,revision=revised,
                                    candidate=None,candidate_sha256=None,
                                    target_key_id=None)
                else:
                    current=replace(current,phase=phase,revision=revised,
                                    candidate=tr,candidate_sha256=tr.sha256,
                                    target_key_id="ab"*16)
            mac=inc._event_mac(seq,prior_mac,current,self.jkey)
            records.append(c.CompactRecord(seq,prior_mac,mac,current))
            prior_mac=mac
        anchor=j.TrustedAnchor(total,prior_mac)
        unsigned=c.CompactBundle(anchor,tuple(records),"0"*64)
        bundle=replace(unsigned,seal=c._seal(unsigned,self.akey))
        return store,bundle,anchor,snap,prepared

    def audit(self,store,bundle,anchor,key=None):
        return inc.audit_unique_ciphertexts(
            bundle,anchor,store=store,archive_key=key or self.akey,
            journal_key=self.jkey,legacy_key=self.legacy,keys=self.keys)

    def test_mac_equivalent_to_original_JK_manifest_for_real_envelope(self):
        store,bundle,head,snap,prepared=self.build(total=3)
        genesis=bundle.records[0]
        self.assertEqual(genesis.mac,j._mac(1,j._ZERO_MAC,snap,self.jkey))
        self.assertEqual(bundle.records[1].mac,
            j._mac(2,genesis.mac,prepared,self.jkey))
        self.assertEqual(self.audit(store,bundle,head).event_count,3)

    def test_256_events_real_50mib_only_two_decryptions(self):
        store,bundle,head,snap,prepared=self.build(
            size=50*1024*1024,total=256)
        source_decode=codec.decode_legacy_v1
        target_decode=codec.decode_v2
        calls=[0,0]
        def source_once(*args,**kwargs):
            calls[0]+=1
            return source_decode(*args,**kwargs)
        def target_once(*args,**kwargs):
            calls[1]+=1
            return target_decode(*args,**kwargs)
        with patch.object(codec,"decode_legacy_v1",side_effect=source_once), \
             patch.object(codec,"decode_v2",side_effect=target_once):
            proof=self.audit(store,bundle,head)
        self.assertEqual(proof.event_count,256)
        self.assertEqual(proof.unique_ciphertexts,2)
        self.assertLessEqual(proof.unique_verified_bytes,101*1024*1024)
        self.assertEqual(calls,[1,1])
        self.assertEqual(proof.anchor,head)
        self.assertEqual(proof.metadata_sha256,
            hashlib.sha256(c._canonical(bundle)).hexdigest())

    def test_wrong_anchor_archive_seal_event_and_key_refuse(self):
        store,bundle,head,_,_=self.build(total=9)
        old=j.TrustedAnchor(head.sequence-1,bundle.records[-2].mac)
        with self.assertRaisesRegex(inc.IncrementalColdLabError,
                                    "INDEPENDENT_HEAD_MISMATCH"):
            self.audit(store,bundle,old)
        with self.assertRaisesRegex(inc.IncrementalColdLabError,
                                    "COMPACT_SEAL_REFUSE"):
            self.audit(store,replace(bundle,seal="0"*64),head)
        forged=replace(bundle.records[3],mac="0"*64)
        corrupt=replace(bundle,records=bundle.records[:3]+(forged,)+
                        bundle.records[4:])
        corrupt=replace(corrupt,seal=c._seal(corrupt,self.akey))
        with self.assertRaisesRegex(inc.IncrementalColdLabError,
                                    "JOURNAL_HMAC_REFUSE"):
            self.audit(store,corrupt,head)
        with self.assertRaisesRegex(inc.IncrementalColdLabError,
                                    "COMPACT_SEAL_REFUSE"):
            self.audit(store,bundle,head,key=b"Q"*32)

    def test_missing_corrupt_media_and_wrong_aead_key_refuse(self):
        store,bundle,head,_,_=self.build(total=9)
        sourcekey=bundle.records[0].snapshot.source.sha256
        original=store._blobs.pop(sourcekey)
        with self.assertRaisesRegex(inc.IncrementalColdLabError,
                                    "CIPHERTEXT_AUTHENTICATION_REFUSE"):
            self.audit(store,bundle,head)
        store._blobs[sourcekey]=original[:-1]+bytes([original[-1]^1])
        with self.assertRaisesRegex(inc.IncrementalColdLabError,
                                    "CIPHERTEXT_AUTHENTICATION_REFUSE"):
            self.audit(store,bundle,head)
        store._blobs[sourcekey]=original
        self.keys["ab"*16]=b"Z"*32
        with self.assertRaisesRegex(inc.IncrementalColdLabError,
                                    "CIPHERTEXT_AUTHENTICATION_REFUSE"):
            self.audit(store,bundle,head)

    def test_stale_archive_and_stale_anchor_both_still_pass_negative(self):
        store,bundle,head,_,_=self.build(total=9)
        prior=bundle.records[:7]
        old_head=j.TrustedAnchor(7,prior[-1].mac)
        unsigned=c.CompactBundle(old_head,prior,"0"*64)
        old=replace(unsigned,seal=c._seal(unsigned,self.akey))
        with self.assertRaisesRegex(inc.IncrementalColdLabError,
                                    "INDEPENDENT_HEAD_MISMATCH"):
            self.audit(store,old,head)
        # Explicit negative: together-rolled-back archive+head pass.
        self.assertEqual(self.audit(store,old,old_head).event_count,7)

    def test_unique_byte_budget_refuses_before_any_blob_get(self):
        store,bundle,head,_,_=self.build(total=9)
        with patch.object(inc,"_MAX_UNIQUE_COLD_VERIFY_BYTES",1), \
             patch.object(store,"get",side_effect=AssertionError("No read")):
            with self.assertRaisesRegex(inc.IncrementalColdLabError,
                                        "UNIQUE_VERIFICATION_BUDGET_REFUSE"):
                self.audit(store,bundle,head)

    def test_forged_epoch_or_phase_with_resealed_archive_fails_JK(self):
        store,bundle,head,_,_=self.build(total=9)
        altered=replace(bundle.records[3].snapshot,phase="VERIFIED")
        changed=replace(bundle.records[3],snapshot=altered)
        forged=replace(bundle,records=bundle.records[:3]+(changed,)+
                       bundle.records[4:])
        forged=replace(forged,seal=c._seal(forged,self.akey))
        with self.assertRaisesRegex(inc.IncrementalColdLabError,
                                    "JOURNAL_HMAC_REFUSE"):
            self.audit(store,forged,head)


if __name__=="__main__":
    unittest.main()
