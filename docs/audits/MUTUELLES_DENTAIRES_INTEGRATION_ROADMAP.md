# Mutuelles dentaires — Integration Roadmap

Date de realignement: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Branche du lot courant: `feature/mutuelles-cnops-20260916`
Base du lot courant: `master@d15d81d0c040a5e6b255e02e635c988cd6d720ee`
Lot precedent: PR `#493` MERGED

## Goal global

Integrer un workflow unique de feuille de soins CNSS/CNOPS/FAR a partir des donnees existantes Digital Crown, avec validation praticien, tracabilite NGAP, rendu sur template exact verrouille et archivage reproductible dans `DocumentArchive`, sans dupliquer Honoraires, `CatalogAct` ni l'archive documentaire.

UX cible:

`Patient -> Honoraires -> Preparer organisme -> Revue/validation -> PDF -> DocumentArchive`

## Architecture verrouillee

- un seul moteur Mutuelles;
- Honoraires reste la source financiere;
- `CatalogAct` reste le catalogue clinique;
- `ngap_catalog_mappings` reste la couche reglementaire versionnee;
- `DocumentArchive` reste l'archive documentaire;
- aucun fuzzy mapping NGAP;
- aucun backfill artificiel;
- aucune signature/cachet/decision assureur fabrique;
- toute donnee inconnue reste fail-closed;
- tout template finalisable doit etre lie a des octets exacts et a un SHA-256;
- tout profil overlay est lie a `organization + template_version + template_hash` exacts;
- reimpression historique depuis le snapshot/profil archive, jamais depuis un recalcul implicite courant.

## Moteur commun — ACQUIS

Les briques suivantes existent et doivent etre reutilisees pour CNOPS/FAR:

- `InsuranceSubmissionDraft`;
- preparation depuis Honoraires;
- coherence serveur Honoraires/Acte;
- liaison `source_line_uid` / `catalog_act_id`;
- resolution NGAP serveur sans fuzzy matching;
- source store local immuable et hash-addressed;
- validation praticien;
- revalidation anti-stale avant finalisation;
- renderer PDF overlay hash-bound;
- hash du PDF final;
- archivage `DocumentArchive` avec preuve de rendu.

`SECONDARY_REFERENCE` reste insuffisant pour une validation/finalisation praticien. Le trust final acceptable reste `OFFICIAL_PRIMARY` ou `CABINET_VALIDATED_BINARY` avec provenance explicite.

## NGAP dentaire — REFERENCE VERROUILLEE / RUNTIME NON AUTO-CERTIFIE

Fichiers canoniques:

- `backend/data/ngap_dental_177_06.json`
- `backend/data/ngap_dental_177_06_conditions.json`
- `backend/data/ngap_dental_177_06_provenance.json`
- `backend/services/ngap_dental_reference.py`
- `docs/audits/MUTUELLES_NGAP_DENTAL_REFERENCE.md`

Source verrouillee:

- B.O. n°5414 / arrete 177-06;
- fichier `bo_5414_fr.pdf`;
- 220 pages;
- 11 334 738 octets;
- SHA-256 `e9db137d6a758bd4ad7a506a94a7c0c84726813de3db1e225c761318a75e1fdb`.

Dataset actuel:

- 145 entrees;
- `D600-D641`;
- `D700-D785`;
- `D800-D816`.

Statut volontaire: `REFERENCE_ONLY_NOT_RUNTIME_CERTIFIED`.

Le dataset ne devient jamais automatiquement un mapping runtime `VERIFIED_PRIMARY`; les mappings `CatalogAct -> NGAP` restent soumis aux gates existants.

## CNSS 610-1-04 — MERGE #493 ACQUIS

Le lot CNSS a ete merge dans `master` via PR `#493`, merge commit `d15d81d0c040a5e6b255e02e635c988cd6d720ee`.

Binaire cabinet valide utilise par le profil CNSS:

- version `CNSS-610-1-04`;
- 2 pages;
- SHA-256 `e1fb63afb1893886d518135dfb209f24f2464e8cd664e89881fc7c373854864d`;
- trust `CABINET_VALIDATED_BINARY`.

Profil courant:

- `backend/services/insurance_cnss_610_1_04_profile.py`;
- version `cnss-610-1-04-e1fb63af-v2`;
- capacite 3 lignes;
- zone superieure reservee a l'assure volontairement non remplie;
- remplissage limite a la zone praticien/beneficiaire validee;
- aucune coordonnee signature/cachet/decision assureur.

UI CNSS acquise:

- action `Preparer CNSS` depuis Honoraires/Documents;
- revue praticien;
- validation;
- finalisation;
- archivage;
- captures AFTER exact-head realisees sur `390x844`, `768x1024`, `1280x900` et validation visuelle humaine acquise avant merge.

Certification pre-merge de reference:

- HEAD `f5c888166a6471a13fa7df67f6e43b17eb67574a`;
- CI `#4515`: SUCCESS;
- M6-I: SKIPPED attendu.

Post-merge `master@d15d81d0...`:

- CI `#4522` existe bien sur le merge commit;
- au controle du 2026-09-16 pendant l'ouverture du lot CNOPS, etat: `in_progress`, conclusion: aucune;
- ceci ne constitue pas encore une certification post-merge.

## CNOPS — LOT COURANT

Fichier de gate canonique du lot:

