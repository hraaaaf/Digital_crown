# Document Studio — Ordonnance Fidelity V3

Date: 2026-09-13

## Goal global

Rapprocher l’UI Ordonnance du mockup cible sans créer de thème Ordonnance dédié et sans modifier le moteur clinique, pharmacologique, les endpoints, le PDF ou les contrats backend.

## Stratégie Git du chantier

Une seule branche et une seule PR cumulative sont conservées pour U1 → U6.

- branche : `ux/ordonnance-fidelity-v3-u1-hierarchy`
- PR : `#474`
- merge : **unique après certification U6 + score global + closeout**

Aucun merge intermédiaire par axe.

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

Aucune palette Ordonnance parallèle. Aucun `data-theme` local. Aucun hexadécimal ajouté dans les surfaces Fidelity V3.

## Axes et lots

| Lot | Axe | Score entrée | Cible | État |
| --- | --- | ---: | ---: | --- |
| U1 | Hiérarchie | 7,5 | 9,5 | **certifié 9,5/10** |
| U2 | Densité clinique | 7,7 | 9,4 | **en cours** |
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

### Exact-head closeout U1

HEAD documentaire U1 : `74e7a7d105dc0b982dc22e3cdee01061121d4651`.

- CI #3785 : **SUCCESS** ;
- T2 #2717 : **SUCCESS** ;
- P3 #22 : **SUCCESS** ;
- Patient P7 #1369 : **SUCCESS** ;
- PostgreSQL #232 : **SUCCESS** ;
- Settings R11 #551 : **SUCCESS** ;
- M6-I #1517 : **SKIPPED attendu**.

## Score U1

Score manuel AFTER Hiérarchie : **9,5/10**.

## État U1

**CERTIFIÉ : 9,5/10.**

Pas de merge intermédiaire : U1 reste dans la PR cumulative #474 jusqu’au closeout global U6.

---

## BEFORE U2 — Densité clinique

Baseline exacte : HEAD U1 certifié `74e7a7d105dc0b982dc22e3cdee01061121d4651`.

Artifact T2 baseline : run #2717, artifact `t2-browser-evidence`, ID `10325204876`, digest `sha256:7eb7ba006f42ce3db136782f91e677b942578eee852bb2bdee51b69bcf9b3125`.

Score manuel BEFORE U2 : **7,7/10**.

Constats sur `390/430/768/1280` :

1. rythme vertical trop généreux entre contexte, protocoles, QuickEntry et planning ;
2. sur mobile 430 px, les blocs secondaires consomment une part excessive du viewport ;
3. la zone `Ajouter une ligne` utilise plus de hauteur que sa fonction ne le justifie ;
4. la densité peut être améliorée sans réduire les cibles tactiles sous 44 px ;
5. U2 ne doit ni refondre les cartes médicament (U4), ni modifier la composition desktop (U5), ni ajouter d’effets Glass (U3).

## Goal U2

Faire passer la densité clinique de **7,7/10 à >=9,4/10** en réduisant les espaces et paddings non fonctionnels, tout en conservant la lisibilité et les cibles tactiles.

## Succès observable U2

- réduction perceptible de la hauteur perdue entre blocs, cible environ 20–30 % sur les zones compactables ;
- QuickEntry conserve son champ principal `min-h-14` ;
- protocoles, actions contexte, suggestions et accès rapides conservent >=44 px ;
- bouton `Ajouter une ligne` conserve >=44 px ;
- aucune logique clinique, pharmacologique, safety, backend, PDF ou LLM modifiée ;
- aucun token ou thème global modifié ;
- AFTER inspecté sur `390×844`, `430×932`, `768×1024`, `1280×900` ;
- score manuel Densité clinique >= **9,4/10** avant validation U2.

## Implémentation U2 en cours

- wrapper clinique V3 : espacement principal `space-y-3 → space-y-2` ;
- contexte/sécurité : paddings et gaps réduits, sans réduire les contrôles tactiles ;
- protocoles rapides : padding/gap resserrés, chips toujours `min-h-11` ;
- QuickEntry : padding de surface et rythme interne resserrés via la couche U2, champ principal inchangé à 56 px ;
- planning legacy : rythme vertical réduit via CSS ciblé ;
- `Ajouter une ligne` : padding vertical réduit mais `min-height: 44px` imposé ;
- test statique U2 ajouté.

## Validation U2 obligatoire

1. tests frontend + build ;
2. T2 exact-head ;
3. AFTER `390/430/768/1280` ;
4. comparaison visuelle avec baseline U1 ;
5. correction si score <9,4 ;
6. aucun merge : continuer U4 sur la même PR si U2 est certifié.

## Next

Certifier U2, puis démarrer **U4 — Cartes médicaments, 6,2 → 9,4** sur la même PR #474.