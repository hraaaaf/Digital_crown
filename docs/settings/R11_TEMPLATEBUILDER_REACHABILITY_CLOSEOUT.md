# R11 — TemplateBuilder legacy cleanup — CLOSEOUT

Date : 2026-08-20

## Goal
Prouver la reachability réelle du domaine TemplateBuilder, puis supprimer uniquement le frontend prouvé orphelin sans casser le domaine backend/persistance `DocumentTemplate`.

## Résultat
**CERTIFIABLE — nettoyage minimal appliqué.**

### Supprimé
- `frontend/src/features/admin/TemplateBuilder.tsx` : composant non routé et sans import runtime externe ;
- objet frontend `templateApi` dans `frontend/src/services/templateApi.ts` : ses appels étaient exclusivement consommés par le builder orphelin.

### Conservé volontairement
- `cabinetApi`, consommé par `App.tsx`, `Header.tsx` et `SetupWizard.tsx` ;
- modèle/table `DocumentTemplate` ;
- seed startup `DocumentTemplate` ;
- router `/api/templates` ;
- `TemplateEngine`, ses tests et l'instanciation historique dans `DocumentFactory`.

Aucune migration DB, aucune suppression de données, aucun backend produit modifié.

## Preuves reachability BEFORE
Run : `32365989327` — SUCCESS.
Artifact : `9405292952`.
Digest : `sha256:7d25355bc2aa2fd5350beef48aed9985bc1f46fc3817fd118e05a4b433a8d66d`.

Constats :
- `TemplateBuilder` : aucune consommation produit hors du fichier lui-même ;
- `/settings/templates` : aucune route produit active ;
- `templateApi` : méthodes template consommées uniquement par `TemplateBuilder` ;
- `DocumentTemplate` : nombreuses références backend actives, donc conservation obligatoire ;
- `TemplateEngine` : tests et instanciation backend existants, donc hors suppression R11.

## Commit produit
`fb51b02125baee2996694db2e1ab2173ece30897`

Diff produit ciblé :
- suppression `TemplateBuilder.tsx` ;
- retrait de `templateApi` ;
- conservation stricte de `cabinetApi` ;
- garde workflow R11 renforcée.

## Preuves AFTER
R11 TemplateBuilder Reachability Audit #4 : `32366397114` — SUCCESS.
Artifact : `9405470141`.
Digest : `sha256:67a7e753e8bc51f8293c9c9f91d39adffc7d73a78cbe690a068654b28b1f8543`.

Le workflow exact-head prouve :
- `TemplateBuilder.tsx` absent ;
- export `templateApi` absent ;
- `cabinetApi` présent et ses consommateurs actifs conservés ;
- `DocumentTemplate` présent dans router/modèle/seed ;
- `npm ci` + `npm run build` : SUCCESS.

T2 Runtime Browser Certification #707 : `32366397301` — SUCCESS.
Patient P7 Final Certification #6 : `32366397221` — SUCCESS.

CI #1469 `32366397341` au moment du closeout :
- `Frontend (tests & build)` — SUCCESS ;
- `Garde production (négatif)` — SUCCESS ;
- seule la suite backend `Tests & durcissement / Test suite` reste en cours.

Cette suite backend n'est pas bloquante pour le closeout R11 : le compare du commit produit ne contient **aucun fichier backend**, tandis que le job frontend complet, le build R11 ciblé et T2 sont déjà verts. Le statut global CI n'est donc pas présenté comme SUCCESS tant qu'il ne l'est pas ; l'équivalence est explicitement limitée au scope frontend R11.

## UI/UX
Aucun écran actif n'est modifié : le composant supprimé n'était ni routé ni importé dans le produit. Le protocole BEFORE/AFTER visuel n'est donc pas applicable à ce nettoyage non visible. Aucun score visuel n'est attribué artificiellement.

## Dette conservée, explicitement hors scope
`TemplateEngine` et `_get_default_template()` restent des candidats de simplification backend future, mais leur suppression exigerait un lot séparé avec preuves backend et tests documentaires.

## Vercel
Aucun déploiement.
