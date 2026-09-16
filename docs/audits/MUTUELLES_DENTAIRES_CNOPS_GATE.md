# Mutuelles dentaires — CNOPS gate

Date: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Branch: `feature/mutuelles-cnops-20260916`
Base master verifiee: `d15d81d0c040a5e6b255e02e635c988cd6d720ee`

## Goal

Integrer CNOPS dans le moteur Mutuelles existant sans creer de moteur parallele:

`Honoraires -> Preparer CNOPS -> revue praticien -> validation -> PDF CNOPS fidele -> DocumentArchive`

## Baseline verifiee

- PR `#493` est MERGED dans `master` via `d15d81d0c040a5e6b255e02e635c988cd6d720ee`.
- Au premier controle post-merge du 2026-09-16, CI `#4522` sur ce merge commit etait `in_progress`; ceci n'est pas une certification post-merge.
- Le moteur commun existe deja: preparation depuis Honoraires, coherence source, validation praticien, source store immuable, renderer overlay hash-bound, finalisation et archivage.
- `InsuranceSubmissionDraft` et les types frontend supportent deja `CNOPS` comme organisme.
- Les verrous encore specifiques CNSS sont principalement la politique administrative, le facade/router de preparation/finalisation et l'UI de revue/action.

## Sources CNOPS recroisees

### Source primaire CNOPS — identite fonctionnelle

Le site officiel CNOPS expose une section `Feuille de soins dentaires` avec deux faces/pages dans ses informations pratiques.

Sources de decouverte primaires:
- `https://www.cnops.org.ma/fr/infopratiques`
- `https://www.cnops.org.ma/fr/soins-dentaires`
- `https://www.cnops.org.ma/fr/dossierem?r=117`
- `https://cnops.org.ma/fr/prestations?r=86`

Ces pages sont une preuve primaire des exigences et de l'existence du formulaire, mais elles ne fournissent pas dans l'environnement courant des octets PDF officiels exacts reproductiblement recuperes. Aucun hash `OFFICIAL_PRIMARY` n'est donc attribue.

### Binaire exact valide par le cabinet

Le 2026-09-16, le praticien/cabinet a explicitement confirme que le candidat exact inspecte correspond au formulaire CNOPS dentaire utilise/acceptable au cabinet.

Identite immuable validee:
- fichier source inspecte: `Feuile de soins denatires CNOPS - ATARBAWI.COM.pdf`
- taille: `1 325 493` octets
- pages: `2`
- format: A4 paysage, `841.89 x 595.276 pt`
- champs PDF: aucun
- JavaScript: non
- SHA-256: `89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505`
- provenance d'acquisition: copie secondaire Google Drive / site tiers
- validation humaine: cabinet/praticien, explicite, 2026-09-16
- trust runtime autorise pour CE binaire exact: `CABINET_VALIDATED_BINARY`
- version runtime: `CNOPS-DENTAL-CABINET-2026-09-16`

Cette validation ne transforme PAS la provenance en `OFFICIAL_PRIMARY`. Toute autre sequence d'octets, meme visuellement identique, doit repasser le gate hash/validation.

## Zones constatees sur le binaire valide

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

A generaliser/ajouter:
- politique de completude/prefill administrative par organisme;
- selection du template/profile dans le router commun;
- action/revue frontend actuellement nommees CNSS;
- profil overlay CNOPS lie au SHA exact.

## Invariants fail-closed CNOPS

- Aucun champ assure/beneficiaire inconnu n'est invente.
- Aucun lien assure-beneficiaire n'est infere silencieusement.
- Aucun INPE/IF/ICE n'est deduit depuis un champ non explicitement identifie.
- Aucune signature, aucun cachet, aucune decision assureur n'est genere.
- Le trust `CABINET_VALIDATED_BINARY` ne vaut que pour le SHA exact ci-dessus.
- Un profil overlay n'est utilisable que pour `organization + version + SHA-256` exacts.
- Toute divergence Honoraires/Acte/NGAP/template apres validation invalide la finalisation.
- CNSS existant doit rester strictement non-regresse.

## Human gate binaire — PASSE

Gate passe le 2026-09-16 par confirmation explicite du praticien/cabinet pour le SHA-256 exact `89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505`.

Le registre code promeut maintenant la definition `CNOPS_DENTAL_CABINET_2026_09_16` en `CABINET_VALIDATED_BINARY`. Cela n'est pas encore une activation runtime complete: le store immuable doit contenir CE binaire exact avec manifeste/validateur, puis le profil overlay et les gates metier doivent etre prouves.

## Next exact

1. verrouiller/store le binaire exact avec le SHA valide et l'identite du validateur;
2. definir la politique administrative CNOPS fail-closed;
3. calibrer un profil overlay uniquement sur CE SHA, sans coordonnees signature/cachet/assureur;
4. ajouter tests backend de hash, capacite lignes, champs interdits et non-regression CNSS;
5. effectuer le protocole UI obligatoire `BEFORE -> Goal -> mockup/reference -> implementation -> AFTER memes viewports -> comparaison/tests -> score visuel -> validation humaine`;
6. certifier l'exact HEAD avant closeout.
