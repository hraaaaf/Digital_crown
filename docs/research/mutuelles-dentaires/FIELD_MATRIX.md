# Matrice de champs — CNOPS / CNSS / Mutuelle FAR

Statut : préparation fonctionnelle. Aucun formulaire n’est rendu par l’application dans ce lot.

Légende : `AUTO`, `DERIVED_NGAP`, `MANUAL_REQUIRED`, `INSURER_ONLY`, `SIGNATURE_REQUIRED`, `UNSUPPORTED`.

| Bloc | Champ | CNOPS | CNSS | FAR | Source Digital Crown cible / statut |
|---|---|---:|---:|---:|---|
| Assuré | nom/prénom | requis | requis | requis | Patient/assurance à auditer ; `AUTO` si présent |
| Assuré | n° affiliation / immatriculation / compte | requis selon organisme | requis | requis | champ assurance à verrouiller ; sinon `MANUAL_REQUIRED` |
| Assuré | CIN | présent dans les formulaires observés | présent dans les copies observées | présent dans copie observée | Patient à auditer |
| Bénéficiaire | nom/prénom | oui si différent | oui | oui | Patient ; `AUTO` |
| Bénéficiaire | date de naissance | oui | oui | oui | Patient ; `AUTO` si renseignée |
| Bénéficiaire | sexe / lien avec assuré | selon template | selon template | oui | assurance patient à auditer |
| Praticien | nom / cabinet | oui | oui | oui | profil cabinet à auditer |
| Praticien | INPE | oui | oui dans sources secondaires | oui dans copie observée | profil praticien ; `AUTO` seulement si valeur réellement stockée |
| Praticien | cachet/signature | oui | oui | oui | `SIGNATURE_REQUIRED`, jamais simulé |
| Soins | date de soins | oui | oui | oui | Acte ; `AUTO` |
| Soins | dent/position | oui | oui | oui | Acte/dent ; `AUTO` après vérification convention |
| Soins | nature/libellé acte | oui | oui | oui | Acte ; `AUTO` |
| Soins | code/cotation NGAP | oui | oui | coefficient/cotation selon copie | `DERIVED_NGAP` si mapping univoque, sinon `MANUAL_REQUIRED` |
| Soins | honoraires | oui | oui | oui | Note Honoraires ; `AUTO` |
| Dentaire | schéma/odontogramme | demandé selon feuille | copie CNSS observée | à confirmer | dérivation depuis dents structurées, pas depuis image libre |
| Pièces | note d’honoraires | demandée dans cas CNOPS documentés | à confirmer sur officiel courant | à confirmer | réutiliser P4 |
| Pièces | ordonnance | si prescription / contexte indiqué | selon dossier | page ordonnance présente dans copie FAR | réutiliser P1, jamais ordonnance bis |
| Pièces | radiographies | certains actes/cas | selon actes/règles | à confirmer | pièce existante si disponible, sinon manuel |
| Accord | entente/accord préalable | certains actes | ODF et autres cas selon règles | à confirmer | `MANUAL_REQUIRED` / `INSURER_ONLY`; aucun accord auto-fabriqué |
| Organisme | décision, cachet, n° dossier interne | oui selon template | oui selon template | oui selon template | `INSURER_ONLY` |

## Règles d’auto-remplissage futures
1. Un champ `AUTO` n’est rempli que si sa source canonique existe réellement et passe les validations de type/nullabilité.
2. Un champ administratif manquant ne doit jamais être inventé depuis le nom, téléphone ou autre heuristique.
3. `DERIVED_NGAP` nécessite une correspondance versionnée acte → code/cotation avec provenance primaire.
4. Si plusieurs codes sont plausibles, afficher l’ambiguïté au praticien et laisser le champ en attente.
5. Les champs `INSURER_ONLY` restent vierges dans le document produit par le cabinet.
6. Une signature/cachet exige une fonctionnalité explicitement autorisée et une empreinte réelle ; aucune image générique automatique.

## Statut des templates
- CNOPS : exigences fonctionnelles étayées par source officielle CNOPS ; template exact à hasher avant renderer.
- CNSS : copie publique plausible identifiée, mais formulaire officiel courant non verrouillé ; NON CANONIQUE.
- FAR : portail officiel identifié mais formulaire courant non récupéré ; copie publique informative uniquement ; NON CANONIQUE.