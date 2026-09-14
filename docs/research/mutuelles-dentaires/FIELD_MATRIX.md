# Matrice de champs — CNOPS / CNSS / Mutuelle FAR

Statut : préparation fonctionnelle. Aucun formulaire n’est rendu par l’application dans ce lot.

Légende : `AUTO`, `PATIENT_OPTIONAL`, `DERIVED_NGAP`, `MANUAL_REQUIRED`, `INSURER_ONLY`, `SIGNATURE_REQUIRED`, `UNSUPPORTED`.

| Bloc | Champ | CNOPS | CNSS | FAR | Source Digital Crown cible / statut |
|---|---|---:|---:|---:|---|
| Assuré | nom/prénom | requis | requis | requis | Patient ; `AUTO` si assuré = patient, sinon donnée assurance optionnelle |
| Assuré | n° affiliation / immatriculation / compte | requis selon organisme | requis | requis | nouveau champ administratif `PATIENT_OPTIONAL`; visible seulement si assurance activée |
| Assuré | CIN | présent dans les formulaires observés | présent dans modèle cabinet validé | présent dans copie observée | nouveau champ `PATIENT_OPTIONAL`; jamais requis pour créer un patient |
| Bénéficiaire | nom/prénom | oui si différent | oui | oui | Patient ; `AUTO` |
| Bénéficiaire | date de naissance | oui | oui | oui | Patient ; `AUTO` |
| Bénéficiaire | sexe | selon template | oui | oui | Patient ; `AUTO` |
| Bénéficiaire | qualité/lien avec assuré | selon template | selon template | oui | `PATIENT_OPTIONAL`, activé avec données mutuelle |
| Praticien | nom / cabinet | oui | oui | oui | `CabinetConfig` ; `AUTO` |
| Praticien | INPE | oui | oui | oui dans copie observée | `CabinetConfig.inpe` ; `AUTO` si renseigné |
| Praticien | cachet/signature | oui | oui | oui | `SIGNATURE_REQUIRED`, jamais simulé |
| Soins | date de soins | oui | oui | oui | Acte ; `AUTO` |
| Soins | dent/position | oui | oui | oui | source structurée à tracer avant implémentation |
| Soins | nature/libellé acte | oui | oui | oui | Acte ; `AUTO` |
| Soins | code/cotation NGAP | oui | oui | coefficient/cotation selon copie | `DERIVED_NGAP` si mapping univoque, sinon `MANUAL_REQUIRED` |
| Soins | honoraires | oui | oui | oui | Note Honoraires ; `AUTO` |
| Dentaire | schéma/odontogramme | demandé selon feuille | modèle cabinet observé | à confirmer | dérivation depuis dents structurées, pas depuis image libre |
| Pièces | note d’honoraires | demandée dans cas CNOPS documentés | à confirmer | à confirmer | réutiliser P4 |
| Pièces | ordonnance | si prescription / contexte indiqué | selon dossier | page ordonnance présente dans copie FAR | réutiliser P1, jamais ordonnance bis |
| Pièces | radiographies | certains actes/cas | selon actes/règles | à confirmer | pièce existante si disponible, sinon manuel |
| Accord | entente/accord préalable | certains actes | ODF et autres cas selon règles | à confirmer | `MANUAL_REQUIRED` / `INSURER_ONLY`; aucun accord auto-fabriqué |
| Organisme | décision, cachet, n° dossier interne | oui selon template | oui selon template | oui selon template | `INSURER_ONLY` |

## UX des données assurance patient
Principe verrouillé : le formulaire patient standard reste léger.

- `assurance` peut rester un choix simple existant.
- CIN, affiliation/immatriculation, qualité assuré/ayant-droit et informations analogues sont **optionnelles**.
- Ces champs ne sont pas affichés automatiquement à chaque création/édition de patient.
- Ils deviennent visibles via une action dédiée du type « Informations mutuelle / assurance » ou lorsqu’une feuille de soins doit être préparée.
- Une donnée absente reste vide ; elle ne bloque pas le dossier patient général.
- Une fois renseignée, elle devient réutilisable automatiquement pour les prochains formulaires du même patient.

## Règles d’auto-remplissage futures
1. Un champ `AUTO` n’est rempli que si sa source canonique existe réellement et passe les validations de type/nullabilité.
2. `PATIENT_OPTIONAL` signifie : stockage patient autorisé mais facultatif, absent du formulaire standard par défaut et jamais backfillé artificiellement.
3. Un champ administratif manquant ne doit jamais être inventé depuis le nom, téléphone ou autre heuristique.
4. `DERIVED_NGAP` nécessite une correspondance versionnée acte → code/cotation avec provenance primaire.
5. Si plusieurs codes sont plausibles, afficher l’ambiguïté au praticien et laisser le champ en attente.
6. Les champs `INSURER_ONLY` restent vierges dans le document produit par le cabinet.
7. Une signature/cachet exige une fonctionnalité explicitement autorisée et une empreinte réelle ; aucune image générique automatique.

## Compatibilité patients historiques
Toute future évolution du schéma Patient est additive : nouveaux champs nullable/optionnels uniquement, aucune suppression/renommage destructif, aucun backfill obligatoire. Les dossiers patients déjà présents doivent rester lisibles et éditables sans fournir ces nouvelles informations.

## Statut des templates
- CNOPS : exigences fonctionnelles étayées par source officielle CNOPS ; template exact à hasher avant renderer.
- CNSS : référence `610-1-04` validée métier comme modèle utilisé au cabinet ; binaire officiel courant encore à verrouiller avant activation applicative.
- FAR : portail officiel identifié mais formulaire courant non récupéré depuis une source primaire ; copie publique informative tant que non validée métier/primary.
