# Document Studio — Ordonnance Fidelity V3

Date: 2026-09-13

## Goal global

Rapprocher l’UI Ordonnance du mockup cible sans créer de thème Ordonnance dédié et sans modifier le moteur clinique, pharmacologique, les endpoints, le PDF ou les contrats backend.

## Invariant thème

Ordonnance hérite exclusivement du thème actif de Digital Crown.

Tokens de référence existants :

- `--primary`
- `--secondary`
- `--accent`
- `--glass-bg`
- `--glass-border`
- `--card-bg`
- `--sidebar-bg`
- `--text-main`
- `--text-muted`
- `--border-color`
- `--input-bg`

Aucune palette Ordonnance parallèle. Aucun `data-theme` local. Aucun hexadécimal ajouté dans les surfaces U1.

## Axes et lots

| Lot | Axe | Score entrée | Cible |
| --- | --- | ---: | ---: |
| U1 | Hiérarchie | 7,5 | 9,5 |
| U2 | Densité clinique | 7,7 | 9,4 |
| U3 | Premium / Glass | 5,8 | 9,6 |
| U4 | Cartes médicaments | 6,2 | 9,4 |
| U5 | Composition desktop | 6,5 | 9,5 |
| U6 | Cohérence générale | 6,8 | 9,5 |

Ordre d’exécution retenu : `U1 → U2 → U4 → U5 → U3 → U6`.

## BEFORE U1 — Hiérarchie

Baseline produit : `37f58ed0bc410a1b29b32fdc62ae1d11e924ec25`.

`master` au lancement U1 : `ab4bd58bf17bf567473ebfd6dfbd2e273ebd9426`.

Comparaison `37f58ed → master` : uniquement documentation, aucun fichier produit Ordonnance modifié. Les captures T2 exact-head du lot précédent restent donc la référence visuelle produit BEFORE.

Score manuel BEFORE U1 : **7,5/10**.

Constats :

1. le titre primaire affiche encore `Studio Documentaire` au lieu de `Ordonnance` ;
2. le type de document est relégué en badge alors qu’il doit guider la lecture ;
3. les mentions légales apparaissent avant le workflow clinique principal ;
4. auteur/date sont nécessaires mais ne doivent pas battre visuellement le type de document et le patient ;
5. l’ordre clinique interne attendu reste `contexte/sécurité → protocoles → saisie → médicaments → actions`.

## Goal U1

Faire comprendre immédiatement au praticien qu’il est dans une ordonnance, pour quel patient, puis lui présenter les contrôles cliniques dans le bon ordre sans changer le thème actif.

## Succès observable U1

- `Ordonnance` est le titre primaire du Studio sur cet onglet ;
- le patient est immédiatement sous le titre ;
- auteur clinique et date restent présents et tactiles >=44 px mais secondaires ;
- contexte/sécurité précèdent les protocoles ;
- les protocoles précèdent le corps de prescription ;
- les mentions légales passent après le workflow clinique ;
- aucun thème ou token global n’est modifié ;
- aucune logique clinique, safety, pharmacologie, backend, PDF ou LLM n’est modifiée ;
- AFTER vérifié sur `390×844`, `430×932`, `768×1024`, `1280×900` ;
- score manuel Hiérarchie >= **9,5/10** avant clôture U1.

## Validation U1 obligatoire

1. tests statiques du contrat de hiérarchie et héritage thème ;
2. frontend tests + build ;
3. T2 runtime browser exact-head ;
4. P7 / PostgreSQL si déclenchés ;
5. inspection manuelle des quatre viewports ;
6. comparaison BEFORE / AFTER ;
7. correction si score < 9,5 ;
8. merge uniquement après preuve.

## État U1

EN COURS.
