# Document Studio — Ordonnance Fidelity V3 / V3.1

Date de reprise : 2026-09-14

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

Aucune palette Ordonnance parallèle. Aucun `data-theme` local. Les couleurs d’alerte clinique restent sémantiques.

## Lots V3 déjà prouvés

| Lot | Axe | Score prouvé avant V3.1 |
| --- | --- | ---: |
| U1 | Hiérarchie | 9,5/10 |
| U2 | Densité clinique | 9,4/10 |
| U4 | Cartes médicaments | 9,4/10 |
| U5 | Composition desktop | 9,5/10 |
| U3 | Premium / Glass | 9,6/10 |
| U6 | Cohérence générale | 9,5/10 |

Preuve visuelle U6 précédente : HEAD `617d4f53c07ff9ca8174f637ccf6379e76a20f24`, Fidelity V3 Visual #23 SUCCESS, artifact `10327099356`, digest `sha256:ab36cd1d25fe76b099ca0a643d4ba0235098f0fcfe15ed6210af4dae78033ea4`.

## Réouverture V3.1 — défaut confirmé

La revue visuelle utilisateur du mockup a identifié un écart central non correctement reflété dans le score précédent : le **Prescription Composer structuré** du mockup était absent.

Le mockup présente pour chaque médicament :

`Prise → rythme/condition → durée/limite → moment/durée → phrase synthétique`.

Exemples de référence :

- `1 comprimé | 3 fois par jour | 7 jours | Après repas`
- `1 comprimé | Si douleur | Max 3/jour | 3 jours`

L’app V3 précédente conservait essentiellement une zone de posologie texte libre. L’ancien score global `9,48/10 → 9,5/10 arrondi` est donc **retiré comme score final** tant que V3.1 n’est pas certifiée.

## Goal V3.1 — Prescription Composer

Ajouter dans chaque `DrugRow` médicament un compositeur structuré fidèle au mockup tout en conservant le contrat de données `DrugItem.posologie: string`.

### Succès observable

- quatre contrôles structurés visibles ;
- contrôles principaux >=44 px ;
- phrase de prescription synthétique visible immédiatement dessous ;
- texte libre conservé comme fallback ;
- presets historiques parsés quand leur syntaxe est reconnue ;
- aucun champ backend ajouté ;
- aucune migration DB ;
- aucune modification des endpoints, du PDF ou du moteur pharmacologique ;
- 390×844 / 430×932 / 768×1024 / 1280×900 sans overflow ;
- comparaison visuelle directe avec le bloc du mockup ;
- nouveau score global uniquement après preuve AFTER.

## Implémentation V3.1 en cours

### Moteur UI pur

Fichier ajouté :

`frontend/src/features/admin/DocumentStudio/Forms/PrescriptionComposer.ts`

Fonctions :

- parsing non destructif des posologies historiques reconnues ;
- composition d’une phrase dans le champ `posologie` existant ;
- aucune donnée pharmacologique inventée automatiquement ;
- la sélection structurée reste une action explicite du praticien.

Commit : `bf58121d7d48a6ca58439aa851f683787512c9f9`.

### DrugRow

`DrugRow.tsx` contient maintenant :

- contrôle Prise ;
- contrôle Rythme ;
- contrôle Durée / max ;
- contrôle Moment / durée ;
- résumé synthétique `data-composer-summary` ;
- fallback `Texte libre` ;
- surfaces basées sur les tokens du thème actif ;
- grille responsive 2 colonnes mobile / 4 colonnes desktop large.

Commit : `3cc1342e10b192cb9ae50c53ae86921caf17bbee`.

### Tests

`PrescriptionComposer.test.ts` verrouille :

1. `1 comprimé, 3 fois par jour pendant 7 jours, après les repas.` ;
2. `1 comprimé, si douleur, sans dépasser 3 fois par jour pendant 3 jours.` ;
3. parsing `1 cp x 3 / jour pendant 4 jours` ;
4. parsing `Matin et Soir ... au milieu des repas` ;
5. texte non reconnu conservé hors composer jusqu’à action explicite.

HEAD code + tests V3.1 : `9b2a0527efd70ed8fa8771c7d472f33e597366ee`.

## État Git vérifié

Au HEAD `9b2a0527efd70ed8fa8771c7d472f33e597366ee` :

- `behind_by=0` face à `master` ;
- PR #474 ouverte ;
- aucun merge intermédiaire ;
- Fidelity V3 Visual #27 lancé ;
- CI #3863 lancé ;
- T2 #2791 lancé ;
- P7 #1429 lancé ;
- PostgreSQL #306 lancé ;
- P3 #54 lancé ;
- Settings #583 lancé ;
- M6-I #1591 SKIPPED attendu.

## Score global

**EN ATTENTE DE RECERTIFICATION V3.1.**

L’ancien `9,5/10` ne doit plus être présenté comme score final tant que le Prescription Composer n’a pas son AFTER exact-head.

## Next exact

1. obtenir Fidelity V3 #27 exact-head ;
2. inspecter le composer sur 390 / 430 / 768 / 1280 ;
3. comparer directement avec le bloc du mockup ;
4. corriger si nécessaire ;
5. rescorrer U4/U6 et le global ;
6. mettre à jour ce canonique ;
7. certifier le HEAD documentaire final ;
8. vérifier PR / reviews / diff ;
9. merge unique #474 ;
10. vérifier `master` post-merge.
