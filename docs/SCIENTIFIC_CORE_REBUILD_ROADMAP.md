# DIGITAL CROWN — SCIENTIFIC CORE REBUILD — CANONICAL HANDOVER

**Règle de reprise :** vérifier `repo / branche / PR / HEAD / CI` avant toute conclusion. Les runs historiques ne valent jamais état courant.

## GOAL FINAL

Noyau scientifique minimal, explicable, sourcé/versionné et fail-closed.

Invariant : `measurement != diagnosis != indication != treatment`.

Succès : aucune donnée patient inventée influente ; aucune interprétation ou décision clinique autonome non validée ; séparation observation/interprétation/décision praticien ; tests et CI verts avant merge ; aucun déploiement Vercel sans autorisation explicite.

## REPO

Repo : `hraaaaf/Digital_crown`  
Base : `master`

Aucun pourcentage global n'est déclaré sans recalcul vérifié.

## LOT 7 — CÉPHALOMÉTRIE / ORTHODONTIE

### État vérifié

- Frontend : aucune génération thérapeutique automatique ; aucune norme locale ; sexe patient nullable/reset `null` ; CVM âge/sexe et DDM par IMPA neutralisés.
- `CephaloService` utilise `cephalo_safe_engine`.
- `cephalo_engine.py` est géométrie seule : normes locales, z-scores, croissance T1/T2, diagnostic et traitement autonomes supprimés.
- `cephalo_consistency_validator.py` ne garde que cohérence structurelle, identité SNA-SNB=ANB, unités et calibration.
- `bilan_ortho_engine.py` restitue valeurs brutes + données praticien, sans classe/typologie/sévérité/diagnostic/traitement autonome.
- `backend/routers/ia.py` n'importe plus directement `cephalo_engine` ni `ai_advisor`.
- `backend/services/clinical_intelligence.py` ne dépend plus de `ai_advisor` ; son chemin céphalo historique restitue désormais les mesures brutes uniquement, sans cohorte âge-dérivée, diagnostic, indication ou stratégie automatique.
- Les motifs `ORTHODONTIE` de `clinical_intelligence` servent uniquement au routage de spécialité : ils n'alimentent aucun `motif_treatment_hints`.
- `backend/services/ai_advisor.py` est supprimé.

### Preuve finale avant merge

Sur le HEAD exact `6622260c2cd14f623499e9f4bee36d9cb60d3b06` :

- CI `34410144405` : **success** ; backend `Tests & durcissement`, frontend tests/build, garde production et M4-A/B/C verts.
- Patient Indicators `34410144139` : **success** après correction déterministe du harness.
- T2 `34410144336` : **success**.
- P7 `34410144189` : **success**.
- Catalog `34410144211` : **success**.
- Portability Runtime `34410144360` : **success**.
- Settings, Mobile et autres certifications visibles du même HEAD : **success**, hors M6-I **skipped**.
- Reviews : 0 ; threads : 0.

### Merge vérifié

- PR `#371` — **merged** le 2026-09-09.
- Merge commit : `4c4f7e11b29c6a37d3dd4bbd96069b347359227a`.
- Le lot a absorbé `master@c5b775987a1a3198a9e3fe3cfdf2426ac6de145e` avant merge ; le conflit unique du workflow Patient Indicators a été résolu sans écraser le correctif documents #384.
- Aucun déploiement Vercel effectué.

## AUTRES LOTS ENCORE OUVERTS

Les autres chantiers scientifiques restent distincts du lot ortho. La fermeture du lot ortho ne vaut pas certification scientifique globale.

## CLOSEOUT LOT ORTHO

Statut : **MERGED / CLOSEOUT TECHNIQUE VÉRIFIÉ**.

Chaîne réalisée : `code → tests → comportement observé → docs → CI → cohérence PR → ready → merge → post-merge`.

La protection de branche/required checks n'est pas entièrement lisible avec les permissions du connecteur et ne doit pas être surinterprétée.

## NEXT EXACT

Re-baseliner l'inventaire scientifique restant sur `master@4c4f7e11b29c6a37d3dd4bbd96069b347359227a`, identifier le prochain lot ouvert le plus critique, puis créer son Goal / Succès / Preuve avant toute modification. Aucun déploiement Vercel.
