# Prescription Pharmacology — Amoxicilline sévère + poids

Status: VALIDATED — PRE-MERGE

## Goal

Sécuriser l’adaptation de l’amoxicilline lorsqu’une infection dentaire sévère est explicitement structurée, en utilisant uniquement des données patient réelles et un contexte clinique structuré, sans inférence depuis du texte libre et sans auto-sélection d’un schéma thérapeutique lorsque les sources doivent être réconciliées.

## Contrat de sécurité

- `severeInfection` n’est consommé que via `DentalAbscessContext` explicite ;
- aucun texte libre n’est converti en sévérité clinique ;
- aucun poids n’est inventé ;
- une donnée pondérale requise mais absente échoue fermé ;
- une insuffisance rénale structurée bloque toute adaptation automatique ;
- les adolescents sont revus manuellement lorsque les référentiels d’âge et de poids doivent être réconciliés ;
- aucune valeur explicitement saisie par le praticien n’est écrasée ;
- le gate Maroc reste inchangé ;
- aucune nouvelle proposition thérapeutique n’est auto-adoptée sans preuve locale appropriée.

## Sources vérifiées

- SDCEP, Drug Prescribing for Dentistry — Amoxicillin / Dental abscess.
- SmPC amoxicilline eMC, utilisé comme cross-check produit pour âge, poids, sévérité et fonction rénale.

Les deux sources justifient un comportement fail-closed lorsque le contexte clinique ou patient est incomplet ou lorsqu’une réconciliation entre référentiels est nécessaire.

## Architecture

`PrescriptionAmoxicillinSevereSafety` est un gate post-arbitrage :

1. vérifie la molécule concernée ;
2. exige un contexte d’infection sévère explicitement structuré ;
3. conserve les blocages antérieurs ;
4. refuse toute adaptation automatique en cas d’insuffisance rénale structurée ;
5. exige le poids réel lorsque la règle source-backed en dépend ;
6. expose seulement des bornes de sécurité issues des sources, sans choisir automatiquement une dose ;
7. impose une revue praticien pour les contextes où les référentiels doivent être réconciliés ;
8. préserve les valeurs explicitement saisies par le praticien.

Le pipeline expose `dentalAbscessContext` comme paramètre explicite. Il n’est jamais construit depuis du texte clinique libre.

## Tests

9 scénarios couvrent : contexte non sévère inchangé, poids absent, borne pondérale, plafond absolu, insuffisance rénale, adolescent avec/sans poids, saisie explicite praticien et adulte sévère.

## UI/UX

Aucun changement visuel dans ce sous-lot. Aucun AFTER visuel requis.

## Proof

HEAD fonctionnel certifié : `58eadfaca959746b7853b248f003a04290fa6bfd`.

PR : #514.

Certifications exactes du HEAD fonctionnel :
- CI #4342 : SUCCESS ;
- Ordonnance Fidelity V3 Visual Certification #183 : SUCCESS ;
- Cabinet Upgrade PostgreSQL Certification #743 : SUCCESS ;
- Settings R11 TemplateBuilder Dependency Audit #752 : SUCCESS ;
- T2 Runtime Browser Certification #3228 : SUCCESS ;
- Patient P7 Final Certification #1658 : SUCCESS ;
- M6-I Biometric Passkey Certification #2028 : skipped attendu.

Revue statique : 5 fichiers, uniquement pharmacologie + documentation ; aucune DB ; aucun changement UI/UX ; aucun déploiement Vercel.

Post-merge du lot précédent : master `e1540b18342aeb9f1ae60e1da0295adf23b3f9ff`, CI #4338 SUCCESS.

Gate final : le commit documentaire de closeout doit être certifié avant passage en ready/merge.
