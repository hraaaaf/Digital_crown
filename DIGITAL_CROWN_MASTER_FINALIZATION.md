# DIGITAL CROWN — FINALISATION PRODUIT

**FICHIER CANONIQUE DE PILOTAGE GLOBAL — HORS CÉPHALOMÉTRIE**

Baseline de création : `master@dca24d01ca5591d4255f3ac85f79a32ab6d673c1`.

## Périmètre

Ce fichier fusionne le pilotage des chantiers Digital Crown restants en un seul programme maître.

**Exclusion explicite : la Céphalométrie reste un chantier séparé et n'entre ni dans le score global, ni dans le Next exact, ni dans les priorités de ce fichier.**

Le regroupement concerne le pilotage, pas l'exécution technique : les PR, branches, tests et certifications restent séparés par domaine afin de conserver des preuves attribuables et des rollbacks sûrs.

## Goal global

Obtenir un Digital Crown non-Céphalo cohérent, certifié et exploitable en cabinet réel, avec :
- workflows cliniques/documentaires cohérents ;
- multi-praticiens fermé ;
- UX patient transversale fermée ;
- sécurité/licence close ;
- portabilité physique certifiée ;
- expérience mobile terrain certifiée ;
- release/CI sans dette bloquante ;
- preuve finale consolidée sur master.

## Méthode de score

Le score global est un **indice de pilotage conservateur**, calculé uniquement à partir des chantiers non-Céphalo disposant déjà d'un pourcentage explicite et comparable dans le pilotage courant. Chaque axe compte une fois. Aucun poids subjectif n'est ajouté.

Axes inclus au score courant :
1. Document Studio P1→P6 : 100 %
2. Dossier Patient UX1 A/B/C : 100 %
3. Clinique multi-praticiens : 100 % après fermeture certifiée de P3
4. Portabilité : 89,2 % (`149/167 EP`)
5. Mobile Terrain : 70 %
6. Sécurité / Anti-piratage : 60 % baseline

Calcul courant : `(100 + 100 + 100 + 89,2 + 70 + 60) / 6 = 86,53 %`.

**Indice global courant : 86,5 %.**

Indice initial avant fermeture P3 : **82,4 %**.

Règle : un axe ne monte que sur preuve observable. Un sous-lot presque fini ne vaut pas 100 % tant que son gate de clôture n'est pas fermé.

Le benchmark Competitive vs Orthalis (`70/100` au dernier état vérifié) reste un KPI séparé et n'entre pas dans ce calcul, car il mesure une position comparative, pas un pourcentage d'exécution.

## État consolidé

### L1 — Document Studio — FERMÉ
- P1→P6 actifs certifiés.
- T1 transversal P1→P6 mergé via PR #465.
- Aucun lot produit supplémentaire requis ici tant qu'une régression n'est pas démontrée.

### L2 — Dossier Patient UX — FERMÉ
- UX1-A/B : PR #467 mergée.
- UX1-C overlays : PR #468 mergée.
- 390 / 768 / 1280 certifiés sur les gates dédiés.

### L3 — Clinique multi-praticiens — FERMÉ
- P0 agenda backend : fermé.
- P1 UI praticien : fermé.
- P2 patient/facturation : fermé.
- P3 documents/provenance/signature : implémentation majeure mergée via #454, #455, #457, #459.
- Gate final #463 `Clinic P3: certify local document preservation` : MERGED.
- HEAD certifié #463 : `30e5c235cebdb9f4e460b03a0687856336149c08`.
- Merge commit : `f16fc658dad0ee4ff67a919568359f1e90d4e2da`.
- CI #3763 : SUCCESS.
- `Clinic P3 Local Document Preservation Certification` #7 : SUCCESS.
- `Cabinet Upgrade PostgreSQL Certification` #216 : SUCCESS.
- `T2 Runtime Browser Certification` #2701 : SUCCESS.
- Preuve P3 : migration additive idempotente SQLite/PostgreSQL 18, identité de ligne/patient/path/SHA-256/taille/statut préservés, aucun backfill silencieux author/signer/timestamp, signature applicative limitée aux métadonnées prévues et bytes physiques inchangés.
- Frontière de preuve : rehearsal synthétique isolé local-vault + PostgreSQL 18 ; aucune prétention de copie de données patient réelles ni de signature électronique qualifiée.
- Axe multi-praticiens : **100 %**.

### L4 — Portabilité — HUMAN GATE
- État vérifié : `149/167 EP = 89,2 %`.
- P13 physique : `0/13 EP`.
- Fermeture requiert Windows 11 cabinet réel + stockage hors machine + Apple Silicon + closure guard.
- Aucun CI/rehearsal ne remplace ce gate physique.

