# Mutuelles dentaires — préparation isolée

Statut : RESEARCH ONLY — aucune intégration applicative.
Date : 2026-09-14.
Baseline auditée : `master` @ `5e1802901301a36fa4acf3d34adbfbde84258c18`.

## Goal
Préparer l’automatisation future des feuilles de soins dentaires CNOPS, CNSS et Mutuelle des FAR en réutilisant les données déjà présentes dans Digital Crown, sans dupliquer les domaines Patient, Actes, Honoraires ou Ordonnance.

## Succès de ce lot
- audit anti-doublon documenté ;
- matrice de champs assureur documentée ;
- politique NGAP déterministe et versionnée documentée ;
- sources primaires/secondaires classées ;
- référence CNSS `610-1-04` validée métier le 2026-09-14 comme formulaire effectivement utilisé au cabinet ;
- aucun fichier runtime, route, dépendance, modèle DB ou UI modifié.

## Architecture cible — non implémentée

```text
Patient / Cabinet / Actes / Honoraires / Ordonnance existants
                    ↓
              adapter / extractor
                    ↓
          InsuranceSubmissionDraft
                    ↓
       mapping NGAP déterministe versionné
                    ↓
          renderer template assureur
             ↙        ↓        ↘
          CNOPS      CNSS      FAR
```

Principe : `InsuranceSubmissionDraft` est un DTO/adaptateur de sortie. Il ne devient pas une seconde source de vérité clinique ou financière.

## Statuts de champ prévus
- `AUTO` : fait déjà présent en base/dossier.
- `DERIVED_NGAP` : calcul/mapping déterministe depuis un acte existant.
- `MANUAL_REQUIRED` : donnée que le praticien doit saisir/confirmer.
- `INSURER_ONLY` : champ réservé à l’organisme gestionnaire.
- `SIGNATURE_REQUIRED` : signature/cachet réel requis, jamais simulé automatiquement.
- `UNSUPPORTED` : absent ou non fiabilisé dans Digital Crown.

## Garde-fous
1. Aucun code NGAP n’est deviné silencieusement.
2. Toute ambiguïté de mapping bloque l’auto-remplissage du code concerné et demande validation praticien.
3. Aucun cachet, signature, accord préalable ou décision assureur n’est fabriqué.
4. CNSS : `610-1-04` est désormais `VERIFIED_CABINET_REFERENCE`, mais le binaire officiel courant reste à verrouiller avant activation applicative.
5. FAR : le PDF/formulaire reste NON CANONIQUE tant qu’une version officielle actuelle n’est pas verrouillée depuis une source primaire.
6. Les données Honoraires et Ordonnance devront être lues depuis les sous-systèmes existants, jamais recopiées dans un second moteur.

## Fichiers de ce pack
- `EXISTING_APP_AUDIT.md` : réutilisation de l’existant et gaps.
- `FIELD_MATRIX.md` : champs CNOPS/CNSS/FAR et provenance future.
- `SOURCES.md` : sources et niveau de confiance.
- `NGAP_POLICY.md` : gouvernance du référentiel et du mapping.

## Gate avant toute intégration
Le chantier d’intégration ne doit démarrer qu’après : verrouillage du formulaire officiel courant pour chaque organisme, hash/version du template, audit exact des champs Patient/Cabinet/Actes, et table NGAP/TNR validée à partir de sources ONMD/ANAM.

CNSS `610-1-04` a franchi le gate métier/visuel cabinet, mais pas encore le gate `VERIFIED_PRIMARY`.