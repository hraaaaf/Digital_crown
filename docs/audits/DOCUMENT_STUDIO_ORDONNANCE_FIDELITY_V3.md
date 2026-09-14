# Document Studio — Ordonnance Fidelity V3.1

Date de clôture : 2026-09-14

## Goal global

Rapprocher l’UI Ordonnance du mockup cible sans créer de thème Ordonnance dédié et sans modifier le moteur clinique, pharmacologique, les endpoints, le PDF ou les contrats backend.

## Résultat final

| Lot | Axe | Score final |
| --- | --- | ---: |
| U1 | Hiérarchie | 9,5/10 |
| U2 | Densité clinique | 9,4/10 |
| U4 | Cartes médicaments + Prescription Composer V3.1 | 9,6/10 |
| U5 | Composition desktop | 9,5/10 |
| U3 | Premium / Glass | 9,6/10 |
| U6 | Cohérence générale | 9,5/10 |

Moyenne : `9,52/10`, présentée à un chiffre après la virgule : **9,5/10**.

## Invariant thème

Ordonnance hérite exclusivement du thème actif Digital Crown via les tokens existants (`primary`, `secondary`, `accent`, `glass-bg`, `glass-border`, `card`, `text-main`, `text-muted`, `border-main`, `input-field`).

Aucune palette Ordonnance parallèle. Aucun `data-theme` local dans le produit. Les couleurs d’alerte clinique restent sémantiques.

## V3.1 — Prescription Composer

Le compositeur structuré est présent dans chaque `DrugRow` avec le contrat :

`Prise → rythme/condition → durée/limite → moment/durée → phrase synthétique`.

Scénarios certifiés :

- `1 comprimé | 3 fois par jour | 7 jours | Après repas`
  → `1 comprimé, 3 fois par jour pendant 7 jours, après les repas.`
- `1 comprimé | Si douleur | Max 3/jour | 3 jours`
  → `1 comprimé, si douleur, sans dépasser 3 fois par jour pendant 3 jours.`

Le texte libre reste disponible comme fallback et le contrat persistant reste `DrugItem.posologie: string`.

Aucun champ backend, migration DB, endpoint, PDF ou moteur pharmacologique n’a été modifié.

## Écart assumé au mockup

La mention automatique `voie orale` n’est pas générée car le contrat médicament actuel ne fournit pas de donnée fiable de voie d’administration. V3.1 n’infère pas une route clinique à partir de la forme galénique.

## Preuves exact-head finales

HEAD documentaire final avant merge :

`c57f69931ccdc46732c167f6f47631e0d9acbe8f`

- CI #3896 : **SUCCESS**
- T2 Runtime Browser #2822 : **SUCCESS**
- Ordonnance Fidelity V3 Visual #48 : **SUCCESS**
  - artifact `10339208565`
  - digest `sha256:018e71b154551aadba5f90171b735770efde4b19cf03654cf64eaac4044e230d`
- Ordonnance Composer Visual #12 : **SUCCESS**
- Patient P7 #1458 : **SUCCESS**
- PostgreSQL #337 : **SUCCESS**
- Clinic P3 #75 : **SUCCESS**
- Settings #604 : **SUCCESS**
- M6-I #1622 : **SKIPPED attendu**

Composer Visual certifie :

- 390×844 / 430×932 / 768×1024 / 1280×900 ;
- 4 contrôles structurés ;
- hauteur minimale des contrôles >=44 px ;
- résumés synthétiques exacts ;
- aucun overflow horizontal ;
- aucune erreur runtime.

Fidelity V3 certifie :

- 390 / 430 / 768 / 1280 sans overflow ;
- tactile minimum 44 px ;
- preview desktop inline conservé ;
- mobile/tablette modal conservé ;
- structure U1→U6 préservée après V3.1.

## Correctifs de certification T2

Deux probes historiques supposaient encore que le preview desktop était modal et fermable par `Escape`. Depuis U5, le contrat produit est :

- `<1280 px` : preview modal/portal, fermeture `Escape` ;
- `>=1280 px` : preview inline, fermeture par bouton `Fermer`.

Les certificateurs `certify-document-studio-browser.mjs` et `certify-p6-editor.mjs` ont été alignés sur ce contrat. Le produit n’a pas été modifié pour satisfaire ces probes.

## Merge unique et post-merge

PR `#474` : **MERGED**.

Merge commit :

`7607f759cf30d78df20de3d17bf0d361f11d2d36`

Après merge, comparaison `c57f699...7607f759` :

- `ahead_by=4` ;
- un seul fichier supplémentaire diffère : `docs/CEPHALO_DIAGNOSTIC_SPEC.md` ;
- aucun fichier Ordonnance, Fidelity, Composer ou Document Studio n’a changé entre le HEAD certifié et le `master` mergé.

La capture réelle utilisée pour le comparatif final provient donc du gate Fidelity #48 sur le même contenu produit que `master` post-merge.

## Déploiement

Aucun déploiement Vercel.

## Statut

**CLOS — Ordonnance Fidelity V3.1 certifiée et mergée.**
