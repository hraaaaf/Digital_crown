# START PROMPT — Digital Crown / Mutuelles dentaires — FAR

Tu reprends le chantier `Mutuelles dentaires` dans le repo `hraaaaf/Digital_crown`.

## Première règle

Ne commence PAS par coder FAR.

Commence par reconstruire l'état réel depuis GitHub et par inspecter le binaire FAR exact. Aucune provenance, pagination, coordonnée d'overlay, donnée administrative ou règle d'ordonnance ne doit être inventée.

## À lire en premier, dans cet ordre

1. `docs/audits/MUTUELLES_DENTAIRES_INTEGRATION_ROADMAP.md`
2. `docs/audits/MUTUELLES_DENTAIRES_CNOPS_CLOSEOUT.md`
3. `docs/audits/MUTUELLES_DENTAIRES_CNOPS_TO_FAR_HANDOVER.md`
4. `docs/audits/MUTUELLES_NGAP_DENTAL_REFERENCE.md`
5. les profils/services CNSS et CNOPS existants utiles au moteur commun

## État vérifié au handover

CNOPS a été mergé via PR #534.

Merge commit CNOPS:
`5290df7cb1a12989ef3799f92e32fd49d02d5ca1`

Preuve post-merge associée à CE commit:
- CI #4674 / run `35126199252` — SUCCESS;
- full backend regression DB/patients/documents — SUCCESS;
- frontend tests + build — SUCCESS;
- garde production — SUCCESS;
- Cabinet Upgrade PostgreSQL #925 — SUCCESS.

Ne suppose jamais que ce SHA est encore le master courant: vérifie GitHub au début de la nouvelle conversation.

## Architecture à préserver absolument

Un seul moteur Mutuelles:

`Patient -> Honoraires -> Preparer organisme -> Revue praticien -> Validation -> PDF -> DocumentArchive`

Réutiliser:
- `InsuranceSubmissionDraft`;
- Honoraires comme source financière;
- `CatalogAct` comme catalogue clinique;
- `ngap_catalog_mappings` comme couche réglementaire;
- source store immuable/hash-addressed;
- validation praticien;
- revalidation anti-stale;
- overlay PDF hash-bound;
- hash final;
- `DocumentArchive`.

Interdits:
- second moteur Mutuelles/Honoraires;
- second catalogue clinique;
- fuzzy mapping NGAP;
- backfill artificiel;
- données inconnues déduites silencieusement;
- signature/cachet/accord/décision assureur fabriqués;
- mutation production;
- déploiement Vercel sans autorisation explicite;
- merge sans accord utilisateur explicite.

## CONTRAINTE FAR À NE PAS PERDRE

Le cabinet précise qu'une **page d'ordonnance est incluse dans la feuille/dossier FAR**.

Cette page doit être **traitée séparément des autres feuilles/pages FAR**.

Important:
- cette exigence produit est confirmée par le cabinet;
- la page exacte, son index, son format, ses champs et son hash ne sont PAS encore vérifiés tant que le binaire FAR n'a pas été inspecté;
- ne jamais supposer que c'est la page 1, 2, 3, etc.;
- ne jamais copier les règles CNSS/CNOPS sur cette page sans inspection.

## Principe d'architecture attendu pour l'ordonnance

Après inspection du binaire FAR:
- conserver le document FAR original comme source verrouillée par SHA-256;
- classifier les pages par rôle;
- créer pour la page ordonnance un rôle logique séparé, p.ex. `FAR_PRESCRIPTION` si ce nom est cohérent avec le code existant;
- contrat de données séparé;
- profil overlay séparé;
- revue praticien séparée;
- validation/finalisation séparée;
- tests séparés;
- preuve visuelle séparée.

Aucune molécule, dose, posologie, durée ou fréquence ne doit être déduite automatiquement depuis les actes dentaires/NGAP. Toute prescription doit provenir d'une source explicite et être revue par le praticien.

La relation avec le dossier FAR global doit être conservée. Si le produit exige un PDF final combiné, la réassemblage ne doit intervenir qu'après validation indépendante des sous-documents et ne doit pas mélanger leurs règles métier.

## Goal du premier lot FAR

Produire un **FAR SOURCE/GATE** fiable avant toute implémentation:

1. identifier le binaire FAR exact;
2. calculer SHA-256, taille, pages, dimensions;
3. inspecter visuellement chaque page;
4. identifier le rôle de chaque page;
5. confirmer précisément la page ordonnance;
6. déterminer la provenance/trust réellement justifiable;
7. cartographier champs autorisés/interdits;
8. vérifier si le moteur commun actuel couvre les besoins ou nécessite seulement une extension minimale;
9. écrire `docs/audits/MUTUELLES_DENTAIRES_FAR_GATE.md` avec Goal / Succès / Preuves / Interdits / Next exact;
10. ne coder qu'après ce gate.

## Trust

Utiliser les mêmes règles que CNSS/CNOPS:
- `OFFICIAL_PRIMARY` uniquement avec preuve primaire réelle;
- `CABINET_VALIDATED_BINARY` uniquement si le cabinet valide explicitement les octets exacts;
- une copie secondaire non validée reste insuffisante pour finaliser.

Le trust doit être lié au SHA exact. Tout autre binaire repasse le gate.

## UI/UX FAR

Pour toute UI nouvelle:
BEFORE réel → Goal écrit → référence/mockup → implémentation → AFTER mêmes viewports → comparaison Target ↔ Render → tests → score visuel.

La page ordonnance est une surface distincte: sa certification UI/visuelle ne peut pas être noyée dans la note globale du formulaire FAR.

## Tests et non-régression

Avant merge FAR, prouver au minimum:
- CNSS toujours fonctionnel;
- CNOPS toujours fonctionnel;
- Honoraires inchangé comme source financière;
- DB/patients/documents non régressés;
- source store/hash gates fail-closed;
- NGAP sans fuzzy mapping;
- aucune signature/cachet/décision assureur auto-générée;
- ordonnance FAR indépendante des autres pages;
- CI exact-HEAD verte;
- branche `behind_by=0` et mergeable;
- runtime UI réel certifié;
- accord utilisateur explicite avant merge.

## Score

Pour chaque étape matérielle:
- EXECUTION_SCORE /10;
- ADVERSARIAL_SCORE /10;
- retenir le plus bas, jamais la moyenne;
- écart >0,5 = investigation;
- même agent exécution + revue = plafond 9,4/10;
- preuve requise absente ou test requis rouge = max 7,9/10;
- régression = max 6,9/10;
- blocker sécurité/privacy/data/claim clinique = max 5,9/10 + BLOCKED;
- UI sans vraie comparaison Target ↔ Render = max 7,5/10.

## Next exact à l'ouverture de la nouvelle conversation

1. lire les 4 documents listés;
2. vérifier master/HEAD/CI actuels;
3. localiser le binaire FAR exact disponible pour le cabinet;
4. l'inspecter page par page;
5. identifier et isoler logiquement la page ordonnance;
6. produire le gate FAR avant toute implémentation.

Ne redemande pas une validation déjà acquise pour CNOPS. FAR repart de ses propres preuves.
