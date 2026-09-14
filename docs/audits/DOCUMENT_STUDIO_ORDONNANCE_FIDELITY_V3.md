# Document Studio — Ordonnance Fidelity V3.1

Date de clôture candidate : 2026-09-14

## Goal global

Rapprocher l’UI Ordonnance du mockup cible sans créer de thème Ordonnance dédié et sans modifier le moteur clinique, pharmacologique, les endpoints, le PDF ou les contrats backend.

## Stratégie Git

- repo : `hraaaaf/Digital_crown`
- branche : `ux/ordonnance-fidelity-v3-u1-hierarchy`
- PR cumulative : `#474`
- merge : unique après certification globale réelle
- Vercel : aucun déploiement

## Invariant thème

Ordonnance hérite exclusivement du thème actif Digital Crown via les tokens existants (`primary`, `secondary`, `accent`, `glass-bg`, `glass-border`, `card`, `text-main`, `text-muted`, `border-main`, `input-field`).

Aucune palette Ordonnance parallèle. Aucun `data-theme` local dans le produit. Les couleurs d’alerte clinique restent sémantiques.

## Scores finaux du scope Ordonnance

| Lot | Axe | Score final |
| --- | --- | ---: |
| U1 | Hiérarchie | 9,5/10 |
| U2 | Densité clinique | 9,4/10 |
| U4 | Cartes médicaments + Prescription Composer V3.1 | 9,6/10 |
| U5 | Composition desktop | 9,5/10 |
| U3 | Premium / Glass | 9,6/10 |
| U6 | Cohérence générale | 9,5/10 |

Moyenne : `9,52/10`, présentée à un chiffre après la virgule : **9,5/10**.

## V3.1 — Prescription Composer

La revue utilisateur du mockup avait identifié un écart central : le compositeur structuré de posologie manquait dans la V3 initiale.

Le composant est maintenant présent dans chaque `DrugRow` avec le contrat suivant :

`Prise → rythme/condition → durée/limite → moment/durée → phrase synthétique`.

Scénarios de référence certifiés :

- `1 comprimé | 3 fois par jour | 7 jours | Après repas`
  → `1 comprimé, 3 fois par jour pendant 7 jours, après les repas.`
- `1 comprimé | Si douleur | Max 3/jour | 3 jours`
  → `1 comprimé, si douleur, sans dépasser 3 fois par jour pendant 3 jours.`

Le texte libre reste disponible comme fallback et le contrat persistant reste `DrugItem.posologie: string`.

Aucun champ backend, migration DB, endpoint, PDF ou moteur pharmacologique n’a été modifié.

## Écart assumé au mockup

La mention automatique `voie orale` n’est pas générée car le contrat médicament actuel ne fournit pas de donnée fiable de voie d’administration. V3.1 n’infère pas une route clinique à partir de la forme galénique.

## Preuves visuelles et runtime

### HEAD produit recertifié

`3016fc70629a4c531979633beb6ba1e19a23bad7`

- CI #3893 : **SUCCESS**
- T2 Runtime Browser #2819 : **SUCCESS**
- Ordonnance Fidelity V3 Visual #46 : **SUCCESS**
  - artifact `10339125099`
  - digest `sha256:833ae33f6c9f3a4da8e625233f0fa2ab168eb7218ca6cd4960cd6d47c6ad5bd3`
- Ordonnance Composer Visual #10 : **SUCCESS**
  - artifact `10338661093`
  - digest `sha256:1cbb3a07cba83468b2e0ee49a1d031361f2200ebfb39c7d19519b99193854ac8`
- Patient P7 #1455 : **SUCCESS**
- PostgreSQL #334 : **SUCCESS**
- Clinic P3 #73 : **SUCCESS**
- Settings #602 : **SUCCESS**
- M6-I #1619 : **SKIPPED attendu**

### Composer Visual #10

Viewports certifiés :

- 390×844
- 430×932
- 768×1024
- 1280×900

Critères observables :

- 2 cartes `DrugRow` réelles dans le fixture dédié ;
- 4 contrôles structurés par carte ;
- hauteur minimale des contrôles >=44 px ;
- résumé synthétique visible ;
- textes attendus exacts sur les deux scénarios ;
- aucun overflow horizontal ;
- aucune erreur runtime.

### Fidelity V3 #46

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

## Synchronisation master

Le produit recertifié a ensuite été resynchronisé sans force avec `master` `629907dedae74d7d28d1dfc33e635b8410eb5f1e` via le merge commit `c0f2a284f23fcda03f104d7067596b013ea10970`.

Les commits arrivés sur `master` concernaient Céphalo et étaient hors du périmètre Ordonnance.

## État final avant merge unique

- PR #474 ouverte ;
- mergeable : oui ;
- aucun déploiement Vercel ;
- score final scope Ordonnance : **9,5/10** ;
- capture finale à produire depuis `master` après merge pour le comparatif demandé `MOCKUP CIBLE | APP RÉELLE FINALE`.

## Next exact

1. certifier le HEAD documentaire final ;
2. vérifier PR / reviews / threads / diff ;
3. merge unique #474 avec verrouillage du HEAD ;
4. vérifier `master` post-merge ;
5. produire la capture finale réelle depuis le code mergé ;
6. livrer le côte-à-côte final sans fixture ni incrustation de démonstration.
