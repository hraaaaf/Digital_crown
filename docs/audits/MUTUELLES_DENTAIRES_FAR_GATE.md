# Mutuelles dentaires — FAR source/template gate

Date: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Base inspectée: `master@4cffca14b025785b9d2da8b4c13251c7d74e69c0`
Branche: `audit/mutuelles-far-source-gate-20260916`
Référence de reprise: `docs/audits/MUTUELLES_DENTAIRES_FAR_START_PROMPT.md`

## Goal

Établir le gate FAR **avant toute implémentation** : identifier le binaire exact utilisé/accepté par le cabinet, verrouiller sa provenance et son SHA-256, inspecter sa géométrie et ses champs, confirmer le rôle exact de chaque page — notamment l'ordonnance — puis seulement décider du contrat de mapping/rendu.

## Succès observable

Le passage en `GO_IMPLEMENTATION` exige simultanément :

- binaire FAR exact disponible sous forme d'octets PDF ;
- provenance documentée ;
- validation explicite cabinet/praticien si la provenance n'est pas `OFFICIAL_PRIMARY` ;
- SHA-256 calculé sur ces octets exacts ;
- taille, nombre de pages, dimensions et orientations inspectés ;
- présence/absence d'AcroForm et XFA inspectée ;
- rôle de chaque page confirmé sur **ce binaire exact** ;
- page/zone ordonnance identifiée sans ambiguïté ;
- stratégie `provider_fields` / `coordinate_overlay` / mixte justifiée ;
- contrat ordonnance séparé et fail-closed ;
- aucune molécule, dose ou posologie déduite des actes, Honoraires ou NGAP.

## 1. État du moteur existant — VÉRIFIÉ

Le moteur réel est Python sous `backend/...`.

Briques inspectées sur la base exacte :

- `backend/services/insurance_template_registry.py` ;
- `backend/services/insurance_source_store.py` ;
- `backend/services/insurance_pdf_overlay.py` ;
- `backend/services/insurance_preparation.py` ;
- `backend/services/insurance_validation.py` ;
- `backend/schemas/insurance_submission.py` ;
- profil CNOPS de référence `backend/services/insurance_cnops_dental_profile.py` ;
- tests de source store `backend/tests/test_insurance_source_store.py`.

Contrat commun confirmé :

`Honoraires -> draft -> NGAP explicite -> revue praticien -> source template hash-lockée -> validation -> overlay hash-bound -> PDF final -> DocumentArchive`

Le renderer générique refuse les champs signature/cachet/décision assureur et lie chaque profil à `organization + template_version + template_hash`.

## 2. Entrée FAR préexistante — PLACEHOLDER, PAS PREUVE

Le registre contient déjà :

- organisation `FAR` ;
- version `FAR-2021-1` ;
- label `Feuille de Mutuelle FAR 2021-1` ;
- trust déclaré `CABINET_VALIDATED_BINARY` ;
- `expected_page_count=None`.

