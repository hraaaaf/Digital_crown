# LOT B — COMPETITIVE EVIDENCE HARNESS

**Statut : ACTIVE — baseline documentaire et exécutable**  
**Date : 2026-09-11**  
**Repo : `hraaaaf/Digital_crown`**  
**Baseline Digital Crown : `master@c6ed747b9b67c725d88b6cb5cc85914d969e2aed`**  
**Chantier parallèle Céphalo : PR #413 — hors scope de ce lot**

---

## 1. GOAL

Transformer le benchmark Digital Crown vs Orthalis en une base de preuve **versionnée, reproductible et falsifiable** avant toute implémentation concurrentielle lourde.

Le lot B ne cherche pas à augmenter le score produit. Il cherche à empêcher les faux gains issus d'une fonction supposée, d'une brochure concurrente interprétée comme preuve runtime, ou d'une comparaison non symétrique.

---

## 2. SUCCÈS OBSERVABLE

LOT B est fermé uniquement lorsque :

1. chaque capacité benchmarkée possède un identifiant stable ;
2. chaque affirmation Digital Crown est reliée à une preuve repo au ref figé ou marquée `NOT_PROVEN` ;
3. chaque affirmation Orthalis issue d'une source officielle est marquée `VENDOR_CLAIM_VERIFIED`, jamais assimilée à une preuve runtime indépendante ;
4. les capacités partiellement couvertes sont explicitement `PARTIAL_VERIFIED` ;
5. les scénarios comparatifs utilisent les mêmes objectifs fonctionnels pour les deux produits ;
6. temps, clics, erreurs et taux de réussite ne sont renseignés que lorsqu'ils ont été réellement mesurés ;
7. l'impossibilité actuelle d'exécuter un runtime Orthalis comparable est représentée par `BLOCKED_RUNTIME` / `NOT_MEASURED`, pas par une estimation ;
8. un dataset synthétique sans donnée patient réelle permet d'exécuter les scénarios Digital Crown ;
9. un validateur automatique refuse les statuts inconnus, IDs dupliqués, preuves vides et métriques prétendument mesurées sans provenance ;
10. la CI exacte du HEAD final est verte avant merge.

---

## 3. PREUVE ATTENDUE

Fichiers canoniques du harness :

- `docs/competitive/capabilities.json`
- `docs/competitive/orthalis_sources.json`
- `docs/competitive/scenarios.json`
- `docs/competitive/synthetic_dataset.json`
- `scripts/validate_competitive_evidence.py`
- `backend/tests/test_competitive_evidence_harness.py`

Commande de validation :

```bash
python scripts/validate_competitive_evidence.py
python -m pytest backend/tests/test_competitive_evidence_harness.py -q
```

---

## 4. VOCABULAIRE DE PREUVE

### Digital Crown

- `VERIFIED_REPO` : preuve directe dans le repo à la baseline figée.
- `PARTIAL_VERIFIED` : une partie substantielle est prouvée, mais la capacité benchmarkée complète ne l'est pas.
- `NOT_PROVEN` : preuve insuffisante dans le périmètre inspecté. **Ne signifie pas absent.**
- `BLOCKED_RUNTIME` : runtime comparable indisponible.

### Orthalis

- `VENDOR_CLAIM_VERIFIED` : la source officielle Orthalis/Orqual revendique explicitement la capacité.
- `NOT_PROVEN` : aucune source officielle suffisante dans le registre actuel.
- `BLOCKED_RUNTIME` : aucune exécution comparable et reproductible disponible dans ce chantier.

Une page marketing officielle est une preuve de **revendication fournisseur**, pas une validation de précision clinique, sécurité, performance ou UX.

---

## 5. BASELINE DIGITAL CROWN INSPECTÉE

Sources primaires internes inspectées sur `c6ed747b...` :

- `README.md`
- `STATE.md`
- `frontend/src/features/*`
- `backend/routers/*`
- `docs/CEPHALO_DIAGNOSTIC_SPEC.md`
- `docs/CABINET_ONPREM_GUIDE.md`
- `DigitalCrown.spec`

Éléments directement vérifiés :

- agenda et dossier patient ;
- documents et finance ;
- module ortho ;
- céphalométrie typée et calculs locaux ;
- panoramique / imagerie ciblée ;
- mobile appairé ;
- local-first / tenant isolation / médias authentifiés ;
- packaging Windows.

Éléments qui restent **non prouvés comme capacités complètes** dans ce harness :

- Media Hub transverse de niveau Kitview ;
- superposition céphalométrique longitudinale T0/T1/Tn complète ;
- Ortho Journey dédié de bout en bout jusqu'à contention/suivi ;
- Patient Companion avec toute la breadth Dentapoche ;
- connecteurs réels 3Shape / Invisalign / Spark / DentalMonitoring ;
- équivalence terrain à une base installée/supportée mature.

