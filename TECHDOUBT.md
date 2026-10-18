# TECHDOUBT — Digital Crown | Registre des réserves techniques

**Statut : OUVERT / registre vivant.** Créé le 18 octobre 2026 à la demande du propriétaire pour éviter que les réserves transversales F05 absorbent le chantier produit **LOT07 Desktop Experience & MultiView**.

**Décision de séquencement :** poursuivre les développements **visuels, autonomes et réversibles** du LOT07 pendant que les réserves sont consignées ici. Les traiter et les retester **avant GLOBAL-G10-S et LOT10 physique** selon les dépendances. *Une réserve de sécurité clinique BLOCKER/MAJOR interdit la fusion, l'activation, l'installation en cabinet et toute utilisation réelle de la fonctionnalité concernée jusqu'à son traitement ; le report de diagnostic n'est pas une autorisation de mise en production.*

Source de vérité : [Roadmap unique](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb) · [LOT07](https://app.notion.com/p/3e677c66336281639049f4cc7be1e5ae) · [PR F05-R2 #954](https://github.com/hraaaaf/Digital_crown/pull/954) · [LOT07 contract #893](https://github.com/hraaaaf/Digital_crown/pull/893).

## Règles d'utilisation

- Chaque réserve doit conserver : **ID, sévérité, portée, origine, HEAD vérifié, preuve disponible, preuve manquante, dépendance de livraison, critère de clôture et statut**. N'effacer aucune réserve sur la foi d'une CI d'un ancien SHA ou d'une seule revue interne.
- Statuts : **OPEN** / **WIP_NON_CERTIFIE** / **TESTED_SYNTHETIC** / **READY_FOR_INDEPENDENT_REVIEW** / **CLOSED_PROVEN**. Seul CLOSED_PROVEN exige des tests réellement exécutés sur HEAD figé, deux revues indépendantes si la modification est critique, et approbation adéquate.
- Toute ligne **P0/P1 sécurité clinique** reste **NO-GO installation / merge du code concerné**. Le développement indépendant du LOT07 peut se poursuivre en branches DRAFT et fixtures synthétiques, **sans composer automatiquement** ses changements avec F05.
- Aucune modification d'un gate REQUIRED pour masquer un problème de périmètre ; classifier REQUIRED / EXPERIMENTAL / HORS SCOPE sans extension automatique.
- **Avant LOT10** : exécuter le gate synthétique transverse **GLOBAL-G10-S** couvrant toutes les fonctionnalités réellement supportées V1 + V1.5 (et pas seulement LOT07), avec un inventaire traçable et zéro P0/P1. LOT10.1–10.8 restent des lots de **preuve matérielle réelle**, pas un conteneur pour tests logiciels manquants.
- Ce fichier est un **backlog vérifiable**, pas une attestation de certification ni un substitut aux tickets/PR/revues.

## Registre de réserves

### TD-001 — F05 R2 : quota anti-abus commun HTTP/Relay
- **Priorité : P1 / MAJOR sécurité. Statut : WIP_NON_CERTIFIE.**
- **Origine :** reviews indépendantes #952 (REV1-A3) ; remédiation isolée [#954](https://github.com/hraaaaf/Digital_crown/pull/954).
- **État précis au 18/10/2026 :** l'ancien HEAD #954 `9df3ca4ea9251bd9220872f5f2b4bc563d0338bf` dispose de tests PostgreSQL [#39126379651](https://github.com/hraaaaf/Digital_crown/actions/runs/39126379651) SUCCESS sur révocation, mauvais endpoint et ACK perdu. **Mais** le HEAD #954 a avancé à `c59ff68781ea725f6e918620ee50005943e94a15` pendant la rédaction d'un quota DB partagé et d'une migration `f05q0000033` : modifications **non certifiées à ce HEAD**. Ce HEAD ne doit pas être qualifié GREEN par transfert.
- **Preuves nécessaires :** quota réellement partagé entre deux PIDs HTTP + Relay sur PostgreSQL 16 et SQLite/SQLCipher supporté ; même accès/opération, plafond et fenêtre, 429/Retry-After, refus 503 fail-closed si schéma absent/DB inaccessible, compteur non annulé par rollback métier, isolation entre accès/cabinets et preuve de compatibilité des migrations.
- **Clôture :** logs et assertions SQL sur SHA final, zéro fail-open, revues indépendantes A/B, no activation avant Human Gate.

### TD-002 — F05 R2 : course révocation / commandes / archivage
- **Priorité : P1 / sécurité clinique. Statut : TESTED_SYNTHETIC (partiel).**
- **Preuves :** [#954, run #39126379651](https://github.com/hraaaaf/Digital_crown/actions/runs/39126379651), sur `9df3ca4e...` : 49 tests contrats, deux vrais PIDs FastAPI sur PG fictif, verrou accès et ordonnance de révocation, commande post-révocation refusée, SQL sans réservation; test archivage patient+audit dans une transaction.
- **Manque :** parcours complet Relay authentifié sur identité révoquée, suppression/revocation autres entrées, fail-closed SQLite durable et faute forcée worker.
- **Clôture :** SQL post-COMMIT et vrai worker Relay démontrés, mêmes tests sur HEAD d'intégration final, revues A/B.

### TD-003 — Patient Companion : ACK perdu / anciens reçus / réconciliation
- **Priorité : P1 / cohérence clinique et utilisateur. Statut : TESTED_SYNTHETIC (partiel).**
- **Preuves :** [run #39126379651](https://github.com/hraaaaf/Digital_crown/actions/runs/39126379651) : HTTP JOSE `RECONCILIATION_REQUIRED`, une réservation et un reçu persistants ; PWA comporte l'état `needs_reconciliation`.
- **Manque :** parcours réellement authentifié depuis PWA mobile, perte d'ACK pendant reconnexion, synchronisation Relay réelle, visualisation du RDV existant, interdiction d'un deuxième essai jusqu'à résolution. Vérifier les actions UI et captures AFTER à viewports identiques.
- **Clôture :** E2E sans seconde réservation ni fausse affirmation de succès, erreur compréhensible et réconciliation auditable.

### TD-004 — PostgreSQL/SQLite : arrêt forcé, migration, backup et restauration
- **Priorité : P1 sécurité des données / exploitation. Statut : OPEN.**
- **Manque :** SIGKILL worker entre mutation et COMMIT, redémarrage/rejeu avec vérification SQL, répétition d'une migration sur copie **synthétique représentative** d'une base de cabinet PostgreSQL pré-version, ainsi que scénario SQLite/SQLCipher existant, sauvegarde et restauration.
- **Clôture :** run de reprise exact SHA, zéro reçu et rendez-vous incohérents, procédures reproductibles ; ne jamais modifier une vraie base clinique lors de ces certifications.

### TD-005 — Frontière du gate Agenda P2 AFTER
- **Priorité : P1 de certification UX / non assimilé à une régression d'interface. Statut : OPEN.**
- **Preuve :** [run #39126379443](https://github.com/hraaaaf/Digital_crown/actions/runs/39126379443) FAILURE car diff cumulé #954 contient `.github/workflows/lot07-07a-postgres-cert.yml` hors périmètre P2. La capture AFTER P2 n'est pas exécutée : **ce n'est pas un FAIL visuel démontré ni un PASS**.
- **Clôture :** exécuter P2 BEFORE/AFTER depuis une branche UX bornée, sans désactiver/modifier le garde de périmètre. Valider mêmes données, états, viewports, zoom, approbation visuelle sur HEAD.

### TD-006 — Desktop LOT07 : sécurité et complétude du MultiView Studio
- **Priorité : P1 si fuite inter-patient/RBAC ; sinon dette produit P2. Statut : OPEN.**
- **État :** pilote G1 **deux panneaux Dossier + Imagerie** sur [#897](https://github.com/hraaaaf/Digital_crown/pull/897) HEAD `b75012e3edc1a63d1b904635cafb2a20dc4913b2`, CI/human visual gate verts sur cette branche, **DRAFT non fusionnée**.
- **Reste :** cadre ViewSlot authentifié couvrant tous les modules éligibles desktop, 9 layouts déclaratifs, séparation des patients A/B, états persistés sans PHI, accès par rôle/panneau, onglets désynchronisés, fenêtres read-only, vraie preuve physique deux moniteurs au LOT10.
- **Clôture :** preuves E2E desktop et permissions exact SHA, aucune fuite ni perte de brouillon ; approbation de chaque palier visuel. Les écrans Pocket/Patient Companion ne doivent pas être artificiellement intégrés au MultiView desktop.

### TD-007 — LOT07 : expériences Signature Iconic, Command et sélecteur
- **Priorité : P2 produit. Statut : OPEN / LOT07 À FAIRE (pas une certification différée).**
- **Séquence :** 07-A Core+G1 existants → **07-B Signature Iconic** → **07-C Command** → **07-D choix par utilisateur+poste** → **07-E acceptance**. Theme clinique `selected_theme` indépendant ; pas de préférence clinique dans `localStorage` non protégé ni mélange avec la palette cabinet. Preview/apply/cancel/rollback, reduced-motion, contraste, zoom natif, non-régression.
- **Clôture :** code réel en PRs DRAFT séparées, tests UI BEFORE/TARGET/AFTER, parcours validés, Human Gate puis intégration approuvée. Ne pas confondre screenshots concepts et runtime certifié.
- **BENCH-REA-07C R2 (18/10/2026 — RISQUE DE FAUSSE PREUVE UX, statut OUVERT)** : [PR labo #961](https://github.com/hraaaaf/Digital_crown/pull/961) DRAFT ; [run exact-HEAD #39139120482](https://github.com/hraaaaf/Digital_crown/actions/runs/39139120482) SUCCESS source `9ad46bb5f03c43ec2a149c3109c20470dd40558d` (job `117709691126`). REA 6.7.0 a examiné la page de démonstration publique : deux frames `demo.orthalis.com`, 312 nœuds DOM échantillonnés et capture scénario DOM/accessibilité/URL/screenshot en état `captured`, **sans publication ni revue visuelle du screenshot, sans clic ni flux patient**. Le lien officiel de démo [Orthalis Connect](https://www.orthalis.com/en/orthalis-connect/) mène à `demo.orthalis.com`, iframe `/guacamole/` : rendu métier distant, pas de garantie d'actions natives via DOM. Les fonctionnalités publiées sur orthalis.com/orthalis, /kitview, /ceph et /nos-formations/client restent DOCUMENTÉES, pas exécutées. Une tentative d'instrumentation supplémentaire a été refusée par les contrôles de sécurité : aucune preuve tirée de cette tentative. Ne pas attribuer un score ni un PASS ergonomique ou concevoir Command 07-C maintenant. **Critère de clôture** : démo métier autorisée avec données synthétiques, traces REA des actions à l'écran Agenda→fiche de synthèse→RDV et chemin imagerie/ODF lorsqu'accessibles, mesures comparables et captures anonymisées vérifiées sur les deux logiciels, avec limites documentées et revue contradictoire. Pas de merge/deploy ni de déverrouillage 07-C avant preuve. Voir [commentaire GitHub #6251520811](https://github.com/hraaaaf/Digital_crown/pull/961#issuecomment-6251520811).

### TD-008 — Full-app synthetic gate GLOBAL-G10-S avant LOT10
- **Priorité : P1 de release/certification. Statut : OPEN.**
- **Portée :** 100 % des modules/pages/features réellement supportés V1+V1.5 inventoriés, rôles, erreurs, confidentialité, scénarios multi-module ; matériel LOT10 déclaré **HORS SCOPE** de ce gate.
- **Clôture :** 100 % des éléments classés (ou explicitement « en construction »), tous gates REQUIRED applicables GREEN sur HEAD exact, aucun P0/P1, preuves inspectées et revues. **Ne pas démarrer LOT10 physique sans ce gate.**

## Gouvernance, frontières et ordre de reprise

**Voie 1 — Travail produit autorisé dès maintenant (sans fusion/déploiement) :**
réutiliser G0/G1 et P1/P2 existants, cadrer/implémenter 07-B Signature Iconic sur branche dédiée, puis 07-C, 07-D, 07-E et les sous-paliers MultiView ; preuves sur données fictives.

**Voie 2 — Réserves isolées (pas de travail produit bloqué artificiellement) :**
terminer TD-001→TD-005, revue indépendante et Human Gate sur le code de sécurité concerné **avant toute composition/release qui en dépend** ; tenir le registre à jour à chaque nouveau HEAD.

**Gate avant LOT10 :** résoudre toute réserve P0/P1, mettre à jour et certifier GLOBAL-G10-S, puis seulement organiser les tests physiques du LOT10 ; les items visuels P2 de LOT07 doivent être clos par le lot produit, pas simplement repoussés à la certification de matériel.

**Règle d'arbitrage :** si un nouveau défaut clinique P0/P1 menace même les tests synthétiques ou des utilisateurs existants, suspendre la fonctionnalité concernée et corriger en priorité. « Techdoubt » ne signifie jamais « ignorer un risque ».

Dernière vérification de ce fichier : **18/10/2026**. Toute conclusion future doit citer l'HEAD GitHub exact et ses runs, pas celui-ci par défaut.