Cette entrée a été introduite lors de la fondation Mutuelles (PR #493), **sans binaire FAR hash-locké documenté dans ce gate**.

Elle ne vaut donc pas validation du formulaire FAR actuel.

Le source store impose par ailleurs une identité de validateur pour tout binaire `CABINET_VALIDATED_BINARY`, et la validation serveur actuelle ne possède une politique administrative finale que pour CNSS et CNOPS : FAR tombe explicitement sur `Administrative validation policy is not yet implemented for this insurer`.

Conclusion : le système reste fail-closed pour FAR malgré ce placeholder historique.

## 3. Recherche du binaire exact — RÉSULTAT

### Repo / Drive / File Library

Recherches effectuées sur :

- arbre Git/master et historique Mutuelles ;
- Google Drive connecté ;
- File Library ChatGPT.

Aucun binaire FAR exact, aucun SHA-256 FAR, aucun manifeste de source FAR et aucun fichier ordonnance FAR cabinet-validé n'ont été retrouvés.

### Sources publiques secondaires

Plusieurs copies publiques secondaires concordantes ont été localisées, notamment :

- Scribd — `Feuille de Mutuelle FAR 2021-1` ;
- Scribd — `FAR-Recto-Verso` / `Feuille de soins Mutuelle FAR` ;
- Scribd — `Feuille de maladie - Mutuelle des FAR` ;
- Studocu — `Feuille de Soins Dentaire (INPE) - Mutuelle des FAR`.

Les aperçus textuels montrent des libellés logiques `Page 1`, `ORDONNANCE ... Page 2`, `Page 3` et `Page 4 SOINS ET PROTHESE DENTAIRE`, tandis que certaines plateformes annoncent seulement `2 pages` de fichier. Cette discordance empêche toute conversion fiable en index PDF, géométrie ou coordonnées.

Ces copies sont utiles comme **références secondaires de comparaison uniquement**. Elles ne fournissent pas la preuve du binaire exact utilisé par le cabinet et ne doivent pas être promues en `OFFICIAL_PRIMARY` ou `CABINET_VALIDATED_BINARY` sans validation explicite des octets exacts.

## 4. Géométrie / champs PDF — NON ACQUIS

Faute du binaire exact, les éléments suivants restent `UNKNOWN` :

- taille exacte du fichier ;
- SHA-256 ;
- nombre réel de pages PDF ;
- correspondance page logique <-> index PDF ;
- dimensions et orientation de chaque page ;
- présence/absence d'AcroForm ;
- présence/absence d'XFA ;
- champs fournisseurs éventuels ;
- coordonnées d'overlay ;
- capacité exacte de lignes dentaires.

Aucune coordonnée FAR n'est autorisée avant acquisition et inspection du PDF exact.

## 5. Contrat ordonnance FAR — VERROUILLÉ AU NIVEAU PRODUIT

Contrainte cabinet héritée du handover : le dossier FAR contient une ordonnance et elle doit être traitée séparément des pages administratives/soins.

Le schéma commun possède déjà `source_ordonnance_document_id`, ce qui permet de lier explicitement un document ordonnance sans le fabriquer depuis les lignes de soins.

Contrat clinique pour FAR :

1. l'ordonnance est une surface clinique distincte ;
2. les données de prescription proviennent uniquement d'une action/document de prescription explicite du praticien ;
3. les actes, dents, coefficients NGAP, montants ou catégories administratives ne peuvent jamais générer une molécule, un dosage, une posologie, une durée ou une fréquence ;
4. aucune prescription implicite n'est créée si la source ordonnance manque ;
5. la page ordonnance du template FAR ne sera reliée à un index PDF qu'après inspection du binaire exact ;
6. signature/cachet du praticien restent hors auto-génération, sauf mécanisme explicite séparé ultérieurement validé.

Ce contrat est indépendant de la future stratégie d'overlay et reste applicable même si l'ordonnance est physiquement incluse dans le même fichier PDF FAR.

## 6. Mapping/rendu — DÉCISION DIFFÉRÉE

`provider_fields` : NON DÉMONTRÉ.

`coordinate_overlay` : NON DÉMONTRÉ.

Mode mixte : NON DÉMONTRÉ.

Le choix sera fait uniquement après introspection native du binaire exact. Si aucun champ PDF exploitable n'existe, un overlay pourra être calibré comme CNSS/CNOPS, mais uniquement avec :

- hash exact ;
- coordonnées mesurées sur ce hash ;
- exclusions explicites signature/cachet/contrôle mutuelle ;
- capacité de lignes fail-closed ;
- rendu témoin ;
- preuve visuelle BEFORE/AFTER aux mêmes viewports/renders ;
- tests de mismatch hash/page/capacité.

## 7. Gate clinique et sécurité

Interdits maintenus :

- déduire une prescription depuis NGAP/Honoraires/Acte ;
- réutiliser les coordonnées CNSS/CNOPS ;
- considérer `FAR-2021-1` comme validé parce que le symbole existe dans le registre ;
- inventer pagination, dimensions, champs ou coordonnées ;
- promouvoir une copie publique secondaire en source officielle ;
- auto-remplir signature, cachet, visa, accord ou décision de la Mutuelle FAR ;
- coder le profil FAR avant verrouillage du binaire exact.

## 8. Verdict

`NO_GO_IMPLEMENTATION_SOURCE_BINARY_REQUIRED`

Le gate source/template est documenté, mais **l'implémentation FAR ne doit pas commencer** tant que le binaire exact cabinet n'est pas fourni/acquis et validé.

### Human gate exact

Fournir le PDF FAR exact actuellement utilisé/accepté par le cabinet, idéalement le fichier original non recompressé.

Dès réception, la séquence autorisée est :

`SHA-256 -> introspection PDF native -> rôle de chaque page -> confirmation ordonnance -> validation cabinet -> stratégie mapping -> mise à jour de ce gate en GO/NO-GO -> seulement ensuite code`

## Score actuel

EXECUTION_SCORE: 7.9/10
ADVERSARIAL_SCORE: 7.9/10
Score retenu: 7.9/10.

Plafond volontaire : la preuve binaire requise par le gate est absente. Aucun score >= 9.0 et aucun statut `VERIFIED` ne sont revendiqués tant que cette preuve manque.

## Statut

`FAR_SOURCE_GATE_BLOCKED_ON_EXACT_BINARY`

## Next exact

Acquérir le PDF FAR exact du cabinet, puis calculer son SHA-256 et inspecter nativement ses pages/champs avant toute modification applicative.