### L5 — Mobile Terrain — HUMAN GATE
- Baseline de pilotage : 70 %.
- PR terrain historique #279 reste le référentiel du bootstrap HTTPS/mDNS.
- Gates physiques iPhone/Android/biométrie/Push restent non substituables.

### L6 — Sécurité / Anti-piratage — BLOQUÉ EXTERNE
- Baseline de pilotage : 60 %.
- SEC-1 / SEC-2 restent séparés techniquement.
- Blocage historique : accès control-plane production absent pour finaliser les mutations réelles et la chaîne OWNER/licences.
- Aucun pourcentage supplémentaire sans preuve prod réelle ou fermeture documentée du gate.

### L7 — Release / CI — ACTIF TRANSVERSE
- Correctifs packaging CODE_CERTIFIED #450 et #451 mergés.
- Dette Document History restaurée et fermée via PR #469, mergée sur `master` au commit `0c89a3f31dfb86b752b980e711f267c8bbb8d067`.
- HEAD #469 `6fca04b870f03bdd6805067ea6bba8ca93d85d35` : CI, T2, PostgreSQL et `Document History Actions Visual Certification` en SUCCESS ; artifact `document-history-actions-before-after` produit.
- P3 #463 a également fermé sur CI #3763 SUCCESS, PostgreSQL #216 SUCCESS et T2 #2701 SUCCESS.
- Cet axe n'entre pas dans l'indice numérique tant qu'aucun pourcentage canonique comparable n'est défini.
- Rechercher uniquement les dettes release/CI encore réellement ouvertes lors des closeouts suivants.

### L8 — Competitive / Media — KPI SÉPARÉ
- Score comparatif dernier état vérifié : `70,0/100` tant que LOT C n'est pas fermé.
- C1→C3 mergés ; C4 historique reste un sous-lot distinct tant que non fermé.
- Ce score ne doit jamais être confondu avec le % d'exécution global.

## Chemin critique unique

1. **Revalider les gates logiciels réellement encore ouverts** Competitive/Media et release, sans toucher Céphalo.
2. **Fermer le prochain gate logiciel prouvé ouvert**, en commençant par C4 Competitive/Media si son état live confirme qu'il reste réellement incomplet.
3. **Exécuter les gates physiques** : Portabilité P13 puis Mobile Terrain, selon disponibilité du matériel réel.
4. **Fermer Sécurité** dès que l'accès control-plane production permet l'exécution réelle des mutations autorisées.
5. **Certification globale non-Céphalo** : master propre, CI transverse verte, docs canoniques cohérents, aucun gate logiciel connu restant, inventaire explicite des seuls human/external gates résiduels.

## Next exact

**Fenêtre suivante : revalider l'état live de Competitive/Media C4 et des dettes release/CI, choisir le premier gate réellement ouvert, puis le fermer avec preuve sans toucher Céphalométrie.**

## Règles de continuité

- Une CI en cours n'arrête pas le programme ; faire le travail indépendant restant.
- Aucun lot n'est déclaré fermé sans preuve exacte.
- Aucun déploiement Vercel sans autorisation explicite.
- Les chantiers Céphalo ne sont ni modifiés, ni scorés, ni priorisés depuis ce fichier.
- Les anciens roadmaps restent des sources techniques historiques ; ce fichier devient la source de vérité pour le pilotage global non-Céphalo.

## Critère de fin réelle

Le programme est clos lorsque :
- tous les gates logiciels non-Céphalo sont fermés ;
- P3 est certifié ;
- CI/release transverse est saine ;
- Portabilité et Mobile Terrain ont leurs preuves physiques requises, ou sont explicitement documentés comme seuls human gates restants si la décision produit est de livrer avant leur exécution ;
- Sécurité prod est fermée ou explicitement bloquée par un accès externe non disponible ;
- le score global final est recalculé à partir d'états réellement fermés ;
- le closeout master et les docs canoniques concordent.

## Repères courant

- baseline de création : `master@dca24d01ca5591d4255f3ac85f79a32ab6d673c1`
- master post-P3 vérifié : `f16fc658dad0ee4ff67a919568359f1e90d4e2da`
- PR #463 : MERGED
- HEAD P3 certifié : `30e5c235cebdb9f4e460b03a0687856336149c08`
- indice global courant : **86,5 %**
- Céphalométrie : **hors périmètre**
- prochain gate logiciel : à revalider live entre Competitive/Media C4 et dette release/CI
- human gates : **Portabilité P13 + Mobile Terrain**
- external gate : **Security control-plane production**
