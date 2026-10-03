"""Lightweight immutable SRPose38 runtime identity contract.

No model loading, OpenCV, numpy or ONNX runtime side effects belong here.
Scientific/evidence code may safely import these constants.
"""
from __future__ import annotations

SRPOSE38_MODEL_NAME = "srpose38-tta-1024.onnx"
SRPOSE38_MODEL_SHA256 = "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
SRPOSE38_MODEL_SIZE_BYTES = 267_484_931
SRPOSE38_PIPELINE_VERSION = "SRPOSE38_TTA_1024_V1"

SOTA_LANDMARKS_MAPPING = {
    0: "S", 1: "N", 2: "Or", 3: "Po", 4: "A", 5: "B", 6: "Pog", 7: "Me",
    8: "Gn", 9: "Go", 10: "L1_incisal", 11: "U1_incisal",
    12: "Ls_soft", 13: "Li_soft", 14: "Sn_soft", 15: "Pog_soft",
    16: "PNS", 17: "ANS", 18: "Ar", 19: "D_point", 20: "U1_apex", 21: "L1_apex",
    22: "Cm", 23: "Ptm", 24: "Co", 25: "Prn", 26: "Ba", 27: "PT_point", 28: "Bo",
    29: "Ls2", 30: "Li2", 31: "Gn_soft", 32: "Me_soft", 33: "G_soft", 34: "N_soft",
    35: "C_point", 36: "U6", 37: "L6",
}
