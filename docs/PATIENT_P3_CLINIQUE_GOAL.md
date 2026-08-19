# Patient P3 — Clinique

## Goal
Faire de l’espace Clinique le dossier clinique structuré du patient : données médicales visibles et sourcées, odontogramme persistant côté backend, examens séparés des conclusions, propositions distinguées des diagnostics retenus, et Master Plan traçable.

## Succès observable
1. Aucune donnée clinique autoritative n’est conservée uniquement dans `localStorage`.
2. L’odontogramme est chargé/sauvegardé via backend patient-scopé et permission `clinical`, avec erreur explicite en cas d’échec.
3. Les antécédents médicaux canoniques (`Patient.antecedents_medicaux`) sont visibles dans Clinique sans passer par un radar d’insights générique.
4. Les assistants restent des outils de collecte/proposition. Une proposition n’est jamais affichée comme diagnostic retenu.
5. Le Master Plan reste backend-authoritative et ses mutations deviennent traçables/versionnées avant clôture P3.
6. Les examens général/spécialisés restent accessibles et clairement groupés.
7. Aucun score financier/commercial, insight générique ou message d’« intelligence » opaque dans la lecture clinique.
8. Zéro overflow horizontal, erreur runtime ou HTTP 5xx sur 390x844, 430x932, 768x1024, 1280x900.

## Preuve requise
- baseline BEFORE Clinique sur les 4 viewports avant changement UI ;
- tests backend ciblés : isolation patient/tenant, RBAC clinical, persistence odontogramme, traçabilité Master Plan ;
- tests frontend + build ;
- AFTER sur les mêmes 4 viewports ;
- comparaison BEFORE / wireframe / AFTER ;
- CI + T2 exact-HEAD ;
- certification scientifique séparée pour toute règle clinique conservée/modifiée.

## Audit initial

### 1. Profil médical
Source canonique actuelle : `Patient.antecedents_medicaux` (P0-G). Dans `ClinicalHub`, cette donnée n’a pas de bloc dédié ; la surface affiche `VigilanceRadar`, alimenté par un store générique d’insights et capable d’afficher aussi des signaux financiers/suggestions. Ce radar n’est pas une source clinique canonique.

### 2. Odontogramme
`ClinicalHub` initialise `odontogram_state_<patientId>` depuis `localStorage` et réécrit chaque changement dans `localStorage`. Le texte précise que c’est un brouillon local non enregistré, ce qui était acceptable en P0 comme fail-closed, mais ne satisfait pas P3 « odontogramme canonique et persistant ».

### 3. Examens et conclusions
Les assistants Général/Paro/Endo/Chirurgie/Prothèse/Pédo/Ortho/ATM/Pathologie sont déjà classés comme protocoles structurés. Leur sortie est gardée en état de session `lastDiagnosis` et libellée « Proposition clinique à valider ». Cette frontière doit être conservée.

### 4. Master Plan
Le backend `/patients/{id}/master-plan` est la source autoritative. L’UI remplace le plan après succès backend et reste fail-closed à l’erreur. En revanche, les mutations remplacent l’état courant sans historique de révision visible : P3 doit ajouter une traçabilité/version simple et testable sans réécrire le moteur clinique.

### 5. Vigilance / Compagnon
`VigilanceRadar` vit dans `features/admin/DocumentStudio` mais est monté dans Clinique. Il mélange `safety`, `financial_risk`, `financial`, `habit`, `suggestion`, propose un marquage « VÉRIFIÉ » basé sur `source_type === DETERMINISTIC` et des navigations legacy (`tab=admin`, `tab=archives`). Il doit sortir de la lecture clinique principale. Le « Compagnon Diagnostique » ne sera déplacé depuis Documents que si son code est retrouvé et son rôle confirmé comme collecte/proposition, jamais comme diagnostic autonome.

## Découpage P3

### P3-A — Vérité clinique + odontogramme
- bloc « Sécurité médicale » depuis la source Patient ;
- supprimer `VigilanceRadar` de la colonne clinique principale ;
- modèle/endpoint odontogramme backend patient-scopé ;
- migration de l’UI `localStorage` vers lecture/sauvegarde backend ;
- états loading/error/empty honnêtes.

### P3-B — Examens / hypothèses / diagnostic retenu
- organiser Examen général vs examens spécialisés ;
- conserver les propositions session-only tant qu’elles ne sont pas explicitement validées ;
- auditer l’existence d’un modèle persistant de diagnostic retenu avant d’en créer un ;
- aucun passage automatique proposition → diagnostic.

### P3-C — Master Plan traçable + Compagnon
- conserver le Master Plan actuel comme source ;
- journaliser/versionner chaque sauvegarde réussie ;
- rendre la dernière modification/provenance visible ;
- déplacer le Compagnon uniquement si audit fonctionnel conclut qu’il appartient à Clinique.

### P3-D — Certification
- validation scientifique composant par composant ;
- AFTER 4 viewports ;
- tests/CI/T2 exact-HEAD ;
- roadmap + certificat.

## Wireframe cible

```text
CLINIQUE
┌──────────────────────────────────────────────────────────────┐
│ SÉCURITÉ MÉDICALE                                            │
│ Antécédents enregistrés / Aucun antécédent renseigné         │
│ Source : dossier Patient                         [Modifier]    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐ ┌──────────────────────────────┐
│ DOSSIER CLINIQUE             │ │ MASTER PLAN                  │
│ [Odontogramme] [Examens]     │ │ étapes backend enregistrées  │
│                              │ │ dernière révision / auteur    │
│ Odontogramme persistant      │ │                              │
│ Etat sauvegardé / erreur     │ │ [étapes / statuts]            │
└──────────────────────────────┘ └──────────────────────────────┘

EXAMENS
[Examen clinique complet]
[Parodontologie] [Endodontie] [Prothèse] [...]

PROPOSITION DE L’ASSISTANT
« Proposition à valider »
≠ DIAGNOSTIC RETENU
```

## Règles
- pas de nouvelle règle thérapeutique en P3-A ;
- pas de score de risque automatique ;
- pas de donnée clinique autoritative en `localStorage` ;
- pas de succès avant réponse backend réussie ;
- pas de déploiement Vercel.
