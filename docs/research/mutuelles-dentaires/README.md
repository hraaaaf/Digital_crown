# Mutuelles dentaires — préparation isolée

Statut : RESEARCH ONLY — aucune intégration applicative.
Date : 2026-09-14.
Baseline auditée initiale : `master` @ `5e1802901301a36fa4acf3d34adbfbde84258c18`.
Master observé au handover : `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc` (ne jamais supposer qu'il est encore HEAD à la reprise).

## Goal
Préparer l’automatisation future des feuilles de soins dentaires CNOPS, CNSS et Mutuelle des FAR en réutilisant les données déjà présentes dans Digital Crown, sans dupliquer Patient, Actes, Honoraires, Ordonnance ou catalogue d’actes et sans mettre en risque la base existante.

## Résultats vérifiés du lot
- audit anti-doublon documenté ;
- CNSS `610-1-04` validé métier comme formulaire utilisé au cabinet ;
- FAR `Feuille de Mutuelle FAR 2021-1` validée métier par le praticien comme référence visuelle cabinet ;
- CNOPS : page institutionnelle identifiée avec feuille de soins dentaires ; binaire exact encore à hasher ;
- données assurance Patient futures : facultatives, activables et masquées par défaut ;
- DB future : évolution additive/rétrocompatible uniquement ;
- source actuelle des dents d’une note Honoraires verrouillée : `DocumentArchive.clinical_data.payments[*].dent/dents` ;
- convention FDI déjà présente dans le contrat documentaire ;
- `Acte` ne matérialise actuellement ni dent(s), ni `catalog_act_id` ;
- `CatalogAct.code` existe mais peut être NGAP ou interne ;
- aucun fichier runtime, route, modèle DB, dépendance ou UI modifié dans ce lot.

## Architecture cible — non implémentée
```text
Patient / Cabinet
DocumentArchive Honoraires + Actes / Payments
CatalogAct
Ordonnance existante
        ↓
adapter / extractor
        ↓
InsuranceSubmissionDraft
        ↓
mapping NGAP déterministe, typé, versionné
        ↓
renderer template assureur
   ↙        ↓        ↘
CNOPS      CNSS      FAR
```

`InsuranceSubmissionDraft` est un DTO/adaptateur de sortie, jamais une seconde source de vérité clinique ou financière.

## Règle dents
Pour une note Honoraires archivée, les dents sont déjà dans le snapshot documentaire (`clinical_data`). Le futur adaptateur doit les lire depuis cette source et ne jamais les reconstruire depuis le libellé de l’acte.

Le miroir `Acte` ne conserve pas actuellement `dent/dents`. La relation ligne-document ↔ Acte repose aujourd’hui sur le même `document_archive_id` et l’ordre des lignes. Avant intégration, il faudra décider si ce lien suffit ou si un identifiant de ligne stable additif est nécessaire.

## Règle NGAP
`CatalogAct` reste le catalogue unique. Aucun second catalogue NGAP ne doit être créé.

Avant automatisation :
- distinguer explicitement code interne / code NGAP ;
- versionner provenance et validité NGAP ;
- obtenir un lien stable ligne/Acte ↔ `CatalogAct` quand nécessaire ;
- conserver dans le document mutuelle la version et le code réellement utilisés.

Aucun fuzzy matching silencieux libellé→NGAP.

## Règle Patient / assurance
CIN, affiliation/immatriculation/compte, qualité assuré/ayant-droit et données analogues : facultatives, non affichées par défaut, activées seulement en contexte assurance/mutuelle, réutilisées si déjà renseignées, jamais inventées.

## Garde-fou DB — P0
Toute future intégration doit préserver la base cabinet : nouveaux champs uniquement additifs et nullable/optionnels, aucun backfill artificiel obligatoire, aucune suppression/renommage destructif.

Avant migration réelle sur une copie représentative : même nombre de patients, mêmes IDs, aucune valeur existante perdue/modifiée, anciens dossiers toujours lisibles/éditables, rollback testé.

## Garde-fous fonctionnels
1. Aucun code NGAP deviné silencieusement.
2. Ambiguïté = validation praticien.
3. Aucun cachet, signature, accord préalable ou décision assureur fabriqué.
4. CNSS `610-1-04` = `VERIFIED_CABINET_REFERENCE`, pas encore `VERIFIED_PRIMARY`.
5. FAR = `VERIFIED_CABINET_REFERENCE`, source primaire/binaire institutionnel encore à verrouiller.
6. CNOPS = `VERIFIED_INSTITUTIONAL_PAGE`, binaire exact/hash encore à verrouiller.
7. Honoraires et Ordonnance restent les sous-systèmes existants.
8. Aucune migration Patient dans ce lot.

## Fichiers canoniques de reprise
1. `README.md` — canonical principal / état synthétique.
2. `HANDOVER.md` — reprise nouvelle conversation, Next exact et séquence restante.
3. `VISUAL_REFERENCES.md` — références visuelles des trois organismes et statut de validation.
4. `EXISTING_APP_AUDIT.md` — audit exact, sources canoniques et gaps.
5. `FIELD_MATRIX.md` — champs CNOPS/CNSS/FAR et provenance.
6. `SOURCES.md` — sources et niveau de confiance.
7. `NGAP_POLICY.md` — gouvernance NGAP.

## Gate avant toute intégration
Restent à verrouiller : stratégie stable ligne Honoraires/Acte ↔ `CatalogAct`, typage/version/provenance NGAP, binaire/hash CNOPS, source primaire/hash CNSS et FAR si récupérables, signature/cachet, plan de migration additive testé sur copie DB.

Aucune intégration applicative ne doit commencer simplement parce que les références visuelles sont validées.
