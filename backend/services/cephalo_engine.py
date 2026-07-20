import math
import logging
from typing import Dict, Optional, Tuple, List, Any
from backend import schemas

logger = logging.getLogger(__name__)

class CephaloEngine:
    """
    Moteur géométrique COM-Skeletal V4 (Console Bilan Premium).
    Orchestre les calculs COM, le morphing T1, le diagnostic SLM et la DDM Réelle.
    """

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
            # Alias *_soft : nomenclature émise par le modèle SOTA (sota_vision_service).
            # Sans eux, Ligne E et angle nasolabial ne se calculent jamais avec les points SOTA.
            "Sn": ["Sn", "Sn_soft", "Subnasale"],
            "Ls": ["Ls", "Ls_soft", "Labrale_Superius", "UL", "ul", "Upper_Lip"],
            "Li": ["Li", "Li_soft", "Labrale_Inferius", "LL", "ll", "Lower_Lip"],
            "Co": ["Co", "Condylion", "Condyle"],
            "Gn": ["Gn", "Gnathion"],
            "ANS": ["ANS", "ENA", "Anterior_Nasal_Spine"],
            "Occ_Ant": ["Occ_Ant", "Occlusal_Anterior", "Occlusal_Incisive"],
            "Occ_Post": ["Occ_Post", "Occlusal_Posterior", "Occlusal_Molar"]
        }

    # --- UTILITAIRES GÉOMÉTRIQUES ---

    def _get_point(self, points: Dict, canonical_key: str) -> Optional[Tuple[float, float]]:
        if canonical_key in points:
            p = points[canonical_key]
            return (p[0], p[1]) if isinstance(p, (list, tuple)) else None
        for alias in self.key_mapping.get(canonical_key, []):
            if alias in points:
                p = points[alias]
                return (p[0], p[1]) if isinstance(p, (list, tuple)) else None
        return None

    def _get_clinical_angle(self, p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float], p4: Tuple[float, float], invert: bool = False) -> Optional[float]:
        """Calcule l'angle absolu d'intersection avec option d'inversion clinique."""
        if not all([p1, p2, p3, p4]): return None

        a1 = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
        a2 = math.degrees(math.atan2(p4[1] - p3[1], p4[0] - p3[0]))

        angle = abs(a1 - a2) % 180
        if invert:
            angle = 180 - angle
        return round(angle, 1)

    def _get_orthogonal_projection(self, line_p1: Tuple[float, float], line_p2: Tuple[float, float], target: Tuple[float, float]) -> Tuple[float, float]:
        """Projette orthogonalement le point 'target' sur la droite (p1-p2)."""
        dx = line_p2[0] - line_p1[0]
        dy = line_p2[1] - line_p1[1]
        l2 = dx**2 + dy**2
        if l2 == 0: return target
        t = ((target[0] - line_p1[0]) * dx + (target[1] - line_p1[1]) * dy) / l2
        return (line_p1[0] + t * dx, line_p1[1] + t * dy)

    def _signed_e_line_distance(
        self,
        lip: Optional[Tuple[float, float]],
        prn: Optional[Tuple[float, float]],
        pog_soft: Optional[Tuple[float, float]],
        po: Optional[Tuple[float, float]],
        or_: Optional[Tuple[float, float]],
        ratio: Optional[float],
    ) -> Optional[float]:
        """Return lip-to-E-line distance signed by the anatomical Po -> Or axis.

        The E-line itself is undirected, so reversing Prn/Pog_soft cannot change
        the result. ``_ELINE_EPSILON_PX`` only protects degenerate pixel geometry;
        it is not a clinical threshold.
        """
        if not all((lip, prn, pog_soft, po, or_)) or ratio is None:
            return None

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

    # --- MOTEUR DE DATA QUALITY & COMPENSATIONS ---

    def _evaluate_metric(self, value: Optional[float], mean: float, dev: float, inc_msg: str, dec_msg: str, norm_msg: str, comp_range: Optional[Tuple[float, float]] = None) -> dict:
        """Génère le format Machine-Readable avec bornes strictes et gestion des compensations."""
        min_val = round(mean - dev, 2)
        max_val = round(mean + dev, 2)

        if value is None:
            return {
                "valeur": None,
                "norm_mean": float(mean),
                "norm_min": float(min_val),
                "norm_max": float(max_val),
                "plage_compensation": comp_range,
                "status": "Missing",
                "interpretation": "Points requis manquants",
                "z_score": 0.0
            }

        val_rounded = round(value, 1)
        z_score = abs(val_rounded - mean) / dev if dev > 0 else 0.0

        status = "Normal"
        interp = norm_msg

        if val_rounded > max_val:
            if comp_range and val_rounded <= comp_range[1]:
                status = "Compensated"
                interp = f"{inc_msg} (Compensé)"
            else:
                status = "High"
                interp = inc_msg
        elif val_rounded < min_val:
            if comp_range and val_rounded >= comp_range[0]:
                status = "Compensated"
                interp = f"{dec_msg} (Compensé)"
            else:
                status = "Low"
                interp = dec_msg

        return {
            "valeur": val_rounded,
            "norm_mean": float(mean),
            "norm_min": float(min_val),
            "norm_max": float(max_val),
            "plage_compensation": comp_range,
            "status": status,
            "interpretation": interp,
            "z_score": round(z_score, 2)
        }

    # --- LOGIQUE MÉTIER V4 : DDM RÉELLE ---

    def calculate_ddm_reelle(self, ddm_clinique: float, impa_patient: float) -> float:
        """
        Calcule la DDM Réelle avec la règle empirique : 2.5° = 1mm
        DDM Céphalo = (IMPA - 90) / 2.5
        DDM Réelle = DDM Clinique + DDM Céphalo
        """
        # Écart d'inclinaison par rapport à la norme (90°)
        ecart_impa = impa_patient - 90.0

        # DDM Céphalométrique : 2.5° = 1mm
        ddm_cephalo = ecart_impa / 2.5

        # DDM Réelle = DDM Clinique + DDM Céphalo
        return round(ddm_clinique + ddm_cephalo, 2)

    # --- MORPHING T1 (CROISSANCE) ---

    def _project_t1_growth(self, pts: Dict[str, Optional[Tuple[float, float]]], ratio: Optional[float], age: Optional[int]) -> Dict[str, Tuple[float, float]]:
        """Calcule le ghosting de croissance (Points T1) pour le Frontend."""
        if ratio is None or not age or age >= 18 or ratio == 0:
            return {k: p for k, p in pts.items() if p}

        faces_right = pts.get("N") and pts.get("Po") and pts["N"][0] > pts["Po"][0]
        sign_x = 1 if faces_right else -1

        # Vecteurs annuels (mm) moyens selon Ricketts/Tweed
        growth = {
            "A": (0.5 * sign_x, 1.0),
            "B": (1.5 * sign_x, 2.0),
            "Me": (1.5 * sign_x, 2.0),
            "Go": (-1.0 * sign_x, 1.5)
        }

        t1 = {}
        for k, p in pts.items():
            if not p:
                continue

            if k in growth:
                t1[k] = (round(p[0] + (growth[k][0]/ratio), 1), round(p[1] + (growth[k][1]/ratio), 1))
            else:
                # Logique de suivi anatomique des tissus et dents
                if "U1" in k:
                    base = "A"
                    t1[k] = (round(p[0] + (growth[base][0]/ratio), 1), round(p[1] + (growth[base][1]/ratio), 1))
                elif "L1" in k:
                    base = "B"
                    t1[k] = (round(p[0] + (growth[base][0]/ratio), 1), round(p[1] + (growth[base][1]/ratio), 1))
                elif k in ["Ls", "Ls_soft", "ul", "UL", "St", "st", "Sn_soft", "Sn", "sn", "A_soft", "a_soft"]:
                    base = "A"
                    t1[k] = (round(p[0] + (growth[base][0]/ratio), 1), round(p[1] + (growth[base][1]/ratio), 1))
                elif k in ["Li", "Li_soft", "ll", "LL", "B_soft", "b_soft", "Pog_soft", "pog_soft", "Me_soft", "me_soft", "stpog", "stPog"]:
                    base = "Me"
                    t1[k] = (round(p[0] + (growth[base][0]/ratio), 1), round(p[1] + (growth[base][1]/ratio), 1))
                elif k in ["Prn", "prn", "Nose_Tip", "Cm", "cm"]:
                    # Le nez grandit vers l'avant et le bas
                    t1[k] = (round(p[0] + (0.8 * sign_x / ratio), 1), round(p[1] + (1.2 / ratio), 1))
                else:
                    t1[k] = p
        return t1

    def _project_t2_growth(self, pts: Dict[str, Optional[Tuple[float, float]]], ratio: Optional[float], age: Optional[int]) -> Dict[str, Tuple[float, float]]:
        """Calcule le ghosting de croissance à 5 ans (Points T2) avec limite de maturation à 18 ans."""
        if ratio is None or not age or age >= 18 or ratio == 0:
            return {k: p for k, p in pts.items() if p}

        faces_right = pts.get("N") and pts.get("Po") and pts["N"][0] > pts["Po"][0]
        sign_x = 1 if faces_right else -1

        # Vecteurs annuels (mm) moyens selon Ricketts/Tweed
        growth = {
            "A": (0.5 * sign_x, 1.0),
            "B": (1.5 * sign_x, 2.0),
            "Me": (1.5 * sign_x, 2.0),
            "Go": (-1.0 * sign_x, 1.5)
        }

        # Calcul du multiplicateur de croissance (maximum 5 ans, limité à 18 ans)
        years_remaining = min(18 - age, 5)

        t2 = {}
        for k, p in pts.items():
            if not p:
                continue

            if k in growth:
                t2[k] = (round(p[0] + (growth[k][0] * years_remaining / ratio), 1), round(p[1] + (growth[k][1] * years_remaining / ratio), 1))
            else:
                # Logique de suivi anatomique des tissus et dents
                if "U1" in k:
                    base = "A"
                    t2[k] = (round(p[0] + (growth[base][0] * years_remaining / ratio), 1), round(p[1] + (growth[base][1] * years_remaining / ratio), 1))
                elif "L1" in k:
                    base = "B"
                    t2[k] = (round(p[0] + (growth[base][0] * years_remaining / ratio), 1), round(p[1] + (growth[base][1] * years_remaining / ratio), 1))
                elif k in ["Ls", "Ls_soft", "ul", "UL", "St", "st", "Sn_soft", "Sn", "sn", "A_soft", "a_soft"]:
                    base = "A"
                    t2[k] = (round(p[0] + (growth[base][0] * years_remaining / ratio), 1), round(p[1] + (growth[base][1] * years_remaining / ratio), 1))
                elif k in ["Li", "Li_soft", "ll", "LL", "B_soft", "b_soft", "Pog_soft", "pog_soft", "Me_soft", "me_soft", "stpog", "stPog"]:
                    base = "Me"
                    t2[k] = (round(p[0] + (growth[base][0] * years_remaining / ratio), 1), round(p[1] + (growth[base][1] * years_remaining / ratio), 1))
                elif k in ["Prn", "prn", "Nose_Tip", "Cm", "cm"]:
                    # Le nez grandit vers l'avant et le bas
                    t2[k] = (round(p[0] + (0.8 * sign_x * years_remaining / ratio), 1), round(p[1] + (1.2 * years_remaining / ratio), 1))
                else:
                    t2[k] = p
        return t2

    # --- ORCHESTRATEUR PRINCIPAL ---
    def calculate_metrics(self,
                          raw_points: Dict,
                          custom_mm_ratio: Optional[float] = None,
                          age: Optional[int] = None,
                          cvm_stage: Optional[str] = None,
                          mcnamara_projections: Optional[Dict] = None) -> schemas.CephaloAnalysisResult:
        """
        Orchestre les 4 flux :
        1. Calcul des métriques géométriques COM.
        2. Projection morphologique (T1).
        3. Diagnostic narratif DÉTERMINISTE (Normes COM).
        4. Initialisation du conteneur Bilan V4 (DDM & Plan).
        """
        pts = {key: self._get_point(raw_points, key) for key in self.key_mapping.keys()}

        ratio = custom_mm_ratio if custom_mm_ratio is not None else self.mm_per_pixel
        has_calibration = ratio is not None
        is_child = age is not None and age <= 12

        payload = {
            "analysis_metadata": {
                "unit": "mm",
                "pixel_ratio": ratio,
                "type": "COM_Skeletal",
                "cohort": "Enfant (9 ans)" if is_child else "Adulte"
            },
            "metrics": {
                "analyse_dentaire": {},
                "analyse_osseuse": {},
                "analyse_esthetique": {},
                "wits_mcnamara": {}
            },
            "visual_debug": {"N_prime": None, "A_prime": None, "B_prime": None},
            "t1_projection": {},
            "t2_projection": {},
            "ai_narrative": {},
            "clinical_data": {
                "ddm_maxillaire": None,
                "ddm_mandibulaire": None,
                "ddm_reelle": None,
                "plan_traitement": ""
            }
        }

        # --- FLUX 1 : CALCULS GÉOMÉTRIQUES COM ---

        # 1.A. RÉFÉRENTIEL VECTORIEL
        uFH, uPerp = None, None
        if pts["Po"] and pts["Or"]:
            vFH = (pts["Or"][0] - pts["Po"][0], pts["Or"][1] - pts["Po"][1])
            mag = math.hypot(vFH[0], vFH[1])
            if mag > 0:
                uFH = (vFH[0]/mag, vFH[1]/mag)
                uPerp = (-uFH[1], uFH[0])
                # SVG/image coordinates grow downward. Keep the perpendicular
                # consistently oriented toward the bottom of the image.
                if uPerp[1] < 0:
                    uPerp = (-uPerp[0], -uPerp[1])

        # 1.B. ANALYSE DENTAIRE
        if has_calibration and uFH and uPerp and pts["U1i"] and pts["L1i"]:
            v_incisif = (pts["U1i"][0] - pts["L1i"][0], pts["U1i"][1] - pts["L1i"][1])
            surplomb = (v_incisif[0]*uFH[0] + v_incisif[1]*uFH[1]) * ratio
            recouvrement = (v_incisif[0]*uPerp[0] + v_incisif[1]*uPerp[1]) * ratio

            payload["metrics"]["analyse_dentaire"]["Surplomb"] = self._evaluate_metric(
                surplomb, 2.25, 0.75, "Surplomb augmenté", "Surplomb diminué", "Surplomb normal"
            )
            payload["metrics"]["analyse_dentaire"]["Recouvrement"] = self._evaluate_metric(
                recouvrement, 2.25, 0.75, "Recouvrement augmenté (Deep bite)", "Recouvrement diminué (Open bite)", "Recouvrement normal"
            )

        # --- MODIFICATION: Application explicite de 180 - angle brut ---
        impa_raw = self._get_clinical_angle(pts["L1a"], pts["L1i"], pts["Go"], pts["Me"], invert=False)
        impa = round(180 - impa_raw, 1) if impa_raw is not None else None
        payload["metrics"]["analyse_dentaire"]["IMPA"] = self._evaluate_metric(
            impa, 90.0, 5.0, "Incisive inférieure vestibulo-versée", "Incisive inférieure linguo-versée", "Inclinaison normale", comp_range=(80.0, 100.0)
        )

        if_raw = self._get_clinical_angle(pts["U1a"], pts["U1i"], pts["Po"], pts["Or"], invert=False)
        i_francfort = round(180 - if_raw, 1) if if_raw is not None else None
        payload["metrics"]["analyse_dentaire"]["I_Francfort"] = self._evaluate_metric(
            i_francfort, 107.0, 5.0, "Incisive supérieure vestibulo-versée", "Incisive supérieure palato-versée", "Inclinaison normale", comp_range=(97.0, 120.0)
        )

        inter_incisif_raw = self._get_clinical_angle(pts["U1a"], pts["U1i"], pts["L1a"], pts["L1i"], invert=False)
        inter_incisif = round(max(inter_incisif_raw, 180 - inter_incisif_raw), 1) if inter_incisif_raw is not None else None
        payload["metrics"]["analyse_dentaire"]["Inter_Incisif"] = self._evaluate_metric(
            inter_incisif, 131.0, 10.0, "Angle inter-incisif ouvert", "Angle inter-incisif fermé", "Relation inter-incisive normale", comp_range=(120.0, 142.0)
        )
        # ---------------------------------------------------------------

        # --- FLUX 1.D : ANALYSE DE STEINER & TISSUS MOUS ---
        if pts["S"] and pts["N"]:
            if pts["A"]:
                sna = self._get_clinical_angle(pts["N"], pts["S"], pts["N"], pts["A"])
                payload["metrics"]["analyse_osseuse"]["SNA"] = self._evaluate_metric(
                    sna, 82.0, 2.0, "Prognathie maxillaire (SNA)", "Rétrognathie maxillaire (SNA)", "Normal"
                )
            if pts["B"]:
                snb = self._get_clinical_angle(pts["N"], pts["S"], pts["N"], pts["B"])
                payload["metrics"]["analyse_osseuse"]["SNB"] = self._evaluate_metric(
                    snb, 80.0, 2.0, "Prognathie mandibulaire (SNB)", "Rétrognathie mandibulaire (SNB)", "Normal"
                )
            if pts["A"] and pts["B"]:
                anb = sna - snb if (sna and snb) else None
                payload["metrics"]["analyse_osseuse"]["ANB"] = self._evaluate_metric(
                    anb, 2.0, 2.0, "Classe II squelettique (Steiner)", "Classe III squelettique (Steiner)", "Classe I squelettique"
                )

        # Angle Nasolabial (Prn-Sn-Ls)
        prn = pts.get("Prn")
        sn_soft = pts.get("Sn_soft") or pts.get("Sn")
        ls_soft = pts.get("Ls_soft") or pts.get("Ls")
        if prn and sn_soft and ls_soft:
            # Angle entre segment Sn-Prn et Sn-Ls
            nla = self._get_clinical_angle(sn_soft, prn, sn_soft, ls_soft, invert=True)
            payload["metrics"]["analyse_esthetique"]["Angle_Nasolabial"] = self._evaluate_metric(
                nla, 102.0, 10.0, "Angle ouvert (Nez relevé)", "Angle fermé (Nez tombant)", "Harmonie nasolabiale"
            )

        # 1.C. ANALYSE OSSEUSE

        # 1.C. ANALYSE OSSEUSE
        fma = self._get_clinical_angle(pts["Go"], pts["Me"], pts["Po"], pts["Or"], invert=False)
        payload["metrics"]["analyse_osseuse"]["Angle_de_Tweed"] = self._evaluate_metric(
            fma, 26.0, 4.0, "Hyperdivergent (Face longue)", "Hypodivergent (Face courte)", "Normodivergent"
        )

        sit_a, sit_b, dec_ab, prof_faciale = None, None, None, None
        if has_calibration and uFH and pts["N"]:
            if pts["A"]: sit_a = ((pts["A"][0] - pts["N"][0])*uFH[0] + (pts["A"][1] - pts["N"][1])*uFH[1]) * ratio
            if pts["B"]: sit_b = ((pts["B"][0] - pts["N"][0])*uFH[0] + (pts["B"][1] - pts["N"][1])*uFH[1]) * ratio
            if pts["S"]: prof_faciale = abs(((pts["S"][0] - pts["N"][0])*uFH[0] + (pts["S"][1] - pts["N"][1])*uFH[1])) * ratio
            if sit_a is not None and sit_b is not None: dec_ab = sit_a - sit_b

        norm_dec_ab = (4.2, 3.2) if is_child else (2.3, 3.1)
        norm_sit_a = (2.8, 3.3) if is_child else (2.3, 3.0)
        norm_sit_b = (-1.5, 4.5) if is_child else (0.0, 4.9)
        norm_prof_fac = (61.3, 5.0) if is_child else (70.3, 5.0)

        payload["metrics"]["analyse_osseuse"]["Decalage_A_B"] = self._evaluate_metric(
            dec_ab, norm_dec_ab[0], norm_dec_ab[1], "Décalage Classe II", "Décalage Classe III", "Décalage Classe I"
        )
        payload["metrics"]["analyse_osseuse"]["Situation_A"] = self._evaluate_metric(
            sit_a, norm_sit_a[0], norm_sit_a[1], "Maxillaire en avant", "Maxillaire en retrait", "Position maxillaire normale"
        )
        payload["metrics"]["analyse_osseuse"]["Situation_B"] = self._evaluate_metric(
            sit_b, norm_sit_b[0], norm_sit_b[1], "Mandibule en avant", "Mandibule en retrait", "Position mandibulaire normale"
        )
        payload["metrics"]["analyse_osseuse"]["Profondeur_Faciale"] = self._evaluate_metric(
            prof_faciale, norm_prof_fac[0], norm_prof_fac[1], "Profondeur augmentée", "Profondeur diminuée", "Profondeur normale"
        )

        # --- FLUX 4 : ANALYSE MCNAMARA (CENTRALISÉE) ---
        # 1. Calcul des Projections Automatiques
        if has_calibration and uFH and uPerp:
            if pts["N"]:
                n_prime = self._get_orthogonal_projection(pts["Po"], pts["Or"], pts["N"])
                payload["visual_debug"]["N_prime"] = [round(n_prime[0], 2), round(n_prime[1], 2)]

            if pts["A"]:
                a_prime = self._get_orthogonal_projection(pts["Po"], pts["Or"], pts["A"])
                payload["visual_debug"]["A_prime"] = [round(a_prime[0], 2), round(a_prime[1], 2)]

            if pts["B"]:
                b_prime = self._get_orthogonal_projection(pts["Po"], pts["Or"], pts["B"])
                payload["visual_debug"]["B_prime"] = [round(b_prime[0], 2), round(b_prime[1], 2)]

            # 2. Calcul des Distances (Priorité Backend, Fallback Frontend pour compatibilité)
            np = payload["visual_debug"].get("N_prime") or (mcnamara_projections.get("N_prime") if mcnamara_projections else None)
            ap = payload["visual_debug"].get("A_prime") or (mcnamara_projections.get("A_prime") if mcnamara_projections else None)
            bp = payload["visual_debug"].get("B_prime") or (mcnamara_projections.get("B_prime") if mcnamara_projections else None)

            if np and ap:
                # Distance N'A' (algébrique sur FH)
                v_na = (ap[0] - np[0], ap[1] - np[1])
                dist_na_mm = (v_na[0]*uFH[0] + v_na[1]*uFH[1]) * ratio
                payload["metrics"]["analyse_osseuse"]["Situation_A"] = self._evaluate_metric(
                    dist_na_mm, norm_sit_a[0], norm_sit_a[1], "Prognathie maxillaire", "Rétrognathie maxillaire", "Normoposition"
                )

            if np and bp:
                # Distance N'B' (algébrique sur FH)
                v_nb = (bp[0] - np[0], bp[1] - np[1])
                dist_nb_mm = (v_nb[0]*uFH[0] + v_nb[1]*uFH[1]) * ratio
                payload["metrics"]["analyse_osseuse"]["Situation_B"] = self._evaluate_metric(
                    dist_nb_mm, norm_sit_b[0], norm_sit_b[1], "Prognathie mandibulaire", "Rétrognathie mandibulaire", "Normoposition"
                )

            if ap and bp:
                # Décalage A-B (positif = Classe II, négatif = Classe III)
                v_ab = (ap[0] - bp[0], ap[1] - bp[1])
                dist_ab_mm = (v_ab[0]*uFH[0] + v_ab[1]*uFH[1]) * ratio
                payload["metrics"]["analyse_osseuse"]["Decalage_A_B"] = self._evaluate_metric(
                    dist_ab_mm, norm_dec_ab[0], norm_dec_ab[1], "Classe II squelettique", "Classe III squelettique", "Classe I squelettique"
                )

        # --- NOUVEAU: WITS APPRAISAL ---
        if has_calibration and pts["Occ_Ant"] and pts["Occ_Post"] and pts["A"] and pts["B"]:
            # Vecteur du plan d'occlusion (de Postérieur vers Antérieur)
            v_occ = (pts["Occ_Ant"][0] - pts["Occ_Post"][0], pts["Occ_Ant"][1] - pts["Occ_Post"][1])
            mag_occ = math.hypot(v_occ[0], v_occ[1])
            if mag_occ > 0:
                u_occ = (v_occ[0]/mag_occ, v_occ[1]/mag_occ)
                # Projection algébrique de A sur l'axe du plan d'occlusion
                proj_a = (pts["A"][0] - pts["Occ_Post"][0])*u_occ[0] + (pts["A"][1] - pts["Occ_Post"][1])*u_occ[1]
                # Projection algébrique de B sur l'axe du plan d'occlusion
                proj_b = (pts["B"][0] - pts["Occ_Post"][0])*u_occ[0] + (pts["B"][1] - pts["Occ_Post"][1])*u_occ[1]

                # Distance Wits: AO - BO (Positif = Classe II, Négatif = Classe III)
                # On multiplie par ratio pour avoir des millimètres
                wits_mm = (proj_a - proj_b) * ratio

                payload["metrics"]["wits_mcnamara"]["Wits_Appraisal"] = self._evaluate_metric(
                    wits_mm, 0.0, 1.5, "Classe II Squelettique Vraie", "Classe III Squelettique Vraie", "Classe I Squelettique"
                )

        # --- NOUVEAU: MCNAMARA VRAI (Longueurs Effectives) ---
        if has_calibration and pts["Co"] and pts["A"] and pts["Gn"]:
            # Longueur effective maxillaire (Co-A)
            len_max = math.hypot(pts["A"][0] - pts["Co"][0], pts["A"][1] - pts["Co"][1]) * ratio
            # Longueur effective mandibulaire (Co-Gn)
            len_mand = math.hypot(pts["Gn"][0] - pts["Co"][0], pts["Gn"][1] - pts["Co"][1]) * ratio

            diff_max_mand = len_mand - len_max
            # Norme différentielle selon l'âge : autour de 20-30 mm
            norm_diff = 20.0 if is_child else 27.0

            payload["metrics"]["wits_mcnamara"]["Longueur_Maxillaire"] = {
                "valeur": round(len_max, 1),
                "interpretation": "Longueur Effective Maxillaire (Co-A)",
                "status": "Normal"
            }
            payload["metrics"]["wits_mcnamara"]["Longueur_Mandibulaire"] = {
                "valeur": round(len_mand, 1),
                "interpretation": "Longueur Effective Mandibulaire (Co-Gn)",
                "status": "Normal"
            }
            payload["metrics"]["wits_mcnamara"]["Differentiel_Maxillo_Mandibulaire"] = self._evaluate_metric(
                diff_max_mand, norm_diff, 4.0, "Excès mandibulaire relatif (Classe III)", "Déficit mandibulaire relatif (Classe II)", "Équilibre Maxillo-Mandibulaire"
            )

        if has_calibration and pts["ANS"] and pts["Me"]:
            # Étage inférieur (ENA-Me)
            lafh = math.hypot(pts["Me"][0] - pts["ANS"][0], pts["Me"][1] - pts["ANS"][1]) * ratio
            norm_lafh = 60.0 if is_child else 68.0
            payload["metrics"]["wits_mcnamara"]["Etage_Inferieur_Face"] = self._evaluate_metric(
                lafh, norm_lafh, 4.0, "Étage inférieur augmenté (Hyperdivergence)", "Étage inférieur diminué (Hypodivergence)", "Étage inférieur normal"
            )
        prn = pts.get('Prn')
        pog_s = pts.get('Pog_soft')
        ls = pts.get('Ls')
        li = pts.get('Li')

        if has_calibration and prn and pog_s and pts["Po"] and pts["Or"]:
            if ls:
                d_ls = self._signed_e_line_distance(ls, prn, pog_s, pts["Po"], pts["Or"], ratio)
                if d_ls is not None:
                    payload["metrics"]["analyse_esthetique"]["Ligne_E_Ls"] = self._evaluate_metric(
                        d_ls, -4.0, 2.0, "Lèvre supérieure en avant", "Lèvre supérieure en retrait", "Équilibre labial supérieur"
                    )
            if li:
                d_li = self._signed_e_line_distance(li, prn, pog_s, pts["Po"], pts["Or"], ratio)
                if d_li is not None:
                    payload["metrics"]["analyse_esthetique"]["Ligne_E_Li"] = self._evaluate_metric(
                        d_li, -2.0, 2.0, "Lèvre inférieure en avant", "Lèvre inférieure en retrait", "Équilibre labial inférieur"
                    )
        # The E-line is unavailable when its geometry or anatomical axis is incomplete.

        # --- FLUX 3 : PROJECTION MORPHOLOGIQUE T1 & T2 ---
        payload["t1_projection"] = self._project_t1_growth(pts, ratio, age)
        payload["t2_projection"] = self._project_t2_growth(pts, ratio, age)

        # --- FLUX 3 : INTELLIGENCE CLINIQUE DÉTERMINISTE (Normes COM) ---

        # Une mesure absente ne doit jamais etre remplacee par une norme clinique.
        # Les normes restent des references de comparaison, pas des observations patient.
        def metric_value(group, name):
            return payload["metrics"][group].get(name, {}).get("valeur")

        val_tweed = metric_value("analyse_osseuse", "Angle_de_Tweed")
        val_dec_ab = metric_value("analyse_osseuse", "Decalage_A_B")
        val_anb = metric_value("analyse_osseuse", "ANB")
        val_sit_a = metric_value("analyse_osseuse", "Situation_A")
        val_sit_b = metric_value("analyse_osseuse", "Situation_B")
        val_impa = metric_value("analyse_dentaire", "IMPA")
        val_if = metric_value("analyse_dentaire", "I_Francfort")
        val_inter = metric_value("analyse_dentaire", "Inter_Incisif")
        val_surplomb = metric_value("analyse_dentaire", "Surplomb")
        val_recouvrement = metric_value("analyse_dentaire", "Recouvrement")

        # Extraction Esthétique — None si la mesure n'a pas pu être faite (points cutanés
        # absents) : la narration doit dire "non évaluable", jamais coalescer vers une
        # valeur par défaut présentée comme mesurée (0.0 / 102°).
        val_e_ls = payload["metrics"].get("analyse_esthetique", {}).get("Ligne_E_Ls", {}).get("valeur")
        val_nla = payload["metrics"].get("analyse_esthetique", {}).get("Angle_Nasolabial", {}).get("valeur")

        # --- LOGIQUE DE CONSENSUS SQUELETTIQUE (CERVEAU SCIENTIFIQUE) ---
        mean_ab, dev_ab = norm_dec_ab
        max_ab = mean_ab + dev_ab
        min_ab = mean_ab - dev_ab

        class_steiner = None
        if val_anb is not None:
            class_steiner = "II" if val_anb > 4.5 else "III" if val_anb < 0 else "I"
        class_mcnamara = None
        if val_dec_ab is not None:
            class_mcnamara = "II" if val_dec_ab > max_ab else "III" if val_dec_ab < min_ab else "I"
        skeletal_class = class_steiner or class_mcnamara

        skeletal_parts = []
        if class_steiner is not None and class_mcnamara is not None:
            if class_steiner == class_mcnamara:
                skeletal_parts.append(f"Structure de Classe {class_steiner} (ANB: {val_anb}°, A'B': {val_dec_ab} mm).")
            else:
                skeletal_parts.append(f"Discordance angulaire/linéaire: Classe {class_steiner} selon ANB ({val_anb}°), Classe {class_mcnamara} selon A'B' ({val_dec_ab} mm).")
        elif class_steiner is not None:
            skeletal_parts.append(f"Tendance squelettique de Classe {class_steiner} selon ANB ({val_anb}°).")
        elif class_mcnamara is not None:
            skeletal_parts.append(f"Tendance squelettique de Classe {class_mcnamara} selon A'B' ({val_dec_ab} mm).")

        div = None
        if val_tweed is not None:
            div = "hyperdivergent" if val_tweed > 30 else "hypodivergent" if val_tweed < 22 else "normodivergent"
            skeletal_parts.append(f"Typologie faciale: {div.capitalize()} (Angle de Tweed: {val_tweed}°).")

        val_sna = metric_value("analyse_osseuse", "SNA")
        val_snb = metric_value("analyse_osseuse", "SNB")
        if val_sit_a is not None:
            if val_sit_a > norm_sit_a[0] + norm_sit_a[1]:
                skeletal_parts.append("Prognathie maxillaire.")
            elif val_sit_a < norm_sit_a[0] - norm_sit_a[1]:
                skeletal_parts.append("Retrognathie maxillaire." if val_sna is not None and val_sna < 80.0 else "Situation A hors norme (a confirmer cliniquement).")
        if val_sit_b is not None:
            if val_sit_b > norm_sit_b[0] + norm_sit_b[1]:
                skeletal_parts.append("Prognathie mandibulaire.")
            elif val_sit_b < norm_sit_b[0] - norm_sit_b[1]:
                skeletal_parts.append("Retrognathie mandibulaire." if val_snb is not None and val_snb < 78.0 else "Situation B hors norme (a confirmer cliniquement).")
        diag_squelettique = " ".join(skeletal_parts) or "Analyse squelettique non evaluable: mesures requises absentes."

        dental_parts = []
        impa_diag = None
        if val_impa is not None:
            impa_diag = "proalveolie mandibulaire" if val_impa > 95 else "retroalveolie mandibulaire" if val_impa < 85 else "normoalveolie"
            dental_parts.append(f"IMPA: {impa_diag} ({val_impa}°).")
        if_diag = None
        if val_if is not None:
            if_diag = "proalveolie maxillaire" if val_if > 112 else "retroalveolie maxillaire" if val_if < 102 else "normoalveolie"
            dental_parts.append(f"I/F: {if_diag} ({val_if}°).")
        if val_inter is not None:
            dental_parts.append(f"Angle inter-incisif a {val_inter}°.")
        overjet = None
        if val_surplomb is not None:
            overjet = "augmente" if val_surplomb > 3 else "diminue" if val_surplomb < 1.5 else "normal"
            dental_parts.append(f"Surplomb {overjet} ({val_surplomb} mm).")
        overbite = None
        if val_recouvrement is not None:
            overbite = "supraclusion" if val_recouvrement > 3 else "infraclusion" if val_recouvrement < 1.5 else "normal"
            dental_parts.append(f"Recouvrement {overbite} ({val_recouvrement} mm).")
        diag_dentaire = " ".join(dental_parts) or "Analyse dentaire non evaluable: mesures requises absentes."

        # 3. DIAGNOSTIC ESTHÉTIQUE — chaque segment n'est affirmé que si la mesure existe.
        if val_e_ls is None:
            profil_cutane = None
            segment_profil = "Profil cutané non évaluable (points cutanés non détectés)"
        else:
            profil_cutane = "droit"
            if val_e_ls > 2.0: profil_cutane = "convexe (Lèvre supérieure protrusive)"
            elif val_e_ls < -4.0: profil_cutane = "concave (Lèvre supérieure en retrait)"
            segment_profil = f"Profil {profil_cutane} selon la ligne E de Ricketts"

        if val_nla is None:
            segment_nla = "Angle nasolabial non évaluable (points cutanés non détectés)"
        else:
            nla_diag = "normal"
            if val_nla > 110: nla_diag = "ouvert (Nez relevé)"
            elif val_nla < 90: nla_diag = "fermé (Nez tombant)"
            segment_nla = f"Angle nasolabial {nla_diag} ({val_nla}°)"

        diag_esthetique = f"{segment_profil}. {segment_nla}."

        # --- SYNTHÈSE GHOST ELITE (4 SECTIONS) ---

        # Section 1: Analyse Céphalométrique COM (Squelettique + Dentaire + Esthétique)
        analyse_cephalo_com = f"ANALYSE SQUELETTIQUE : {diag_squelettique}\n\nANALYSE DENTAIRE : {diag_dentaire}\n\nANALYSE ESTHÉTIQUE : {diag_esthetique}"

        # Section 2: Analyse des Moulages (Initialisation - sera complétée par le clinicien)
        analyse_moulages = "Occlusion à préciser (Classe d'Angle, Subdivision, Forme d'arcade)."

        # Section 3: Synthèse Diagnostique (Résumé des anomalies)
        anomalies = []
        if skeletal_class is not None and skeletal_class != "I": anomalies.append(f"Classe {skeletal_class}")
        if div is not None and div != "normodivergent": anomalies.append(div)
        if impa_diag is not None and impa_diag != "normoalveolie": anomalies.append(impa_diag)
        if if_diag is not None and if_diag != "normoalveolie": anomalies.append(if_diag)
        if overjet is not None and overjet != "normal": anomalies.append(f"Surplomb {overjet}")
        if overbite is not None and overbite != "normal": anomalies.append(overbite)

        synthese = f"Anomalies detectees: {', '.join(anomalies)}." if anomalies else "Aucune anomalie ne peut etre conclue avec les mesures disponibles."

        # Section 4: Plan de Traitement (Stratégie Thérapeutique Elite)
        is_child = age is not None and age <= 12
        strategie_parts = []

        # 4.1. Approche Fondamentale
        if is_child:
            strategie_parts.append("PHASE 1 : ORTHOPÉDIE DENTO-FACIALE (ODF) interceptive.")
        else:
            strategie_parts.append("PHASE GLOBALE : Orthodontie fixe ou aligneurs.")

        # 4.2. Choix Technologique — différé si patient en croissance (denture mixte)
        if not is_child:
            if (val_surplomb is not None and val_surplomb > 5) or (val_impa is not None and val_impa > 100):
                strategie_parts.append("MÉTHODE : Méthode Classique / Damon Active si rétraction incisive nécessaire.")
            elif val_surplomb is not None or val_impa is not None:
                strategie_parts.append("MÉTHODE : Système Damon Passif (Gold Standard). Forces légères, auto-ligaturant sans friction pour expansion alvéolaire (Bone Adaptation).")
            else:
                strategie_parts.append("MÉTHODE : À déterminer après acquisition des mesures incisives.")
            strategie_parts.append("OPTION ALTERNATIVE : Aligneurs transparents (Invisalign) avec planification ClinCheck.")
        else:
            strategie_parts.append("ORIENTATION : Réévaluation à la denture permanente avant toute prescription d'appareillage fixe multi-attaches. Surveillance de croissance et intervention interceptive si indiquée.")

        # 4.3. Spécificités Squelettiques
        if skeletal_class == "II":
            if is_child: strategie_parts.append("Classe II : Propulsion mandibulaire par Invisalign MA ou Twin Block.")
            else: strategie_parts.append("Classe II : Camouflage avec élastiques de Classe II ou recul maxillaire (Mini-vis/TADs).")
        elif skeletal_class == "III":
            if is_child: strategie_parts.append("Classe III : Masque de Delaire (Traction extra-orale) + ERM précoce.")
            else: strategie_parts.append("Classe III : Traitement chirurgico-orthodontique si sévère (Ostéotomie) ou compensation dentaire.")

        if div == "hyperdivergent":
            strategie_parts.append("Vertical : Profil hyperdivergent. Contrôle vertical très strict requis (éviter toute extrusion postérieure, caller les secteurs postérieurs, Invisalign recommandé pour l'effet bite-block).")
        elif div == "hypodivergent":
            strategie_parts.append("Vertical : Profil hypodivergent. Autorisation de nivellement de la courbe de Spee par extrusion postérieure.")

        strategie = "\n".join(strategie_parts)

        # Expose the Ricketts-based profil as a separate field so the frontend can use it
        # instead of overriding with the ANB-based formula. Omis quand la Ligne E n'a pas
        # été mesurée : le frontend (useOrthoStore, `if (n.profil_cutane)`) skippe alors
        # proprement — un texte "non évaluable" casserait normalizeProfilFacial.
        payload["ai_narrative"] = {
            "diagnostic_squelettique": analyse_cephalo_com,
            "analyse_moulages": analyse_moulages,
            "synthese_diagnostique": synthese,
            "strategie_therapeutique": strategie,
        }
        if not has_calibration:
            payload["ai_narrative"] = {
                "diagnostic_squelettique": (
                    "Analyse angulaire disponible; les mesures linéaires en millimètres "
                    "ne sont pas évaluables sans calibration vérifiée."
                ),
                "analyse_moulages": analyse_moulages,
                "synthese_diagnostique": synthese,
                "strategie_therapeutique": strategie,
            }
            return schemas.CephaloAnalysisResult.model_validate(payload)

        if val_e_ls is not None:
            profil_cutane_short = "droit"
            if val_e_ls > 2.0: profil_cutane_short = "convexe"
            elif val_e_ls < -4.0: profil_cutane_short = "concave"
            payload["ai_narrative"]["profil_cutane"] = profil_cutane_short

        return schemas.CephaloAnalysisResult.model_validate(payload)

# Instance singleton prête à l'emploi
cephalo_engine = CephaloEngine()
