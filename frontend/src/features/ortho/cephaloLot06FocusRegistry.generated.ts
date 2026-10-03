// AUTO-GENERATED from docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json
// Do not edit by hand. Regenerate with: python scripts/generate_cephalo_lot06_focus_registry.py

export interface CephaloCanonicalFocusDependency {
  measurementId: string;
  unit: string;
  requiredLandmarks: readonly string[];
  requiredConstructions: readonly string[];
  sourceContracts: readonly string[];
  availabilityGate: string;
  requiresCalibration: boolean;
}

export const CEPHALO_LOT06_FOCUS_REGISTRY = {
  "M_AB_PRIME_FH_MM_V1": {
    "measurementId": "M_AB_PRIME_FH_MM_V1",
    "unit": "mm",
    "requiredLandmarks": [
      "A",
      "B",
      "Po_anatomic",
      "Or"
    ],
    "requiredConstructions": [
      "FH_PO_OR_V1",
      "CRANIOM_AB_PRIME_V1"
    ],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md",
      "docs/CEPHALO_CONSTRUCTION_REGISTRY.md"
    ],
    "availabilityGate": "VERIFIED_CALIBRATION_AND_PO_ANATOMIC",
    "requiresCalibration": true
  },
  "M_ANB_DEG_V1": {
    "measurementId": "M_ANB_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "S",
      "N",
      "A",
      "B"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md"
    ],
    "availabilityGate": "ALL_REQUIRED_LANDMARKS_EXACT",
    "requiresCalibration": false
  },
  "M_ANS_ME_MM_V1": {
    "measurementId": "M_ANS_ME_MM_V1",
    "unit": "mm",
    "requiredLandmarks": [
      "ANS",
      "Me"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md"
    ],
    "availabilityGate": "VERIFIED_CALIBRATION",
    "requiresCalibration": true
  },
  "M_A_NPERP_MM_V1": {
    "measurementId": "M_A_NPERP_MM_V1",
    "unit": "mm",
    "requiredLandmarks": [
      "A",
      "N",
      "Po_anatomic",
      "Or"
    ],
    "requiredConstructions": [
      "FH_PO_OR_V1",
      "NASION_VERTICAL_FH_V1"
    ],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md",
      "docs/CEPHALO_CONSTRUCTION_REGISTRY.md"
    ],
    "availabilityGate": "VERIFIED_CALIBRATION_AND_PO_ANATOMIC",
    "requiresCalibration": true
  },
  "M_B_NPERP_MM_V1": {
    "measurementId": "M_B_NPERP_MM_V1",
    "unit": "mm",
    "requiredLandmarks": [
      "B",
      "N",
      "Po_anatomic",
      "Or"
    ],
    "requiredConstructions": [
      "FH_PO_OR_V1",
      "NASION_VERTICAL_FH_V1"
    ],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md",
      "docs/CEPHALO_CONSTRUCTION_REGISTRY.md"
    ],
    "availabilityGate": "VERIFIED_CALIBRATION_AND_PO_ANATOMIC",
    "requiresCalibration": true
  },
  "M_COM_S_NPERP_DEPTH_MM_V1": {
    "measurementId": "M_COM_S_NPERP_DEPTH_MM_V1",
    "unit": "mm",
    "requiredLandmarks": [
      "S",
      "N",
      "Po_anatomic",
      "Or"
    ],
    "requiredConstructions": [
      "FH_PO_OR_V1",
      "NASION_VERTICAL_FH_V1",
      "CRANIOM_S_TO_N_VERTICAL_DEPTH_V1"
    ],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md",
      "docs/CEPHALO_CONSTRUCTION_REGISTRY.md"
    ],
    "availabilityGate": "VERIFIED_CALIBRATION_AND_PO_ANATOMIC",
    "requiresCalibration": true
  },
  "M_CO_A_MM_V1": {
    "measurementId": "M_CO_A_MM_V1",
    "unit": "mm",
    "requiredLandmarks": [
      "Co_anatomic",
      "A"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md"
    ],
    "availabilityGate": "VERIFIED_CALIBRATION_AND_EXACT_CO",
    "requiresCalibration": true
  },
  "M_CO_GN_ANATOMIC_MM_V1": {
    "measurementId": "M_CO_GN_ANATOMIC_MM_V1",
    "unit": "mm",
    "requiredLandmarks": [
      "Co_anatomic",
      "Gn_anatomic"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md",
      "docs/audits/CEPHALO_VNEXT_LOT03_LANDMARK_ATLAS.md"
    ],
    "availabilityGate": "VERIFIED_CALIBRATION_AND_EXACT_ANATOMIC_GN",
    "requiresCalibration": true
  },
  "M_DOWNS_FACIAL_ANGLE_NPOG_FH_ACUTE_DEG_V1": {
    "measurementId": "M_DOWNS_FACIAL_ANGLE_NPOG_FH_ACUTE_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "Po_anatomic",
      "Or",
      "N",
      "Pog_hard"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_VNEXT_LOT06_CANONICAL_LANDMARK_IDENTITY_BRIDGE.md",
      "docs/audits/CEPHALO_VNEXT_LOT01_SCIENTIFIC_CONTRACT.md",
      "docs/audits/CEPHALO_VNEXT_LOT06_MUST_HAVE_SOURCE_LOCK.md"
    ],
    "availabilityGate": "ALL_REQUIRED_LANDMARKS_EXACT",
    "requiresCalibration": false
  },
  "M_DOWNS_Y_AXIS_SGN_FH_DEG_V1": {
    "measurementId": "M_DOWNS_Y_AXIS_SGN_FH_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "S",
      "Gn_anatomic",
      "Po_anatomic",
      "Or"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_VNEXT_LOT06_CANONICAL_LANDMARK_IDENTITY_BRIDGE.md",
      "docs/audits/CEPHALO_VNEXT_LOT01_SCIENTIFIC_CONTRACT.md",
      "docs/audits/CEPHALO_VNEXT_LOT06_MUST_HAVE_SOURCE_LOCK.md"
    ],
    "availabilityGate": "ALL_REQUIRED_LANDMARKS_EXACT",
    "requiresCalibration": false
  },
  "M_FH_GOME_DEG_V1": {
    "measurementId": "M_FH_GOME_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "Po_anatomic",
      "Or",
      "Go",
      "Me"
    ],
    "requiredConstructions": [
      "FH_PO_OR_V1",
      "TWEED_DC_MP_GO_ME_V1"
    ],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md"
    ],
    "availabilityGate": "PO_ANATOMIC_AND_GO_ME_REQUIRED",
    "requiresCalibration": false
  },
  "M_FMIA_L1_FH_DEG_V1": {
    "measurementId": "M_FMIA_L1_FH_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "L1_apex",
      "L1_incisal",
      "Po_anatomic",
      "Or"
    ],
    "requiredConstructions": [
      "FH_PO_OR_V1"
    ],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md"
    ],
    "availabilityGate": "PO_ANATOMIC_REQUIRED",
    "requiresCalibration": false
  },
  "M_IMPA_GOME_DEG_V1": {
    "measurementId": "M_IMPA_GOME_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "L1_apex",
      "L1_incisal",
      "Go",
      "Me"
    ],
    "requiredConstructions": [
      "TWEED_DC_MP_GO_ME_V1"
    ],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md"
    ],
    "availabilityGate": "ALL_REQUIRED_LANDMARKS_EXACT",
    "requiresCalibration": false
  },
  "M_INTERINCISAL_DEG_V1": {
    "measurementId": "M_INTERINCISAL_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "U1_apex",
      "U1_incisal",
      "L1_apex",
      "L1_incisal"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md"
    ],
    "availabilityGate": "ALL_REQUIRED_LANDMARKS_EXACT",
    "requiresCalibration": false
  },
  "M_L1_NB_DEG_V1": {
    "measurementId": "M_L1_NB_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "L1_apex",
      "L1_incisal",
      "N",
      "B"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md"
    ],
    "availabilityGate": "ALL_REQUIRED_LANDMARKS_EXACT",
    "requiresCalibration": false
  },
  "M_LI_EPLANE_MM_V1": {
    "measurementId": "M_LI_EPLANE_MM_V1",
    "unit": "mm",
    "requiredLandmarks": [
      "Li_soft",
      "Prn",
      "Pog_soft",
      "Po_anatomic",
      "Or"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_VNEXT_LOT06_CANONICAL_LANDMARK_IDENTITY_BRIDGE.md",
      "docs/audits/CEPHALO_VNEXT_LOT01_SCIENTIFIC_CONTRACT.md",
      "docs/audits/CEPHALO_VNEXT_LOT06_MUST_HAVE_SOURCE_LOCK.md"
    ],
    "availabilityGate": "VERIFIED_CALIBRATION_AND_CANONICAL_IDENTITIES",
    "requiresCalibration": true
  },
  "M_LS_EPLANE_MM_V1": {
    "measurementId": "M_LS_EPLANE_MM_V1",
    "unit": "mm",
    "requiredLandmarks": [
      "Ls_soft",
      "Prn",
      "Pog_soft",
      "Po_anatomic",
      "Or"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_VNEXT_LOT06_CANONICAL_LANDMARK_IDENTITY_BRIDGE.md",
      "docs/audits/CEPHALO_VNEXT_LOT01_SCIENTIFIC_CONTRACT.md",
      "docs/audits/CEPHALO_VNEXT_LOT06_MUST_HAVE_SOURCE_LOCK.md"
    ],
    "availabilityGate": "VERIFIED_CALIBRATION_AND_CANONICAL_IDENTITIES",
    "requiresCalibration": true
  },
  "M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1": {
    "measurementId": "M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1",
    "unit": "mm",
    "requiredLandmarks": [
      "A",
      "N",
      "Pog_hard",
      "Po_anatomic",
      "Or"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_VNEXT_LOT06_CANONICAL_LANDMARK_IDENTITY_BRIDGE.md",
      "docs/audits/CEPHALO_VNEXT_LOT01_SCIENTIFIC_CONTRACT.md",
      "docs/audits/CEPHALO_VNEXT_LOT06_MUST_HAVE_SOURCE_LOCK.md"
    ],
    "availabilityGate": "VERIFIED_CALIBRATION_AND_CANONICAL_IDENTITIES",
    "requiresCalibration": true
  },
  "M_MERRIFIELD_Z_FH_DEG_V1": {
    "measurementId": "M_MERRIFIELD_Z_FH_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "Po_anatomic",
      "Or",
      "Pog_soft",
      "Ls_soft",
      "Li_soft"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_VNEXT_LOT06_CANONICAL_LANDMARK_IDENTITY_BRIDGE.md",
      "docs/audits/CEPHALO_VNEXT_LOT01_SCIENTIFIC_CONTRACT.md",
      "docs/audits/CEPHALO_VNEXT_LOT06_MUST_HAVE_SOURCE_LOCK.md"
    ],
    "availabilityGate": "ALL_REQUIRED_LANDMARKS_EXACT",
    "requiresCalibration": false
  },
  "M_POG_NPERP_MM_V1": {
    "measurementId": "M_POG_NPERP_MM_V1",
    "unit": "mm",
    "requiredLandmarks": [
      "Pog_hard",
      "N",
      "Po_anatomic",
      "Or"
    ],
    "requiredConstructions": [
      "FH_PO_OR_V1",
      "NASION_VERTICAL_FH_V1"
    ],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md",
      "docs/audits/CEPHALO_GLOBAL_ANALYSIS_CARTOGRAPHY.md"
    ],
    "availabilityGate": "VERIFIED_CALIBRATION_AND_EXACT_POG_HARD_AND_PO_ANATOMIC",
    "requiresCalibration": true
  },
  "M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1": {
    "measurementId": "M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "Po_anatomic",
      "Or",
      "N",
      "Pog_hard"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_VNEXT_LOT06_CANONICAL_LANDMARK_IDENTITY_BRIDGE.md",
      "docs/audits/CEPHALO_VNEXT_LOT01_SCIENTIFIC_CONTRACT.md",
      "docs/audits/CEPHALO_VNEXT_LOT06_MUST_HAVE_SOURCE_LOCK.md"
    ],
    "availabilityGate": "ALL_REQUIRED_LANDMARKS_EXACT",
    "requiresCalibration": false
  },
  "M_SNA_DEG_V1": {
    "measurementId": "M_SNA_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "S",
      "N",
      "A"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md"
    ],
    "availabilityGate": "ALL_REQUIRED_LANDMARKS_EXACT",
    "requiresCalibration": false
  },
  "M_SNB_DEG_V1": {
    "measurementId": "M_SNB_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "S",
      "N",
      "B"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md"
    ],
    "availabilityGate": "ALL_REQUIRED_LANDMARKS_EXACT",
    "requiresCalibration": false
  },
  "M_SN_GOGN_DEG_V1": {
    "measurementId": "M_SN_GOGN_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "S",
      "N",
      "Go",
      "Gn_anatomic"
    ],
    "requiredConstructions": [
      "STEINER_MP_GO_GN_V1"
    ],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md",
      "docs/audits/CEPHALO_VNEXT_LOT03_LANDMARK_ATLAS.md"
    ],
    "availabilityGate": "EXACT_GN_ANATOMIC_REQUIRED",
    "requiresCalibration": false
  },
  "M_U1_FH_DEG_V1": {
    "measurementId": "M_U1_FH_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "U1_apex",
      "U1_incisal",
      "Po_anatomic",
      "Or"
    ],
    "requiredConstructions": [
      "FH_PO_OR_V1"
    ],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md",
      "docs/CEPHALO_CONSTRUCTION_REGISTRY.md"
    ],
    "availabilityGate": "PO_ANATOMIC_REQUIRED",
    "requiresCalibration": false
  },
  "M_U1_NA_DEG_V1": {
    "measurementId": "M_U1_NA_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "U1_apex",
      "U1_incisal",
      "N",
      "A"
    ],
    "requiredConstructions": [],
    "sourceContracts": [
      "docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md"
    ],
    "availabilityGate": "ALL_REQUIRED_LANDMARKS_EXACT",
    "requiresCalibration": false
  },
  "M_FACIAL_AXIS_RICKETTS_DEG_V1": {
    "measurementId": "M_FACIAL_AXIS_RICKETTS_DEG_V1",
    "unit": "°",
    "requiredLandmarks": [
      "Ba",
      "N",
      "Pt_Ricketts",
      "Pog_hard",
      "Go",
      "Me"
    ],
    "requiredConstructions": [
      "RICKETTS_GN_CONSTRUCTED_NPOG_GOME_V1"
    ],
    "sourceContracts": [
      "docs/audits/CEPHALO_VNEXT_LOT01_SCIENTIFIC_CONTRACT.md",
      "docs/audits/CEPHALO_VNEXT_LOT06_MUST_HAVE_SOURCE_LOCK.md"
    ],
    "availabilityGate": "EXPLICIT_PT_RICKETTS_AND_CANONICAL_HARD_TISSUE_IDENTITIES",
    "requiresCalibration": false
  }
} as const satisfies Record<string, CephaloCanonicalFocusDependency>;

export const CEPHALO_LOT06_FOCUS_REGISTRY_SOURCE =
  'docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json' as const;
