# DIGITAL CROWN — SCIENTIFIC CORE REBUILD — CANONICAL HANDOVER

**Règle de reprise :** vérifier `repo / branche / PR / HEAD / CI` avant toute conclusion. Les runs historiques ne valent jamais état courant.

## GOAL FINAL

Noyau scientifique minimal, explicable, sourcé/versionné et fail-closed.

Invariant : `measurement != diagnosis != indication != treatment`.

Succès : aucune donnée patient inventée influente ; aucune interprétation ou décision clinique autonome non validée ; séparation observation/interprétation/décision praticien ; tests et CI verts avant merge ; aucun déploiement Vercel sans autorisation explicite.

## REPO

Repo : `hraaaaf/Digital_crown`  
Branche : `refactor/scientific-core-purge`  
PR : `#371` — draft, ouverte, mergeable au dernier contrôle  
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

### Audit `ai_advisor` corrigé

L'audit initial était incomplet. Deux runs ont révélé des références runtime après suppression du wrapper :

1. CI `34344464825` : référence résiduelle dans `backend/routers/ia.py`, corrigée.
2. CI `34353944361` et T2 `34353944561` : dépendance active dans `backend/services/clinical_intelligence.py`, corrigée par remplacement fail-closed.

Ces runs sont des preuves historiques rouges, pas une certification du HEAD courant.

### Tests clés

- `test_cephalo_geometry_only.py`
- `test_cephalo_treatment_boundary.py`
- `test_cephalo_engine_reachability.py`
- `test_cephalo_consistency_structural_only.py`
- `test_cephalo_service_normative_context.py` — contrat d'intégration fail-closed : âge/sexe ne créent aucune autorité normative.
- `test_bilan_ortho_fail_closed.py`
- `test_ortho_frontend_fail_closed_contract.py`
- `test_clinical_intelligence_cephalo_fail_closed.py` — inclut le verrou `ORTHODONTIE -> motif_treatment_hints == []`.
- `test_scientific_core_purge_contract.py`

### Preuve CI de closeout avant mise à jour documentaire

Sur le HEAD produit `a6ddb33041b07a772e55ba7f44b01fa69b2ae1c1` :

- CI `34401719011` : **success** ; backend `3019 passed, 8 skipped, 4 warnings` ; frontend tests/build, garde production et M4-A/B/C verts.
- T2 `34401719076` : **success**.
- P7 `34401719000` : **success**.
- P8 `34401719065` : **success**.
- Settings `34401719008` : **success**.
- Catalog `34401719077` : **success**.
- P6 Windows Packaging `34401719033` : **success**.
- M6-I `34401719102` : **skipped**.
- Patient Indicators `34401719118` : **failure de harness connue**, reproduite sur l'attente obsolète du heading `Dossiers Patients` après backend ciblé 10/10, frontend ciblé 4/4, build et runtimes verts ; aucune régression produit démontrée. Le correctif du workflow est bloqué par le garde d'écriture du connecteur GitHub.

Aucun nouveau défaut scientifique ou fonctionnel du lot n'est connu à ce stade.

## AUTRES LOTS ENCORE OUVERTS

Les autres chantiers scientifiques restent distincts du closeout ortho. La fermeture du lot ortho ne vaut pas certification scientifique globale.

## CLOSEOUT LOT ORTHO

Ordre : `code → tests → comportement observé → docs → CI → cohérence PR → ready → merge → post-merge`.

Avant merge : aucun rouge scientifique ; aucun comportement clinique autonome non validé connu dans ce lot ; docs cohérentes ; checks visibles du même HEAD verts/acceptables. La protection de branche/required checks n'est pas entièrement lisible avec les permissions du connecteur et ne doit pas être surinterprétée.

## NEXT EXACT

Vérifier les checks du nouveau HEAD documentaire. Si le CI scientifique reste vert et qu'aucun nouveau rouge attribuable au lot n'apparaît : cohérence PR finale → ready → merge avec `expected_head_sha` exact → contrôle post-merge. Aucun déploiement Vercel.
