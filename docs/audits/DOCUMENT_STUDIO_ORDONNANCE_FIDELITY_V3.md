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

| Lot | Axe | Score entrée | Cible | État |
| --- | --- | ---: | ---: | --- |
| U1 | Hiérarchie | 7,5 | 9,5 | cible visuelle atteinte, merge pending exact-head closeout |
| U2 | Densité clinique | 7,7 | 9,4 | à faire |
| U3 | Premium / Glass | 5,8 | 9,6 | à faire |
| U4 | Cartes médicaments | 6,2 | 9,4 | à faire |
| U5 | Composition desktop | 6,5 | 9,5 | à faire |
| U6 | Cohérence générale | 6,8 | 9,5 | à faire |

Ordre d’exécution retenu : `U1 → U2 → U4 → U5 → U3 → U6`.

## BEFORE U1 — Hiérarchie

Baseline produit : `37f58ed0bc410a1b29b32fdc62ae1d11e924ec25`.

`master` au lancement U1 : `ab4bd58bf17bf567473ebfd6dfbd2e273ebd9426`.

Comparaison `37f58ed → master` : uniquement documentation, aucun fichier produit Ordonnance modifié. Les captures T2 exact-head du lot précédent restent donc la référence visuelle produit BEFORE.

Score manuel BEFORE U1 : **7,5/10**.

Constats :

1. le titre primaire affichait `Studio Documentaire` au lieu de `Ordonnance` ;
2. le type de document était relégué en badge alors qu’il doit guider la lecture ;
3. les mentions légales apparaissaient avant le workflow clinique principal ;
4. auteur/date sont nécessaires mais ne doivent pas battre visuellement le type de document et le patient ;
5. l’ordre clinique interne attendu reste `contexte/sécurité → protocoles → saisie → médicaments → actions`.

## Goal U1

Faire comprendre immédiatement au praticien qu’il est dans une ordonnance, pour quel patient, puis lui présenter les contrôles cliniques dans le bon ordre sans changer le thème actif.

## Implémentation U1

- `Ordonnance` est maintenant le titre primaire du Studio pour cet onglet ;
- le patient est immédiatement sous le titre ;
- auteur clinique et date restent présents, >=44 px et visuellement secondaires ;
- le workflow clinique reste `contexte/sécurité → protocoles → prescription` ;
- les mentions légales passent après le corps clinique ;
- aucun token, palette ou thème global n’a été modifié ;
- aucune logique clinique, safety, pharmacologie, backend, PDF ou LLM n’a été modifiée.

## Preuves U1 — exact code HEAD

HEAD code inspecté : `14e8b82ed964a34e7bd3572442b76b04be2faca8`.

### P3 visual header

Run : `34782051118` / #21 — **SUCCESS**.

Artifact : `clinic-p3-document-author-before-after`, ID `10324814613`.
Digest : `sha256:85a6c97f336f5a222985819ecde59df451448178b595ab33cedf74d13e962188`.

Viewports exacts :

- `390×844`
- `430×932`
- `768×1024`
- `1280×900`

Résultats AFTER :

- auteur unique visible ;
- hauteur sélecteur = **44 px** sur les 4 viewports ;
- overflow horizontal = **0 px** ;
- erreurs runtime = **0** ;
- comparaison manuelle BEFORE/AFTER : `Ordonnance` remplace `Studio Documentaire + badge Ordonnance` comme niveau primaire, patient immédiatement dessous.

### T2 runtime browser

Run : `34782051150` / #2716 — **SUCCESS**.

Artifact : `t2-browser-evidence`, ID `10325209319`.
Digest : `sha256:7cbfa421ca1ada48da401dde247ef28058bc85fa91121990e6c740dacf6bdad0`.

Le browser matrix Ordonnance passe sur `390/430/768/1280` et le mobile `430×932` conserve les actions `Aperçu / Enregistrer / Imprimer` sans squeeze ni overflow observé.

### Autres gates exact code HEAD

- Settings R11 #550 : **SUCCESS** ;
- PostgreSQL #231 : **SUCCESS** ;
- Patient P7 #1368 : **SUCCESS** ;
- M6-I #1516 : **SKIPPED attendu** ;
- CI #3784 : frontend tests + build **SUCCESS** ; backend global encore en cours au moment de cette mise à jour documentaire.

## Score U1

Score manuel AFTER Hiérarchie : **9,5/10**.

Justification :

- le type de document est désormais le premier niveau de lecture ;
- le patient est immédiatement associé à ce contexte ;
- les contrôles auteur/date sont présents sans dominer ;
- l’ordre clinique principal reste intact ;
- le secondaire légal n’interrompt plus l’entrée du workflow ;
- les quatre viewports de référence sont couverts visuellement par P3 exact-head.

## État U1

**CIBLE VISUELLE ATTEINTE : 9,5/10.**

Le lot n’est pas déclaré mergé ni clôturé tant que ce commit documentaire exact-head n’a pas repassé les gates requis et que `master` n’a pas été vérifié après merge.

## Next

Après exact-head green + merge U1 : démarrer **U2 — Densité clinique, 7,7 → 9,4**, toujours avec héritage exclusif du thème actif.
