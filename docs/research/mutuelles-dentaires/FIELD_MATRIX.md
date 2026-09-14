# Matrice de champs — CNOPS / CNSS / Mutuelle FAR

Statut : préparation fonctionnelle. Aucun formulaire n’est rendu par l’application dans ce lot.

Légende : `AUTO`, `PATIENT_OPTIONAL`, `DERIVED_NGAP`, `MANUAL_REQUIRED`, `INSURER_ONLY`, `SIGNATURE_REQUIRED`, `UNSUPPORTED`.

| Bloc | Champ | CNOPS | CNSS | FAR | Source Digital Crown cible / statut |
|---|---|---:|---:|---:|---|
| Assuré | nom/prénom | requis | requis | requis | Patient ; `AUTO` si assuré = patient, sinon donnée assurance optionnelle |
| Assuré | n° affiliation / immatriculation / compte | requis selon organisme | requis | requis | `PATIENT_OPTIONAL` ; visible seulement si assurance activée |
| Assuré | CIN | présent | présent dans modèle cabinet validé | présent dans copie observée | `PATIENT_OPTIONAL` ; jamais requis pour créer un patient |
| Bénéficiaire | nom/prénom | oui si différent | oui | oui | Patient ; `AUTO` |
| Bénéficiaire | date de naissance | oui | oui | oui | Patient ; `AUTO` |
| Bénéficiaire | sexe | selon template | oui | oui | Patient ; `AUTO` |
| Bénéficiaire | qualité/lien avec assuré | selon template | selon template | oui | `PATIENT_OPTIONAL` |
| Praticien | nom / cabinet | oui | oui | oui | `CabinetConfig` ; `AUTO` |
| Praticien | INPE | oui | oui | oui dans copie observée | `CabinetConfig.inpe` ; `AUTO` si renseigné |
| Praticien | cachet/signature | oui | oui | oui | `SIGNATURE_REQUIRED` |
| Soins | date de soins | oui | oui | oui | ligne Honoraires / Acte ; `AUTO` |
| Soins | dent/position | oui | oui | oui | `DocumentArchive.clinical_data.payments[*].dent/dents` ; `AUTO` si présent |
| Soins | nature/libellé acte | oui | oui | oui | ligne Honoraires + Acte ; `AUTO` |
| Soins | code/cotation NGAP | oui | oui | coefficient/cotation selon copie | `DERIVED_NGAP` uniquement après lien stable vers référentiel typé/versionné |
| Soins | honoraires | oui | oui | oui | Note Honoraires ; `AUTO` |
| Dentaire | schéma/odontogramme | selon feuille | modèle cabinet observé | à confirmer | dériver des dents FDI structurées du snapshot, jamais d’un libellé/image libre |
| Pièces | note d’honoraires | selon dossier | à confirmer | à confirmer | réutiliser P4 |
| Pièces | ordonnance | si prescription | selon dossier | page ordonnance présente dans copie FAR | réutiliser P1 |
| Pièces | radiographies | certains actes/cas | selon actes/règles | à confirmer | pièce existante si disponible, sinon manuel |
| Accord | entente/accord préalable | certains actes | ODF/autres cas | à confirmer | `MANUAL_REQUIRED` / `INSURER_ONLY` |
| Organisme | décision, cachet, n° dossier interne | selon template | selon template | selon template | `INSURER_ONLY` |

## Source des dents — vérifiée
Le contrat `PaymentItem` utilisé par Honoraires possède `dent` et `dents`. Le payload complet `req.data` est conservé dans `DocumentArchive.clinical_data` lors de l’archivage.

Pour une feuille de soins générée à partir d’une note Honoraires existante, la source actuelle est donc :

```text
DocumentArchive.clinical_data.payments[*].dent / dents
```

Le miroir SQL `Acte` ne possède pas ces champs. Il ne faut donc pas tenter de les relire depuis `Acte` ni les déduire du libellé.

La convention FDI est déjà validée dans le contrat Devis : adulte 11–48 par quadrants et temporaire 51–85 par quadrants.

## Gap NGAP précis
`CatalogAct` existe déjà et possède un champ `code`, mais ce champ est explicitement « NGAP ou interne ». L’`Acte` dérivé d’Honoraires ne possède ni `catalog_act_id` ni snapshot de code catalogue.

Donc :
- aucun mapping automatique NGAP par simple égalité de libellé ;
- aucun usage aveugle de `CatalogAct.code` comme NGAP ;
- futur mapping seulement après liaison stable + type/provenance/version du code.

## UX des données assurance patient
Le formulaire Patient standard reste léger : CIN, affiliation, qualité assuré/ayant-droit et informations analogues sont optionnelles, masquées par défaut et révélées uniquement dans le contexte assurance/mutuelle. Une donnée absente ne bloque jamais le dossier général.

## Règles d’auto-remplissage
1. `AUTO` uniquement depuis une source canonique réellement présente.
2. `PATIENT_OPTIONAL` = facultatif, masqué par défaut, aucun backfill artificiel.
3. Aucun champ administratif inventé.
4. `DERIVED_NGAP` exige mapping versionné, univoque et traçable.
5. Ambiguïté = validation praticien obligatoire.
6. `INSURER_ONLY` reste vierge côté cabinet.
7. Signature/cachet réel uniquement.

## Compatibilité patients historiques
Toute évolution future du schéma Patient est additive : nouveaux champs nullable/optionnels uniquement, aucune suppression/renommage destructif, aucun backfill obligatoire.

## Statut templates
- CNOPS : exigences fonctionnelles étayées institutionnellement ; template exact à verrouiller/hash.
- CNSS : `610-1-04` validé métier comme modèle utilisé au cabinet ; primaire courant encore à verrouiller avant activation.
- FAR : copie publique informative, validation métier exacte encore requise.
