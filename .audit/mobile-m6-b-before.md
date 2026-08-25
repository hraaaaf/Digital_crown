# M6-B — Scan de documents contextuel — BEFORE canonique

Date : 2026-08-25
État : BEFORE VERROUILLÉ — aucun changement produit M6-B.

## Chantier

M6-B — Scan de documents contextuel depuis le contexte Patient exact.

## Baseline produit exacte

- Master de référence : `0a577f05f55a772a1b3f6d2980b18ef4e1a643fb`.
- Les captures réutilisées proviennent du HEAD produit `24dcdc5543f68fd31b65a4facfa824f4a51cfbd8`, run AFTER M6-A `32864337475`, artifact `9569518739`, digest `sha256:69dd249809ba98246b84c298cd5cdffdc387d104ba1dee2e3fa81fde1b76fd1e`.
- Preuve d'équivalence : comparaison `24dcdc5543f68fd31b65a4facfa824f4a51cfbd8` → `0a577f05f55a772a1b3f6d2980b18ef4e1a643fb` = 2 commits, 0 behind, avec seulement :
  - `docs/MOBILE_FULL_EXPERIENCE_ROADMAP.md` ;
  - `docs/MOBILE_M6_A_CLINICAL_PHOTO_CLOSEOUT.md`.
- Aucun fichier frontend/backend produit n'a changé entre les captures et le master M6-B.

## Captures BEFORE réutilisées

Les captures `action` représentent l'état Patient courant avant toute implémentation M6-B :

- `patient-action-390x844.png`
- `patient-action-430x932.png`
- `patient-action-768x1024.png`

Rapport machine du run source :

- 390×844 : 0 overflow, 0 erreur runtime ;
- 430×932 : 0 overflow, 0 erreur runtime ;
- 768×1024 : 0 overflow, 0 erreur runtime.

## Défaut fonctionnel observé

Le contexte Patient exact propose actuellement :

- Appeler ;
- Agenda ;
- Photo clinique.

Il ne propose aucune action `Scanner un document` / `Scan document` et aucun input dédié au scan multi-page.

Le backend `mobile_resource_bridge.py` expose actuellement `resource-context-photo` pour M6-A ainsi que les routes de lecture contextuelle, mais aucune route `resource-context-scan` / archivage de scan document n'existe.

## Vérité de stockage existante

- `PatientDocuments` lit les archives canoniques du patient via `/patients/{patient_id}/documents`.
- Le backend de cette route renvoie les `DocumentArchive` actifs / dernière version.
- M6-B doit donc réutiliser `DocumentArchive` au lieu d'introduire une deuxième bibliothèque de scans.

## Non-crédité à ce stade

- Aucun Goal UX M6-B encore figé.
- Aucun mockup M6-B encore figé.
- Aucun endpoint M6-B.
- Aucun composant M6-B.
- Aucun commit produit M6-B.

L'ordre obligatoire reste : BEFORE verrouillé → Goal écrit → référence visuelle → implémentation → AFTER 390/430/768 → tests/certification.
