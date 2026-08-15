from pathlib import Path

MERGE_SHA = "91a2c2efd781fd736ebdc96e9de4f5e3c73c82c8"
PR_HEAD = "9a00f07c4b1dc98776cf03bc17b27c23b50d7a81"
PRE_RUN = "31897932430"
PRE_ARTIFACT = "9250318673"
PRE_DIGEST = "sha256:81db7ba5b525413908bb3b9faa84a2d6fc6478da756a6367b22d590c88e511e0"
GLASS_RUN = "31898157179"
GLASS_ARTIFACT = "9250378182"
GLASS_DIGEST = "sha256:4809953baa1ed5dd49a7b143da694ae13e438394146a2d3c8809be90e39dd6de"
PR_CI = "31898122575"
MERGE_CI = "31898590067"

p = Path("ROADMAP_ORDONNANCE_P1.md")
text = p.read_text(encoding="utf-8")
for old, new in {
    "- [ ] hiérarchie visuelle glass premium restaurée sans perte de sécurité": "- [x] hiérarchie visuelle glass premium restaurée sans perte de sécurité",
    "- [ ] recapture comparative glass 1440/768/390 validée": "- [x] recapture comparative glass 1440/768/390 validée",
    "- [ ] CI exacte sur le head final de PR #43 verte": "- [x] CI exacte sur le head final de PR #43 verte",
    "- [ ] merge PR #43": "- [x] merge PR #43",
}.items():
    text = text.replace(old, new)
closeout = f"""

---

## 13. Closeout UX/engineering P1 — 2026-08-15

### Preuves finales
- PR `#43` mergée sur `master` : `{MERGE_SHA}`.
- Head fonctionnel final PR : `{PR_HEAD}`.
- CI exacte-head PR : run `{PR_CI}` — **SUCCESS**.
- Audit visuel historique pré-R1 : run `{PRE_RUN}` — **SUCCESS**, artifact `{PRE_ARTIFACT}`, digest `{PRE_DIGEST}`.
- Recertification glass finale 1440 / 768 / 390 : run `{GLASS_RUN}` — **SUCCESS**, artifact `{GLASS_ARTIFACT}`, digest `{GLASS_DIGEST}`.
- Inspection visuelle manuelle des trois captures : **propre**, sans débordement horizontal destructif ni action principale rognée.
- Le langage glassmorphique historique est conservé ; la hiérarchie contexte/sécurité a été regroupée en une surface glass principale sans suppression d'information de sécurité.
- CI push exacte du merge sur `master` : run `{MERGE_CI}` — **à vérifier avant fermeture complète**.

### Limites explicitement conservées
- L'interaction authentifiée dans l'application locale réelle du cabinet reste **non certifiée** par ces captures isolées.
- La certification clinique/pharmacologique humaine reste un gate séparé.
- Aucun statut `production ready` n'est déduit de cette certification visuelle/engineering.
"""
if "## 13. Closeout UX/engineering P1 — 2026-08-15" not in text:
    text = text.rstrip() + closeout + "\n"
p.write_text(text, encoding="utf-8")

p = Path("DOCUMENT_STUDIO_ROADMAP.md")
text = p.read_text(encoding="utf-8")
text = text.replace(
    "- [ ] **Recertification après refonte**",
    f"- [x] **Recertification visuelle après refonte** — PR #43 mergée `{MERGE_SHA}` ; captures 1440/768/390 inspectées ; CI PR `{PR_CI}` SUCCESS. Interaction authentifiée locale reste séparée.",
)
block = f"""
#### P1 — closeout runtime visuel / glass
- PR `#43` — **MERGED**.
- Head final PR : `{PR_HEAD}` ; CI exacte run `{PR_CI}` — **SUCCESS**.
- Merge `master` : `{MERGE_SHA}`.
- Baseline visuelle pré-R1 auditée via run `{PRE_RUN}` — SUCCESS.
- Recapture finale glass 1440 / 768 / 390 via run `{GLASS_RUN}` — **SUCCESS** ; artifact `{GLASS_ARTIFACT}` ; inspection visuelle propre.
- Le glassmorphisme historique n'a pas été supprimé ; le correctif final regroupe contexte, sécurité, actions et alerte forme dans une hiérarchie glass cohérente sans retirer les gardes de sécurité.
- **Non couvert par cette preuve :** interaction authentifiée dans l'application locale réelle et certification clinique/pharmacologique.
- CI push post-merge : run `{MERGE_CI}` — à vérifier avant fermeture documentaire complète.

"""
marker = "### P2 — Devis + Honoraires"
if "#### P1 — closeout runtime visuel / glass" not in text and marker in text:
    text = text.replace(marker, block + marker, 1)
p.write_text(text, encoding="utf-8")

p = Path("docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md")
text = p.read_text(encoding="utf-8")
appendix = f"""

---

## Addendum de recertification P1 — 2026-08-15

Cet addendum met à jour le statut de l'audit statique historique sans réécrire rétroactivement ses constats.

### État engineering / UX vérifié
- R1 → R7 sont fermés côté engineering selon leurs CI exact-head documentées.
- PR `#43` a corrigé les défauts responsive observés en runtime isolé et restauré la hiérarchie glass premium.
- Head final PR : `{PR_HEAD}` ; CI exacte `{PR_CI}` — **SUCCESS**.
- Merge sur `master` : `{MERGE_SHA}`.
- Comparaison historique pré-R1 : run `{PRE_RUN}` — SUCCESS, artifact `{PRE_ARTIFACT}`, digest `{PRE_DIGEST}`.
- Recertification finale glass : run `{GLASS_RUN}` — SUCCESS, artifact `{GLASS_ARTIFACT}`, digest `{GLASS_DIGEST}`.
- Vues inspectées : **1440 × 1100, 768 × 1100, 390 × 844**.
- Verdict visuel : aucune action principale rognée, aucun débordement horizontal destructif observé ; glassmorphisme conservé et hiérarchie contexte/sécurité regroupée.

### Constats historiques désormais corrigés côté engineering
Les sections plus haut décrivent la baseline auditée au moment de l'audit. Elles restent utiles comme historique, mais ne doivent plus être lues comme l'état courant pour : safety non branchée, dirty-state absent, fallback de forme implicite, UX rapide, protocoles/référentiel et preview responsive. Les preuves R1→R7 et PR #43 font foi pour l'état engineering actuel.

### Gates toujours ouverts
- **INTERACTION AUTHENTIFIÉE APPLICATION LOCALE : non certifiée.** Le harness rend les vrais composants mais n'est pas une session cabinet authentifiée.
- **CERTIFICATION CLINIQUE/PHARMACOLOGIQUE : non certifiée.** Revue qualifiée distincte requise.
- CI push exacte du merge `{MERGE_SHA}` : run `{MERGE_CI}` — à vérifier avant closeout documentaire final.
"""
if "## Addendum de recertification P1 — 2026-08-15" not in text:
    text = text.rstrip() + appendix + "\n"
p.write_text(text, encoding="utf-8")
