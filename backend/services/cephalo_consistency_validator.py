"""
Validateur de cohérence céphalo — lecture seule, rejouable.

Vérifie trois catégories de problèmes avant de laisser générer un PDF :

  FATAL  → incohérence bloquante (valeur physiologiquement impossible ou
            contradiction interne grave). Le PDF est refusé.
  WARNING → valeur hors normes mais plausible, ou contradiction faible.
            Le PDF peut être généré mais le praticien est averti.
  OK     → rien à signaler.

Entrée : le dict `angles_data` stocké dans CephaloAnalysis.angles_data.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _val(obj: Any, *keys: str) -> Optional[float]:
    """Descend un dict imbriqué et retourne la valeur numérique ou None."""
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    if cur is None:
        return None
    # MeasureData sérialisé en dict → champ "valeur"
    if isinstance(cur, dict):
        cur = cur.get("valeur")
    try:
        return float(cur)
    except (TypeError, ValueError):
        return None


# ─── Résultat ─────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    fatals: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.fatals) == 0

    def to_dict(self) -> dict:
        return {
            "valid": self.is_valid,
            "fatals": self.fatals,
            "warnings": self.warnings,
        }


# ─── Validateur ───────────────────────────────────────────────────────────────

class CephaloConsistencyValidator:
    """
    Valide les mesures d'une CephaloAnalysis.
    Appeler .validate(angles_data) et vérifier result.is_valid avant le PDF.
    """

    # Bornes physiologiques absolues (au-delà = impossible anatomiquement)
    _HARD_BOUNDS: dict[str, tuple[float, float]] = {
        "SNA":           (60.0, 105.0),
        "SNB":           (58.0, 102.0),
        "ANB":           (-10.0, 15.0),
        "Inter_Incisif": (80.0, 180.0),
        "I_Francfort":   (60.0, 155.0),
        "IMPA":          (60.0, 125.0),
        "Angle_Nasolabial": (50.0, 160.0),
    }

    # Bornes cliniques normales (hors → warning)
    _SOFT_BOUNDS: dict[str, tuple[float, float]] = {
        "SNA":           (76.0, 88.0),
        "SNB":           (74.0, 86.0),
        "ANB":           (-2.0, 6.0),
        "Inter_Incisif": (110.0, 150.0),
        "I_Francfort":   (93.0, 120.0),
        "IMPA":          (80.0, 105.0),
        "Angle_Nasolabial": (85.0, 125.0),
    }

    def validate(self, angles_data: dict) -> ValidationResult:
        result = ValidationResult()
        if not isinstance(angles_data, dict):
            result.fatals.append("angles_data manquant ou format invalide.")
            return result

        metrics = angles_data.get("metrics", {})
        osseuse = metrics.get("analyse_osseuse", {})
        dentaire = metrics.get("analyse_dentaire", {})
        esthetique = metrics.get("analyse_esthetique", {})

        sna = _val(osseuse, "SNA", "valeur")
        snb = _val(osseuse, "SNB", "valeur")
        anb = _val(osseuse, "ANB", "valeur")
        inter = _val(dentaire, "Inter_Incisif", "valeur")
        i_franc = _val(dentaire, "I_Francfort", "valeur")
        impa = _val(dentaire, "IMPA", "valeur")
        nasolab = _val(esthetique, "Angle_Nasolabial", "valeur")

        named = {
            "SNA": sna, "SNB": snb, "ANB": anb,
            "Inter_Incisif": inter, "I_Francfort": i_franc,
            "IMPA": impa, "Angle_Nasolabial": nasolab,
        }

        # 1. Bornes physiologiques absolues
        for name, val in named.items():
            if val is None:
                continue
            lo, hi = self._HARD_BOUNDS[name]
            if not (lo <= val <= hi):
                result.fatals.append(
                    f"{name} = {val:.1f}° hors bornes physiologiques [{lo}°, {hi}°] — "
                    "valeur impossible, vérifier les landmarks."
                )

        # 2. Cohérence interne SNA - SNB ≈ ANB
        if sna is not None and snb is not None and anb is not None:
            expected_anb = round(sna - snb, 1)
            if abs(expected_anb - anb) > 1.5:
                result.fatals.append(
                    f"Incohérence interne : SNA({sna:.1f}°) - SNB({snb:.1f}°) = {expected_anb}° "
                    f"mais ANB = {anb:.1f}° (écart > 1.5°). Recalculer ou réviser les landmarks."
                )

        # 3. Contradiction classe squelettique vs ANB
        if sna is not None and snb is not None and anb is not None:
            # ANB > 4 → tendance Classe II ; ANB < 0 → tendance Classe III
            # SNA < SNB → profil inverse → cohérent avec Classe III
            if anb > 4.0 and sna < snb:
                result.fatals.append(
                    f"Contradiction : ANB = {anb:.1f}° (Classe II) mais SNA < SNB "
                    f"({sna:.1f}° < {snb:.1f}°) → impossible. Vérifier les landmarks S/N/A/B."
                )
            if anb < 0.0 and sna > snb + 5:
                result.warnings.append(
                    f"Incohérence mineure : ANB négatif ({anb:.1f}°) mais SNA largement > SNB "
                    f"({sna:.1f}° vs {snb:.1f}°). Confirmer landmarks A et B."
                )

        # 4. Inter-incisif vs I/Francfort : si I/F > 130° l'inter-incisif devrait être < 130°
        if i_franc is not None and inter is not None:
            if i_franc > 130.0 and inter > 140.0:
                result.warnings.append(
                    f"I/Francfort ({i_franc:.1f}°) et Inter-incisif ({inter:.1f}°) tous deux élevés "
                    "→ biprotrusion peu probable, vérifier les landmarks incisifs."
                )
            if i_franc < 80.0 and inter < 110.0:
                result.warnings.append(
                    f"I/Francfort ({i_franc:.1f}°) et Inter-incisif ({inter:.1f}°) tous deux faibles "
                    "→ rétro-inclination sévère des deux arcades, confirmer les landmarks."
                )

        # 5. Bornes normales (warnings seulement)
        for name, val in named.items():
            if val is None:
                continue
            lo, hi = self._SOFT_BOUNDS[name]
            hard_lo, hard_hi = self._HARD_BOUNDS[name]
            # N'émettre le warning que si la valeur est dans les bornes physio (sinon déjà fatal)
            if (lo <= val <= hi) or not (hard_lo <= val <= hard_hi):
                continue
            result.warnings.append(
                f"{name} = {val:.1f}° hors norme [{lo}°–{hi}°]."
            )

        return result


cephalo_consistency_validator = CephaloConsistencyValidator()
