"""LOT06-E capability and fail-closed mock tests; no device or backend."""
import unittest

from tools.imaging_gateway.adapters import (
    AdapterRejected, AdapterStatus, SourceKind, capability, propose_capture,
)


def valid(**updates):
    kwargs = dict(
        kind=SourceKind.HOT_FOLDER, capture_id="synthetic_capture_001",
        sha256="a" * 64, byte_size=10, category="PHOTO_CLINICAL",
        mime_type="image/png", workstation="workstation1",
    )
    kwargs.update(updates)
    return kwargs


class AdapterContractTests(unittest.TestCase):
    def test_all_device_types_explicitly_declared(self):
        self.assertEqual(set(SourceKind), set(SourceKind(k) for k in SourceKind))
        for kind in SourceKind:
            cap = capability(kind)
            self.assertFalse(cap.certified_hardware)
            self.assertFalse(cap.supports_patient_link)
            self.assertFalse(cap.supports_live_capture)

    def test_hot_folder_only_simulated(self):
        self.assertEqual(capability(SourceKind.HOT_FOLDER).status, AdapterStatus.SIMULATED)
        self.assertEqual(propose_capture(**valid()).kind, SourceKind.HOT_FOLDER)

    def test_no_twain_dicom_or_vendor_driver_activation(self):
        for kind in [SourceKind.TWAIN, SourceKind.DICOM, SourceKind.VENDOR_SDK]:
            with self.subTest(kind=kind), self.assertRaises(AdapterRejected):
                propose_capture(**valid(kind=kind))

    def test_unknown_adapter_rejected(self):
        with self.assertRaises(AdapterRejected):
            capability("HOT_FOLDER")

    def test_bad_hash_and_capture_id_rejected(self):
        for opts in [{"sha256": "ABC" * 21 + "A"}, {"sha256": "0" * 63},
                     {"capture_id": "a/b"}, {"capture_id": "short"}]:
            with self.subTest(opts=opts), self.assertRaises(AdapterRejected):
                propose_capture(**valid(**opts))

    def test_byte_count_checked_with_strict_type_and_limit(self):
        for size in [-1, 0, True, 50 * 1024 * 1024 + 1]:
            with self.subTest(size=size), self.assertRaises(AdapterRejected):
                propose_capture(**valid(byte_size=size))

    def test_no_radiograph_without_real_parser(self):
        for kind in ["RVG", "PANORAMIC", "CEPHALOMETRY"]:
            with self.subTest(kind=kind), self.assertRaises(AdapterRejected):
                propose_capture(**valid(category=kind, mime_type="image/png"))

    def test_no_untrusted_mime_and_unknown_category(self):
        for change in [{"mime_type": "application/dicom"},
                       {"category": "ORTHO_MADE_UP"}, {"workstation": "../other"}]:
            with self.subTest(change=change), self.assertRaises(AdapterRejected):
                propose_capture(**valid(**change))

    def test_proposal_contains_no_patient_or_server_receipt(self):
        p = propose_capture(**valid())
        fields = set(vars(p))
        self.assertNotIn("patient_id", fields)
        self.assertNotIn("appointment_id", fields)
        self.assertNotIn("server_confirmed", fields)
        self.assertNotIn("receipt_id", fields)


if __name__ == "__main__":
    unittest.main()
