# Mutuelles dentaires — CNOPS gate

Date: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Branch: `feature/mutuelles-cnops-20260916`
Base master verifiee: `d15d81d0c040a5e6b255e02e635c988cd6d720ee`

## Goal

Integrer CNOPS dans le moteur Mutuelles existant sans creer de moteur parallele:

`Honoraires -> Preparer CNOPS -> revue praticien -> validation -> PDF CNOPS fidele -> DocumentArchive`

Aucune activation runtime CNOPS n'est autorisee tant que le binaire exact, sa confiance, son profil overlay hash-bound et la validation visuelle ne sont pas prouves.

## Baseline verifiee

- PR `#493` est MERGED dans `master` via `d15d81d0c040a5e6b255e02e635c988cd6d720ee`.
- Au premier controle post-merge du 2026-09-16, CI `#4522` sur ce merge commit etait `in_progress`; ceci n'est pas une certification post-merge.
- Le moteur commun existe deja: preparation depuis Honoraires, coherence source, validation praticien, source store immuable, renderer overlay hash-bound, finalisation et archivage.
- `InsuranceSubmissionDraft` et les types frontend supportent deja `CNOPS` comme organisme.
- Le registre contient deja `CNOPS_DENTAL_PENDING`, 2 pages attendues, trust `SECONDARY_REFERENCE`.
- Les verrous encore specifiques CNSS sont principalement la politique administrative, le facade/router de preparation/finalisation et l'UI de revue/action.

## Sources CNOPS recroisees

### Source primaire CNOPS — identite fonctionnelle

Le site officiel CNOPS expose une section `Feuille de soins dentaires` avec deux faces/pages dans ses informations pratiques.

Sources de decouverte primaires:
- `https://www.cnops.org.ma/fr/infopratiques`
- `https://www.cnops.org.ma/fr/soins-dentaires`
- `https://www.cnops.org.ma/fr/dossierem?r=117`
- `https://cnops.org.ma/fr/prestations?r=86`

Les pages officielles CNOPS corroborent pour le dossier dentaire les informations suivantes selon les actes/cas: identite assure/malade, INPE praticien, date des soins, honoraires, dent(s), code ou libelle d'acte, schema dentaire, cotation NGAP, ainsi que signature/cachet du praticien. Certaines prestations exigent aussi IF/ICE et des pieces complementaires.

Ces pages sont une preuve primaire des exigences et de l'existence du formulaire, mais elles ne fournissent pas dans l'environnement courant des octets PDF officiels exacts reproductiblement recuperes. Aucun hash `OFFICIAL_PRIMARY` n'est donc attribue.

### Copie secondaire exacte acquise — candidat cabinet

Une copie secondaire du formulaire dentaire a ete recuperee depuis un lien Google Drive expose par une page tierce. Elle est uniquement un candidat de travail, jamais une source officielle.

Identite exacte du candidat:
- fichier source: `Feuile de soins denatires CNOPS - ATARBAWI.COM.pdf`
- taille: `1 325 493` octets
- pages: `2`
- format: A4 paysage, `841.89 x 595.276 pt`
- champs PDF: aucun
- JavaScript: non
- SHA-256: `89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505`
- provenance actuelle: copie secondaire Google Drive / site tiers
- trust autorise actuellement: `SECONDARY_REFERENCE`

L'identite visuelle du candidat concorde avec une feuille CNOPS dentaire bilingue en deux pages et porte la reference ANAM `1.1.01.01`. Cette reference est constatee sur le candidat; elle n'est pas promue comme identite d'un binaire officiel tant que les octets officiels ne sont pas verrouilles.

## Zones constatees sur le candidat

### Page 1

Zones administratives visibles:
- nature de demande / execution;
- identite assure et beneficiaire;
- affiliation/immatriculation/CIN/adresse/lien;
- beneficiaire: nom, naissance, CIN, sexe;
- praticien dentiste: INPE;
- type de soins;
- entente prealable;
- accident.

Zones interdites a toute fabrication automatique:
- signature de l'assure;
- cachet/signature du praticien;
- cachet/signature de la mutuelle;
- identification/date de depot par l'agent;
- toute decision ou validation assureur.

### Page 2

La table dentaire visible comporte notamment:
- dent(s) traitee(s);
- code des actes;
- date des actes;
- lettre cle / cotation NGAP;
- valeur cle;
- montant facture;
- signature/cachet du chirurgien-dentiste.

Le schema dentaire est present sous la table.

Aucune coordonnee overlay CNOPS n'est encore canonisee: calibrer un profil avant le gate binaire ferait risquer de lier le runtime au mauvais formulaire.

## Reutilisation CNSS -> CNOPS

Reutiliser sans duplication:
- `InsuranceSubmissionDraft`;
- `prepare_insurance_draft_from_honoraires()`;
- `assert_draft_matches_honoraires_source()`;
- resolution NGAP serveur;
- source store immuable;
- `assert_insurance_template_source()`;
- `finalize_insurance_submission_pdf()`;
- renderer `InsuranceOverlayProfile` hash-bound;
- archivage `DocumentArchive` et preuve de rendu.

A generaliser ou ajouter seulement apres verrouillage du binaire:
- politique de completude/prefill administrative par organisme;
- selection du template/profile dans le router commun;
- action/revue frontend actuellement nommees CNSS;
- profil overlay CNOPS lie au SHA exact.

## Invariants fail-closed CNOPS

- Aucun champ assure/beneficiaire inconnu n'est invente.
- Aucun lien assure-beneficiaire n'est infere silencieusement.
- Aucun INPE/IF/ICE n'est deduit depuis un champ non explicitement identifie.
- Aucune signature, aucun cachet, aucune decision assureur n'est genere.
- `SECONDARY_REFERENCE` reste non finalisable.
- Un profil overlay n'est utilisable que pour `organization + version + SHA-256` exacts.
- Toute divergence Honoraires/Acte/NGAP/template apres validation invalide la finalisation.
- CNSS existant doit rester strictement non-regresse.

## Human gate courant

Le premier gate humain n'est pas une decision de design: c'est l'identite du formulaire.

Pour utiliser le candidat exact ci-dessus comme `CABINET_VALIDATED_BINARY`, le praticien/cabinet doit confirmer explicitement que le PDF de SHA-256 `89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505` correspond bien au formulaire CNOPS dentaire utilise/acceptable au cabinet.

Sans cette validation, le candidat reste `SECONDARY_REFERENCE` et le runtime CNOPS doit rester bloque.

## Next exact apres gate

Si le binaire exact est valide par le cabinet:
1. creer une definition CNOPS versionnee `CABINET_VALIDATED_BINARY` liee a ce SHA;
2. verrouiller/store le binaire avec identite du validateur;
3. definir la politique administrative CNOPS fail-closed a partir des zones autorisees;
4. calibrer un profil overlay sur CE SHA, sans coordonnees signature/cachet/assureur;
5. ajouter tests backend de hash, capacite lignes, champs interdits et non-regression CNSS;
6. effectuer le protocole UI obligatoire `BEFORE -> Goal -> mockup/reference -> implementation -> AFTER memes viewports -> comparaison/tests -> score visuel -> validation humaine`;
7. certifier l'exact HEAD avant closeout.

Si le binaire est refuse:
- ne modifier aucun trust runtime;
- obtenir le PDF exact utilise au cabinet ou un binaire officiel recuperable;
- recalculer son identite/hash avant toute calibration.