---

## 6. SOURCES ORTHALIS — RÈGLE

Le registre `orthalis_sources.json` contient uniquement des sources officielles Orthalis/Orqual utilisées pour cette baseline.

Sources vérifiées le 2026-09-11 :

- `https://www.orthalis.com/orthalis/`
- `https://www.orthalis.com/ceph/`
- `https://www.orthalis.com/kitview/`
- `https://www.orthalis.com/options/`
- `https://www.orthalis.com/les-passerelles/`
- `https://www.orthalis.com/`

Aucune métrique de temps/clics Orthalis n'est produite dans LOT B : la documentation publique vérifiée ne fournit pas un runtime instrumentable symétrique avec Digital Crown.

---

## 7. SCÉNARIOS COMMUNS

Le harness définit des scénarios à objectif commun, sans supposer que les produits ont la même navigation :

1. créer/retrouver un patient et positionner un rendez-vous ;
2. retrouver une information clinique longitudinale ;
3. préparer et produire un document cabinet ;
4. enregistrer/consulter un événement financier ;
5. ouvrir un cas orthodontique et retrouver son état ;
6. exécuter/revoir une analyse céphalométrique ;
7. importer/retrouver/comparer des médias cliniques ;
8. consulter une surface mobile/patient ;
9. utiliser un connecteur externe réel ;
10. restaurer la continuité cabinet après incident.

Tous les scénarios ne sont pas aujourd'hui exécutables des deux côtés. C'est précisément une information du benchmark, pas un trou à remplir avec de l'imagination.

---

## 8. MÉTRIQUES AUTORISÉES

Pour chaque exécution réelle :

- `success` : booléen ;
- `elapsed_ms` : temps mesuré, jamais estimé ;
- `primary_actions` : clic/tap/submit intentionnel ;
- `errors` : erreurs visibles ou runtime ;
- `retries` : reprises nécessaires ;
- `evidence_ref` : artefact, capture, log ou run exact.

Valeur obligatoire si non mesuré : `null` avec `measurement_status = NOT_MEASURED`.

Interdit : écrire `~10 s`, `environ 5 clics` ou toute autre approximation pour rendre un tableau plus séduisant.

---

## 9. DATASET SYNTHÉTIQUE

Le dataset LOT B :

- ne contient aucun vrai nom, téléphone, e-mail, image ou identifiant patient ;
- utilise des IDs `SYN-*` ;
- couvre au minimum patient simple, cas ortho, actes/paiements, documents et références de médias synthétiques ;
- ne doit jamais être injecté dans une base cabinet réelle ;
- sert uniquement de contrat reproductible pour les futurs probes benchmark.

---

## 10. ISOLEMENT DU CHANTIER CÉPHALO

LOT B peut s'exécuter en parallèle du chantier Céphalo parce qu'il ne modifie pas :

- `frontend/src/features/ortho/*`
- `backend/routers/cephalo_*`
- services/repositories céphalométriques ;
- registres scientifiques ;
- migrations cliniques ;
- UI Céphalo.

Le harness peut **référencer** ces fichiers comme preuve, jamais les modifier dans ce lot.

---

## 11. DEFINITION OF DONE LOT B

- manifests JSON valides ;
- zéro ID dupliqué ;
- zéro statut hors vocabulaire ;
- chaque `VERIFIED_REPO` contient au moins une preuve repo avec ref exact ;
- chaque `VENDOR_CLAIM_VERIFIED` contient une source officielle datée ;
- aucun champ de performance non mesuré n'a une valeur chiffrée ;
- dataset déclaré synthétique ;
- validator PASS ;
- test pytest PASS ;
- CI exacte du HEAD PASS ;
- PR/reviews/threads vérifiés ;
- merge sans toucher Céphalo.

---

## 12. NEXT EXACT APRÈS FERMETURE

Ouvrir **LOT C — Media Core** à partir du master réellement courant, en réutilisant `capabilities.json` et `scenarios.json` comme baseline de preuve.

Le premier gain de score n'est crédité qu'après fermeture des gates runtime/sécurité/UX de Media Core.

---

## AVIS EXPERT — REVUE INTERNE

Le principal risque d'un benchmark logiciel n'est pas de rater une fonction visible ; c'est de comparer une capacité prouvée côté Digital Crown à une promesse marketing côté concurrent, ou inversement. LOT B doit donc rester volontairement austère : ses `NOT_PROVEN` et `NOT_MEASURED` valent plus qu'une précision inventée.

## FICHIER CANONIQUE

`docs/competitive/LOT_B_EVIDENCE_HARNESS.md` — Competitive Evidence Harness — **LOT B ACTIVE**
