# HANDOVER — Digital Crown / Mutuelles dentaires — CNOPS → FAR

Date: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Fichier canonique global: `docs/audits/MUTUELLES_DENTAIRES_INTEGRATION_ROADMAP.md`
Closeout CNOPS: `docs/audits/MUTUELLES_DENTAIRES_CNOPS_CLOSEOUT.md`
Prompt de démarrage FAR: `docs/audits/MUTUELLES_DENTAIRES_FAR_START_PROMPT.md`

## Première action obligatoire dans la nouvelle conversation

1. Lire intégralement `docs/audits/MUTUELLES_DENTAIRES_INTEGRATION_ROADMAP.md`.
2. Lire intégralement `docs/audits/MUTUELLES_DENTAIRES_CNOPS_CLOSEOUT.md`.
3. Lire intégralement le présent handover.
4. Vérifier le `master` ACTUEL sur GitHub; ne jamais supposer que `5290df7c...` est encore HEAD.
5. Vérifier que le merge CNOPS `5290df7cb1a12989ef3799f92e32fd49d02d5ca1` est ancêtre du master actuel.
6. Vérifier les CI/certifications post-merge pertinentes du master actuel avant d'ouvrir FAR.
7. Ne lancer aucune implémentation FAR tant que le binaire FAR exact n'a pas été inspecté, hashé et classifié.

## État transmis — CNOPS

CNOPS est clos techniquement et mergé.

PR #534:
- merged;
- merge commit `5290df7cb1a12989ef3799f92e32fd49d02d5ca1`.

Preuve post-merge principale:
- CI #4674 / run `35126199252` — SUCCESS;
- Full backend regression DB/patients/documents — SUCCESS;
- frontend tests/build — SUCCESS;
- garde production — SUCCESS;
- Cabinet Upgrade PostgreSQL #925 — SUCCESS.

Score final CNOPS:
- EXECUTION_SCORE 9.4/10;
- ADVERSARIAL_SCORE 9.4/10;
- retenu 9.4/10.

## Architecture Mutuelles à préserver

FAR ne doit pas créer un deuxième moteur.

Architecture verrouillée:

`Patient -> Honoraires -> Preparer organisme -> Revue praticien -> Validation -> PDF -> DocumentArchive`

Briques communes à réutiliser:
- `InsuranceSubmissionDraft`;
- Honoraires comme source financière;
- `CatalogAct` comme catalogue clinique;
- `ngap_catalog_mappings` comme couche réglementaire versionnée;
- résolution NGAP serveur sans fuzzy matching;
- source store immuable et hash-addressed;
- politique administrative explicite et fail-closed;
- validation praticien;
- revalidation anti-stale;
- renderer PDF overlay hash-bound;
- hash PDF final;
- `DocumentArchive` comme archive documentaire.

Interdits:
- deuxième moteur Honoraires/Mutuelles;
- deuxième catalogue clinique;
- fuzzy mapping NGAP;
- backfill artificiel;
- données administratives inventées;
- signature/cachet/accord/décision assureur fabriqués;
- promotion silencieuse d'une source secondaire en `OFFICIAL_PRIMARY`;
- mutation production;
- déploiement Vercel sans autorisation explicite;
- merge sans accord utilisateur explicite.

## FAR — contrainte produit prioritaire

Information fournie explicitement par le cabinet:

**La feuille/dossier FAR contient une page d'ordonnance incluse dans le document, et cette page doit être traitée séparément des autres feuilles/pages.**

Statut de cette information au handover:
- exigence produit/cabinet: OUI;
- pagination exacte vérifiée sur binaire FAR: NON;
- SHA du binaire FAR: NON CONNU;
- coordonnées overlay ordonnance: NON CONNUES;
- provenance officielle/cabinet-validée: NON ÉTABLIE.

Ne jamais inventer ces éléments.

## Architecture attendue pour la page ordonnance FAR

Le lot FAR doit d'abord inspecter le binaire avant de figer l'implémentation. Sous réserve de cette inspection, le principe à maintenir est:

1. conserver le binaire FAR original comme source verrouillée avec son SHA-256;
2. classifier chaque page par rôle après inspection;
3. traiter la page ordonnance comme un sous-document logique distinct, par exemple rôle `FAR_PRESCRIPTION`, et non comme une simple page administrative du formulaire FAR;
4. lui donner son propre contrat de données, son propre profil overlay, ses propres champs autorisés/interdits, sa propre revue praticien et ses propres tests;
5. ne jamais déduire automatiquement un médicament, dosage, durée ou posologie depuis un acte dentaire ou un code NGAP;
6. toute donnée de prescription doit provenir d'une source explicite et être revue par le praticien;
7. signature/cachet restent hors auto-remplissage sauf preuve produit et règle explicite ultérieure;
8. la finalisation de la page ordonnance doit être indépendante de la validation des autres pages FAR;
9. après validation indépendante, le produit peut conserver un lien de dossier commun et, si le besoin fonctionnel le demande, réassembler les documents pour impression/export sans mélanger leurs règles de validation.

Le point 9 est un choix d'implémentation à confirmer après inspection du binaire; il ne faut pas casser le binaire source ni perdre la relation avec le dossier FAR d'origine.

## Goal FAR

Intégrer FAR au moteur Mutuelles existant avec:
- provenance/template exacts;
- politique administrative FAR explicite;
- profils overlay séparés par rôle de page si nécessaire;
- page ordonnance gérée séparément;
- revue praticien claire;
- validation/finalisation fail-closed;
- archivage reproductible;
- non-régression CNSS/CNOPS.

## Succès observable FAR

Avant toute implémentation fonctionnelle:
- binaire FAR exact obtenu;
- SHA-256 calculé;
- nombre de pages et dimensions inspectés;
- rôle de chaque page identifié;
- page ordonnance confirmée visuellement et indexée;
- trust de source explicite: `OFFICIAL_PRIMARY`, `CABINET_VALIDATED_BINARY` ou autre statut insuffisant;
- aucune zone sensible remplie sans preuve.

Avant merge FAR:
- moteur commun réutilisé;
- aucune régression CNSS/CNOPS;
- page ordonnance a un gate autonome;
- backend contracts ciblés verts;
- UI runtime réelle certifiée aux viewports utiles;
- comparaison visuelle Target ↔ Render acquise pour chaque rôle visuel pertinent;
- CI/non-régressions exact-HEAD vertes;
- branche sans divergence master;
- accord utilisateur explicite pour merge.

## Process UI/UX obligatoire FAR

Pour toute nouvelle UI FAR ou ordonnance:
1. BEFORE réel;
2. Goal écrit;
3. référence/mockup figé;
4. implémentation;
5. AFTER aux mêmes viewports;
6. comparaison Target ↔ Render;
7. tests fonctionnels/non-régression;
8. score visuel uniquement sur preuve observable.

La page ordonnance doit être évaluée séparément de l'UI des autres pages FAR.

## Next exact

Dans une nouvelle conversation:
1. vérifier master/CI;
2. récupérer/identifier le binaire FAR exact fourni par le cabinet;
3. inspecter le PDF page par page;
4. confirmer la page ordonnance et sa position;
5. définir le contrat de source/trust/hash;
6. écrire le gate FAR avant toute implémentation;
7. seulement ensuite ouvrir la branche fonctionnelle FAR.
