# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-09-09.

> **Source de vérité unique du chantier.** `docs/PORTABILITY_LAUNCHER_ROADMAP.md` est déprécié et renvoie vers ce fichier.

## Goal global

Digital Crown doit rester un seul produit local-first, issu d’un cœur partagé, installable et exploitable sur Windows et macOS avec runtime, données cabinet, restauration, licence/secrets, packaging, mises à jour, récupération et certification maîtrisés.

## Succès global

- cœur applicatif commun Windows/macOS, sans fork fonctionnel ;
- intégrations OS derrière des frontières explicites ;
- runtime unique avec readiness réelle ;
- chemins data/config/log/runtime natifs ;
- cabinet portable indépendamment des secrets machine ;
- packaging Windows/macOS certifié ;
- backup, update et rollback vérifiés ;
- hardware explicitement classé par OS ;
- certification finale réelle sur cabinet avant revendication de support complet.

## Doctrine

- un cœur commun, pas deux applications ;
- Frontend React + backend FastAPI partagés ;
- comportement OS-spécifique derrière adapters/frontières ;
- données cabinet et secrets machine séparés ;
- aucune preuve CI ne remplace une gate physique quand celle-ci est explicitement requise ;
- aucun déploiement Vercel dans ce chantier sans autorisation explicite.

## Effort canonique corrigé

| Lot | Effort | État vérifié |
|---|---:|---|
| P0 — Baseline & portability contract | 5 EP | CLOSED ✅ |
| P1 — OS abstraction layer | 13 EP | CLOSED ✅ |
| P2 — Runtime Supervisor / Launcher V2 | 13 EP | CLOSED ✅ |
| P3 — Cabinet data portability | 13 EP | CLOSED ✅ |
| P4 — Licence, secrets & machine identity | 8 EP | CLOSED ✅ |
| P5 — Scientific/native runtime portability | 13 EP | CLOSED ✅ |
| P6 — Industrialized Windows packaging | 8 EP | CLOSED ✅ |
| P7 — Native macOS packaging | 13 EP | CLOSED ✅ |
| P8 — Hardware & peripherals | 21 EP | CLOSED ✅ |
| P9 — Backup / Recovery / DR | 8 EP | CLOSED ✅ |
| P10 — Cross-platform Update Engine | 13 EP | CLOSED ✅ |
| P11 — Launcher & Recovery UX | 8 EP | CLOSED ✅ |
| P12 — CI & certification matrix | 13 EP | CLOSED ✅ |
| P13 — Real cabinet certification | 13 EP | ACTIVE — 0/13 |
| P14 — Closeout | 5 EP | PLANNED |
| **TOTAL** | **167 EP** | |

Effort Points = complexité relative, pas durée. Le précédent total `162 EP` était une erreur arithmétique ; la somme réelle des lots est `167 EP`.

## P0 → P5 — fondations historiques

P0–P5 restent CLOSED sur leurs preuves historiques déjà intégrées à `master` : abstraction OS, runtime supervisor, portabilité cabinet, licence/secrets, runtime scientifique/native fail-closed. Les anciennes preuves détaillées restent dans `docs/portability/` et l’historique Git.

## P6 → P12 — consolidation sur master moderne — CLOSED ✅

### Goal

Réintégrer le stack Portability P6→P12 historiquement certifié sur le `master` moderne sans merger l’ancienne branche divergente et sans écraser Mobile/Marketplace ou les autres évolutions récentes.

### Implémentation consolidée

Branche : `refactor/portability-master-consolidation`.

Candidat produit exact avant closeout docs :
`b149412edc0dce605b8b5bcda49145320ee673df`.

La consolidation :
- repart du master `272d6b71d5c2a23f3ac8dbc97342c450ca311093` ;
- porte les modules/workflows/tests/docs P6→P13 isolés ;
- réconcilie `platform.py`, `runtime_supervisor.py`, `run.py`, `DigitalCrown.spec`, Inno et le builder legacy ;
- conserve les extensions modernes Mobile/Marketplace ;
- expose P10 sur `/api/update/*` et `/api/admin/update/*` avec permission admin ;
- restaure le snapshot DR P9 dans le scheduler moderne ;
- restaure les dépendances package explicites ;
- restaure le contrat UX P11 (`Démarrage de Digital Crown...`, lifecycle Analyse → Secours → Restauration → Vérification) ;
- corrige le harness AFTER pour ignorer uniquement les échecs de fontes externes, sans masquer les erreurs réseau produit.

