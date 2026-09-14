# Audit anti-doublon — Digital Crown → Mutuelles dentaires

Baseline : `master` @ `5e1802901301a36fa4acf3d34adbfbde84258c18`.
Portée : lecture de la roadmap Document Studio et des audits canoniques P1/P4 présents sur cette baseline. Aucun runtime ni migration DB exécuté dans ce lot.

## Résultat
Le futur moteur mutuelle ne doit créer ni un second moteur d’honoraires, ni une seconde ordonnance. Ces deux domaines existent déjà et produisent des documents archivables.

| Domaine existant | Preuve repo | Données/flux vérifiés | Décision future |
|---|---|---|---|
| Ordonnance | `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md` + `DOCUMENT_STUDIO_ROADMAP.md` | saisie médicament/examen, dosage, forme, posologie, contexte patient, génération `/documents/generate`, PDF, archive | REUSE : joindre/référencer l’ordonnance existante si le formulaire assureur l’exige |
| Note d’honoraires | `docs/audits/DOCUMENT_STUDIO_P4_HONORAIRES_AUDIT.md` + `DOCUMENT_STUDIO_ROADMAP.md` | `DocumentHub → AccountingStudio → AccountingStudioLegacy → useAccountingStore → useDocumentGenerator → /documents/generate → HonorairesData → create_note_honoraires() → archive → persist_honoraires_lines() → Acte / Payment` | REUSE : source financière canonique pour lignes, montants et statut |
| Actes / dents | audit P4 | chaque ligne Honoraires doit porter un acte, montant et dent(s) structurées si applicable ; persistance vers `Acte` | REUSE : source du mapping acte/dent → NGAP |
| Paiements | audit P4 | `Payment` lié à `Acte`, statut financier, méthode explicite si encaissé | NE PAS recopier dans la feuille de soins ; seulement exposer les champs nécessaires |
| PDF / archive | audits P1/P4 | génération documentaire existante via `/documents/generate`, preview/print/archive | REUSE infrastructure, mais renderer assureur distinct par template officiel |

## Points explicitement non prouvés dans ce lot
Les audits fonctionnels nomment les modules et les contrats ci-dessus, mais ce lot n’affirme pas encore les chemins source exacts de tous les modèles Patient/Cabinet/Acte, ni la présence exhaustive de tous les identifiants administratifs nécessaires (INPE, ICE, IF, affiliation, CIN, etc.). Ces champs devront être verrouillés avant implémentation par inspection des schémas actuels.

Aucune occurrence dédiée CNOPS/CNSS/NGAP n’a été trouvée dans la recherche indexée réalisée pendant l’audit. Cette absence de résultat n’est pas considérée comme une preuve absolue d’absence de code.

## Réutilisation obligatoire
Le futur adaptateur doit lire un snapshot cohérent des domaines existants :

```text
Patient
Cabinet / praticien
Acte + dent(s)
Note Honoraires
Ordonnance éventuelle
        ↓
InsuranceSubmissionDraft (lecture/adaptation uniquement)
```

Il est interdit de créer une table parallèle `MutuelleHonoraires`, une ordonnance bis, un catalogue d’actes indépendant ou un second solde patient pour satisfaire le formulaire.

## Gaps à verrouiller avant code
1. Identité patient/ayant droit : CIN, date de naissance, sexe, lien avec assuré, numéro d’affiliation/immatriculation selon organisme.
2. Identité praticien/cabinet : INPE, nom, adresse, téléphone, IF/ICE quand exigés.
3. Dents : convention de numérotation et export déterministe vers la représentation du formulaire.
4. Actes : identifiant métier stable permettant le mapping NGAP sans dépendre d’un libellé libre fragile.
5. Signature/cachet : support réel et politique d’usage ; aucune génération artificielle.
6. Ordonnance FAR : rattachement au document P1 existant plutôt que duplication de lignes.
7. Version de formulaire : métadonnées `template_version`, `source_url`, `source_hash`, `verified_at`, `field_map`, `rules`.

## Gate anti-doublon
Avant tout code mutuelle, une inspection source ciblée doit confirmer pour chaque champ : chemin modèle, type, nullabilité, source de vérité et comportement d’archive. Toute donnée déjà canonique est lue ; elle n’est pas recréée.