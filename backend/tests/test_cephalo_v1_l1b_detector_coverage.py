"""V1 L1-b: an ONNX output label is not proof of an exact Steiner structure.

This contract inventory is a guard, not a 15/15 auto-detector certification.
"""
from backend.services.srpose38_contract import SOTA_LANDMARKS_MAPPING
from backend.services.cephalo_landmark_identity_bridge import CANONICAL_LANDMARK_ALIASES
from backend.services.cephalo_steiner_protocol_evidence import _SPECS


EXACT_STEINER_STRUCTURES = frozenset({
    "Gn_anatomic",
    "U1_facial_surface",
    "L1_facial_surface",
    "Occ_Steiner_Ant",
    "Occ_Steiner_Post",
    "D_Steiner_1959",
})


def test_srpose38_has_no_direct_channel_for_steiner_explicit_structures():
    assert len(SOTA_LANDMARKS_MAPPING) == 38
    assert EXACT_STEINER_STRUCTURES.isdisjoint(set(SOTA_LANDMARKS_MAPPING.values()))
    assert EXACT_STEINER_STRUCTURES.isdisjoint(set(CANONICAL_LANDMARK_ALIASES.values()))


def test_specialized_steiner_constructions_are_explicitly_dependent():
    specialized_dependencies = {identity for spec in _SPECS for identity in spec.ids}
    assert EXACT_STEINER_STRUCTURES <= specialized_dependencies


def test_detector_d_and_generic_gn_must_not_be_assumed_steiner_equivalents():
    channels = set(SOTA_LANDMARKS_MAPPING.values())
    assert "D_point" in channels and "D_Steiner_1959" not in channels
    assert "Gn" in channels and "Gn_anatomic" not in channels
