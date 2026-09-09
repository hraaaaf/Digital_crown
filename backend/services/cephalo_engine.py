"""Fail-closed cephalometric geometry engine.

This module computes only patient-observed geometric measurements from supplied
landmarks. It deliberately contains no clinical norms, z-scores, diagnostic
classification, growth projection, treatment strategy, or invented patient
context.
"""

import math
from typing import Dict, Optional, Tuple

from backend import schemas


Point = Tuple[float, float]


class CephaloEngine:
    """Deterministic geometry-only cephalometric engine."""

    def __init__(self, mm_per_pixel: Optional[float] = None):
        self.mm_per_pixel = mm_per_pixel
        self.key_mapping = {
            "S": ["S", "Sella"],
            "N": ["N", "Nasion"],
            "Po": ["Po", "Porion"],
            "Or": ["Or", "Orbitale"],
            "A": ["A", "Point_A"],
            "B": ["B", "Point_B"],
            "Go": ["Go", "Gonion"],
            "Me": ["Me", "Menton"],
            "U1i": ["U1i", "U1_incisal", "11_incisal", "UIe"],
            "U1a": ["U1a", "U1_apex", "11_apex", "UIa"],
            "L1i": ["L1i", "L1_incisal", "41_incisal", "LIe"],
            "L1a": ["L1a", "L1_apex", "41_apex", "LIa"],
            "Prn": ["Prn", "Pronasale", "Nose_Tip"],
            "Pog_soft": ["Pog_soft", "Soft_Pogonion", "stPog", "stpog", "Soft_Pog"],
            "Sn": ["Sn", "Sn_soft", "Subnasale"],
            "Ls": ["Ls", "Ls_soft", "Labrale_Superius", "UL", "ul", "Upper_Lip"],
            "Li": ["Li", "Li_soft", "Labrale_Inferius", "LL", "ll", "Lower_Lip"],
            "Co": ["Co", "Condylion", "Condyle"],
            "Gn": ["Gn", "Gnathion"],
            "ANS": ["ANS", "ENA", "Anterior_Nasal_Spine"],
            "Occ_Ant": ["Occ_Ant", "Occlusal_Anterior", "Occlusal_Incisive"],
            "Occ_Post": ["Occ_Post", "Occlusal_Posterior", "Occlusal_Molar"],
        }

    def _get_point(self, points: Dict, canonical_key: str) -> Optional[Point]:
        if canonical_key in points:
            point = points[canonical_key]
            return (point[0], point[1]) if isinstance(point, (list, tuple)) else None
        for alias in self.key_mapping.get(canonical_key, []):
            if alias in points:
                point = points[alias]
                return (point[0], point[1]) if isinstance(point, (list, tuple)) else None
        return None

    @staticmethod
    def _get_clinical_angle(
        p1: Optional[Point],
        p2: Optional[Point],
        p3: Optional[Point],
        p4: Optional[Point],
        invert: bool = False,
    ) -> Optional[float]:
        if not all((p1, p2, p3, p4)):
            return None
        assert p1 is not None and p2 is not None and p3 is not None and p4 is not None
        a1 = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
        a2 = math.degrees(math.atan2(p4[1] - p3[1], p4[0] - p3[0]))
        angle = abs(a1 - a2) % 180
        if invert:
            angle = 180 - angle
        return round(angle, 1)

    @staticmethod
    def _get_orthogonal_projection(line_p1: Point, line_p2: Point, target: Point) -> Point:
        dx = line_p2[0] - line_p1[0]
        dy = line_p2[1] - line_p1[1]
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            return target
        t = ((target[0] - line_p1[0]) * dx + (target[1] - line_p1[1]) * dy) / length_sq
        return (line_p1[0] + t * dx, line_p1[1] + t * dy)

    @staticmethod
    def _raw_measurement(value: Optional[float]) -> dict:
        """Serialize one observed/computed value without clinical interpretation."""
        return {
            "valeur": round(value, 1) if value is not None else None,
            "norm_mean": None,
            "norm_min": None,
            "norm_max": None,
            "plage_compensation": None,
            "status": "N/A",
            "interpretation": "Non calculé" if value is None else "Mesure géométrique brute",
            "z_score": None,
        }

    @staticmethod
    def _signed_e_line_distance(
        lip: Optional[Point],
        prn: Optional[Point],
        pog_soft: Optional[Point],
        po: Optional[Point],
        or_: Optional[Point],
        ratio: Optional[float],
    ) -> Optional[float]:
        if not all((lip, prn, pog_soft, po, or_)) or ratio is None:
            return None
        assert lip is not None and prn is not None and pog_soft is not None
        assert po is not None and or_ is not None
        epsilon = 1e-6
        e_x, e_y = pog_soft[0] - prn[0], pog_soft[1] - prn[1]
        e_length_sq = e_x * e_x + e_y * e_y
        a_x, a_y = or_[0] - po[0], or_[1] - po[1]
        a_length = math.hypot(a_x, a_y)
        if e_length_sq <= epsilon * epsilon or a_length <= epsilon:
            return None
        t = ((lip[0] - prn[0]) * e_x + (lip[1] - prn[1]) * e_y) / e_length_sq
        q_x, q_y = prn[0] + t * e_x, prn[1] + t * e_y
        r_x, r_y = lip[0] - q_x, lip[1] - q_y
        magnitude_px = math.hypot(r_x, r_y)
        if magnitude_px <= epsilon:
            return 0.0
        anterior_score = r_x * (a_x / a_length) + r_y * (a_y / a_length)
        if abs(anterior_score) <= epsilon:
            return None
        return math.copysign(magnitude_px * ratio, anterior_score)

    def calculate_metrics(
        self,
        raw_points: Dict,
        custom_mm_ratio: Optional[float] = None,
        age: Optional[int] = None,
        sex: Optional[str] = None,
        cvm_stage: Optional[str] = None,
        mcnamara_projections: Optional[Dict] = None,
    ) -> schemas.CephaloAnalysisResult:
        """Compute raw geometry only.

        age, sex and cvm_stage remain accepted for API compatibility but are not
        used to infer norms, growth, diagnosis or treatment.
        """
        del age, sex, cvm_stage
        pts = {key: self._get_point(raw_points, key) for key in self.key_mapping}
        ratio = custom_mm_ratio if custom_mm_ratio is not None else self.mm_per_pixel
        has_calibration = ratio is not None and ratio > 0

        payload = {
            "analysis_metadata": {
                "unit": "mm",
                "pixel_ratio": ratio,
                "type": "COM_Skeletal",
                "cohort": "Non classé",
            },
            "metrics": {
                "analyse_dentaire": {},
                "analyse_osseuse": {},
                "analyse_esthetique": {},
            },
            "visual_debug": {"N_prime": None, "A_prime": None, "B_prime": None},
            "t1_projection": {},
            "t2_projection": {},
            "ai_narrative": {},
            "clinical_data": {
                "ddm_maxillaire": None,
                "ddm_mandibulaire": None,
                "ddm_reelle": None,
                "plan_traitement": "",
            },
        }

        dental = payload["metrics"]["analyse_dentaire"]
        skeletal = payload["metrics"]["analyse_osseuse"]
        esthetic = payload["metrics"]["analyse_esthetique"]

        u_fh: Optional[Point] = None
        u_perp: Optional[Point] = None
        if pts["Po"] and pts["Or"]:
            v_fh = (pts["Or"][0] - pts["Po"][0], pts["Or"][1] - pts["Po"][1])
            magnitude = math.hypot(v_fh[0], v_fh[1])
            if magnitude > 0:
                u_fh = (v_fh[0] / magnitude, v_fh[1] / magnitude)
                u_perp = (-u_fh[1], u_fh[0])
                if u_perp[1] < 0:
                    u_perp = (-u_perp[0], -u_perp[1])

        if has_calibration and u_fh and u_perp and pts["U1i"] and pts["L1i"]:
            assert ratio is not None
            v_incisif = (
                pts["U1i"][0] - pts["L1i"][0],
                pts["U1i"][1] - pts["L1i"][1],
            )
            surplomb = (v_incisif[0] * u_fh[0] + v_incisif[1] * u_fh[1]) * ratio
            recouvrement = (v_incisif[0] * u_perp[0] + v_incisif[1] * u_perp[1]) * ratio
            dental["Surplomb"] = self._raw_measurement(surplomb)
            dental["Recouvrement"] = self._raw_measurement(recouvrement)

        impa_raw = self._get_clinical_angle(pts["L1a"], pts["L1i"], pts["Go"], pts["Me"])
        impa = round(180 - impa_raw, 1) if impa_raw is not None else None
        dental["IMPA"] = self._raw_measurement(impa)

        i_fh_raw = self._get_clinical_angle(pts["U1a"], pts["U1i"], pts["Po"], pts["Or"])
        i_francfort = round(180 - i_fh_raw, 1) if i_fh_raw is not None else None
        dental["I_Francfort"] = self._raw_measurement(i_francfort)

        inter_raw = self._get_clinical_angle(pts["U1a"], pts["U1i"], pts["L1a"], pts["L1i"])
        inter_incisif = round(max(inter_raw, 180 - inter_raw), 1) if inter_raw is not None else None
        dental["Inter_Incisif"] = self._raw_measurement(inter_incisif)

        sna: Optional[float] = None
        snb: Optional[float] = None
        if pts["S"] and pts["N"]:
            if pts["A"]:
                sna = self._get_clinical_angle(pts["N"], pts["S"], pts["N"], pts["A"])
            if pts["B"]:
                snb = self._get_clinical_angle(pts["N"], pts["S"], pts["N"], pts["B"])
        skeletal["SNA"] = self._raw_measurement(sna)
        skeletal["SNB"] = self._raw_measurement(snb)
        skeletal["ANB"] = self._raw_measurement(sna - snb if sna is not None and snb is not None else None)

        fma = self._get_clinical_angle(pts["Go"], pts["Me"], pts["Po"], pts["Or"])
        skeletal["Angle_de_Tweed"] = self._raw_measurement(fma)

        sit_a: Optional[float] = None
        sit_b: Optional[float] = None
        dec_ab: Optional[float] = None
        facial_depth: Optional[float] = None
        if has_calibration and u_fh and pts["N"]:
            assert ratio is not None
            if pts["A"]:
                sit_a = (
                    (pts["A"][0] - pts["N"][0]) * u_fh[0]
                    + (pts["A"][1] - pts["N"][1]) * u_fh[1]
                ) * ratio
            if pts["B"]:
                sit_b = (
                    (pts["B"][0] - pts["N"][0]) * u_fh[0]
                    + (pts["B"][1] - pts["N"][1]) * u_fh[1]
                ) * ratio
            if pts["S"]:
                facial_depth = abs(
                    (pts["S"][0] - pts["N"][0]) * u_fh[0]
                    + (pts["S"][1] - pts["N"][1]) * u_fh[1]
                ) * ratio
            if sit_a is not None and sit_b is not None:
                dec_ab = sit_a - sit_b

        if has_calibration and u_fh and pts["Po"] and pts["Or"]:
            assert ratio is not None
            if pts["N"]:
                n_prime = self._get_orthogonal_projection(pts["Po"], pts["Or"], pts["N"])
                payload["visual_debug"]["N_prime"] = [round(n_prime[0], 2), round(n_prime[1], 2)]
            if pts["A"]:
                a_prime = self._get_orthogonal_projection(pts["Po"], pts["Or"], pts["A"])
                payload["visual_debug"]["A_prime"] = [round(a_prime[0], 2), round(a_prime[1], 2)]
            if pts["B"]:
                b_prime = self._get_orthogonal_projection(pts["Po"], pts["Or"], pts["B"])
                payload["visual_debug"]["B_prime"] = [round(b_prime[0], 2), round(b_prime[1], 2)]

            n_prime = payload["visual_debug"].get("N_prime")
            a_prime = payload["visual_debug"].get("A_prime")
            b_prime = payload["visual_debug"].get("B_prime")
            if mcnamara_projections:
                n_prime = n_prime or mcnamara_projections.get("N_prime")
                a_prime = a_prime or mcnamara_projections.get("A_prime")
                b_prime = b_prime or mcnamara_projections.get("B_prime")

            if n_prime and a_prime:
                v_na = (a_prime[0] - n_prime[0], a_prime[1] - n_prime[1])
                sit_a = (v_na[0] * u_fh[0] + v_na[1] * u_fh[1]) * ratio
            if n_prime and b_prime:
                v_nb = (b_prime[0] - n_prime[0], b_prime[1] - n_prime[1])
                sit_b = (v_nb[0] * u_fh[0] + v_nb[1] * u_fh[1]) * ratio
            if a_prime and b_prime:
                v_ab = (a_prime[0] - b_prime[0], a_prime[1] - b_prime[1])
                dec_ab = (v_ab[0] * u_fh[0] + v_ab[1] * u_fh[1]) * ratio

        skeletal["Situation_A"] = self._raw_measurement(sit_a)
        skeletal["Situation_B"] = self._raw_measurement(sit_b)
        skeletal["Decalage_A_B"] = self._raw_measurement(dec_ab)
        skeletal["Profondeur_Faciale"] = self._raw_measurement(facial_depth)

        prn = pts.get("Prn")
        pog_soft = pts.get("Pog_soft")
        if has_calibration and prn and pog_soft and pts["Po"] and pts["Or"]:
            esthetic["Ligne_E_Ls"] = self._raw_measurement(
                self._signed_e_line_distance(pts.get("Ls"), prn, pog_soft, pts["Po"], pts["Or"], ratio)
            )
            esthetic["Ligne_E_Li"] = self._raw_measurement(
                self._signed_e_line_distance(pts.get("Li"), prn, pog_soft, pts["Po"], pts["Or"], ratio)
            )

        return schemas.CephaloAnalysisResult.model_validate(payload)


cephalo_engine = CephaloEngine()