### Preuves exact-head `b149412e…`

Tous les gates applicables sont SUCCESS :
- CI #2925 — run `34353472792` ;
- P5 Native Dependency #354 — `34353472891` ;
- P6 Windows Packaging #169 — `34353472901` ;
- P6 Authenticode Probe #31 — `34353472897` ;
- P7 macOS Private Distribution #40 — `34353472850` ;
- P7/P10 Clean Hosted #23 — `34353472883` ;
- P8 Hardware Compatibility #93 — `34353472784` ;
- P9 Backup Recovery DR #26 — `34353472906` ;
- P10 Update Engine #155 — `34353472814` ;
- P10 macOS Update Engine #73 — `34353472811` ;
- P11 Launcher Recovery UX #132 — `34353472785` ;
- P12 Certification Matrix Prep #87 — `34353472866` ;
- Portability Runtime #466 — `34353472932` ;
- T2 Runtime Browser #1953 — `34353472837` ;
- Settings Guided Restore AFTER #219 — `34353472913` ;
- Settings Security #242, RBAC #294, Onboarding P2 #275, R11 #422 — SUCCESS.

M6-I #753 est SKIPPED car path-inapplicable à ce lot.

### Preuve visuelle P11 / Guided Restore

Référence historique BEFORE/AFTER :
- Startup recovery AFTER historique : 9.3/10 ;
- Guided Restore AFTER historique : 9.1/10.

Revalidation actuelle :
- P11 #132 — SUCCESS ;
- Guided Restore AFTER #219 — SUCCESS ;
- artifact exact-head `guided-restore-after` id `10104796866` ;
- digest `sha256:160180829e139e0562da3a75e25c56efcc7cf351108c7d43a50ab2d387da31dd` ;
- 5 viewports capturés par le gate AFTER, sans overflow/page error/5xx/request failure produit selon le workflow certifié.

Le score visuel historique reste la référence de comparaison ; cette consolidation n’introduit pas de redesign supplémentaire.

## Progression vérifiée

Crédit technique historique et désormais recertifié sur la branche de consolidation actuelle :
- P0→P12 = **149 / 167 EP = 89.2%** ;
- P13 = **0 / 13 EP** ;
- P14 = 0 / 5 EP.

Ce `89.2%` est une progression technique Portability, pas une certification P13 de cabinet réel.

## P13 — Real cabinet certification — ACTIVE — 0/13 EP

### Goal

Prouver le flow cabinet critique sur machines réelles Windows/macOS avec vraie redondance off-machine et attestations opérateur.

### Gate final non substituable par CI

- Windows 11 réel, `execution_context=cabinet_local` ;
- vraie cible USB/removable/NAS hors machine ;
- first launch/runtime/restore/update observés ;
- attestation opérateur ;
- même release candidate Windows/macOS ;
- macOS Apple Silicon réel ; un remote `.metal` authentique peut contribuer seulement si toutes les observations physiques obligatoires sont réellement attestées ;
- `scripts/p13_real_cabinet_closure_guard.py` doit passer.

P13-R remote bare-metal = réduction de risque uniquement, **0 EP**.

## P14 — Closeout — PLANNED — 5 EP

P14 ne peut fermer qu’après P13 : documentation install/recovery/update, matrices OS/hardware, troubleshooting, gouvernance et preuve finale cohérents avec le HEAD réellement certifié.

## État courant

- P0–P12 : **CLOSED ✅** sur la consolidation actuelle ;
- P13 : **ACTIVE — 0/13 EP** ;
- P14 : **PLANNED** ;
- validé : **149 / 167 EP = 89.2%** ;
- aucun EP partiel n’est crédité ;
- aucun Vercel.

## Next exact

1. merger la consolidation actuelle sur `master` après dernier exact-head docs ;
2. vérifier le nouveau master et fermer les PR historiques superseded `#237` et `#299` sans merge ;
3. repartir de ce master pour le lot P13 physique ;
4. créditer P13 uniquement après preuves physiques complètes ;
5. exécuter P14 après P13.