`docs/audits/MUTUELLES_DENTAIRES_CNOPS_GATE.md`

### Etat repo verifie

- `InsuranceOrganization`/types frontend supportent deja `CNOPS`;
- `insurance_template_registry.py` contient `CNOPS_DENTAL_PENDING`;
- definition actuelle: 2 pages attendues, trust `SECONDARY_REFERENCE`;
- le moteur de preparation/finalisation reste generique sous les couches CNSS;
- les seams encore CNSS-only sont principalement:
  - politique administrative;
  - selection template/profile du router;
  - action/revue frontend.

### Sources primaires CNOPS recroisees

Le site officiel CNOPS expose la `Feuille de soins dentaires` et documente les donnees exigees pour le dossier dentaire, notamment selon les cas: identite assure/malade, INPE, date, honoraires, dent(s), actes, schema dentaire, cotation NGAP, signature/cachet et pieces justificatives.

Sources officielles de decouverte/corroboration:

- `https://www.cnops.org.ma/fr/infopratiques`
- `https://www.cnops.org.ma/fr/soins-dentaires`
- `https://www.cnops.org.ma/fr/dossierem?r=117`
- `https://cnops.org.ma/fr/prestations?r=86`

Aucun binaire PDF officiel exact n'a ete recupere de facon reproductible dans l'environnement courant. Aucun hash `OFFICIAL_PRIMARY` n'est donc declare.

### Binaire candidat secondaire exact

Un candidat 2 pages a ete acquis depuis une copie secondaire Google Drive exposee par un site tiers:

- fichier: `Feuile de soins denatires CNOPS - ATARBAWI.COM.pdf`;
- taille: `1 325 493` octets;
- pages: 2;
- format: A4 paysage, `841.89 x 595.276 pt`;
- formulaire PDF: aucun;
- SHA-256: `89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505`;
- reference ANAM visible sur ce candidat: `1.1.01.01`;
- trust actuel obligatoire: `SECONDARY_REFERENCE`.

Aucune coordonnee overlay CNOPS n'est canonisee avant validation du binaire exact.

### Human gate courant

Le premier vrai gate du lot CNOPS est la validation du binaire exact.

Le candidat de SHA-256 `89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505` ne peut devenir `CABINET_VALIDATED_BINARY` qu'apres confirmation explicite du praticien/cabinet qu'il s'agit bien du formulaire CNOPS dentaire utilise/acceptable.

Si refuse, obtenir le PDF exact cabinet/officiel puis recalculer hash/provenance avant toute calibration.

## FAR — NON OUVERT DANS CE LOT

FAR reste hors scope de la branche CNOPS. Aucun travail CNOPS ne doit muter le comportement FAR sauf refactor generique strictement couvert par tests de non-regression.

## Protocole UI obligatoire

Pour toute modification visuelle CNOPS:

`BEFORE -> Goal ecrit -> mockup/reference -> implementation -> AFTER memes viewports -> comparaison/tests -> score visuel -> validation humaine si necessaire`.

Les viewports CNSS de reference `390x844 / 768x1024 / 1280x900` doivent etre conserves pour la comparaison lorsqu'ils s'appliquent au meme flow.

## Non-regression obligatoire

Toute modification CNOPS doit prouver proportionnellement au risque:

- aucun changement non maitrise de schema/DB;
- aucun dommage donnees patients/documents;
- CNSS prepare/validate/finalize/archive reste fonctionnel;
- source store/hash gates restent fail-closed;
- NGAP reste non fuzzy et non auto-certifie;
- signatures/cachets/decision assureur restent hors rendu automatique.

## Interdits

Second moteur Honoraires, second catalogue clinique, Ordonnance bis, fuzzy mapping, backfill artificiel, signature/cachet/accord assureur fabrique, template secondaire promu silencieusement en final, rendu approximatif d'un formulaire officiel, mutation production, deploiement Vercel sans autorisation explicite, merge sans accord explicite utilisateur.

## Etat courant

`PR_493_MERGED / CNSS_FLOW_ACQUIRED / NGAP_REFERENCE_LOCKED_REFERENCE_ONLY / CNOPS_BRANCH_CREATED / CNOPS_SECONDARY_BINARY_HASHED / CNOPS_OFFICIAL_BINARY_NOT_LOCKED / CNOPS_CABINET_BINARY_VALIDATION_PENDING / CNOPS_RUNTIME_NOT_ENABLED / POST_MERGE_CI_4522_IN_PROGRESS_AT_LAST_CHECK`

## Next exact

1. Gate humain: confirmer ou refuser le binaire CNOPS exact de SHA-256 `89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505`.
2. Si confirme: le promouvoir uniquement en `CABINET_VALIDATED_BINARY` avec identite du validateur, puis lock/store exact.
3. Implementer policy administrative CNOPS fail-closed + tests.
4. Calibrer profil overlay lie a CE SHA + tests des zones interdites/capacite lignes.
5. Generaliser le router/action/revue sans casser CNSS.
6. Executer BEFORE/Goal/mockup -> UI -> AFTER memes viewports -> comparaison/tests -> validation visuelle.
7. Certification exact-head + documentation/handover CNOPS -> FAR.
8. Demander accord merge; ne merger qu'apres accord.
9. Verifier post-merge; nouvelle fenetre pour FAR.
