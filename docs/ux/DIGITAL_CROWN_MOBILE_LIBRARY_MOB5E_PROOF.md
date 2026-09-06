# Digital Crown Mobile — MOB-5E Bibliothèque clinique — Proof

Status: **DONE / MERGED**

## Goal

Apporter la Bibliothèque clinique existante au cockpit mobile comme surface de consultation rapide, sans portage brut desktop ni seconde source de vérité.

## Scope certifié

- `Plus → Bibliothèque`
- deep-link `?tab=library`
- accès DENTISTE / ADMIN uniquement
- RBAC fail-closed tant que le rôle n'est pas chargé, menu Plus inclus
- réutilisation directe de `CLINICAL_PROTOCOLS`
- **50 protocoles** versionnés, sans copie de données
- recherche par acte / code / discipline
- cartes compactes : nom, catégorie, durée, difficulté
- ouverture d'un protocole dans le cockpit mobile
- détail clinique via le contenu existant `ClinicalRefContent`
- favoris via la clé existante `dc_favs`
- récents via la clé existante `dc_recents`
- Science Hub exclu du mobile
- aucun backend/API/DB ajouté
- aucune donnée patient/cabinet dans la preview
- aucun déploiement Vercel

## Références exactes

- Repo : `hraaaaf/Digital_crown`
- PR : `#361` — merged
- branche : `ux/mobile-library-mob5e`
- master de référence produit : `9cb740bc52efc9bf734c19fefc3c4f07470eba80`
- master docs avant PR : `e91d9a6146e82b5090513dec6e38d5b7e4ba6382`
- HEAD produit final : `b345d7153196a8ee5e5e05c128eef8a5a8b2ec41`
- merge ref produit certifiée : `2bd084d39b47dd6c79b25df69c83723c642887d8`
- HEAD final synchronisé avec master avant merge : `05cf642937210e70d70172503a142a45016d20f3`
- merge final : `b850cff2bd03dda667d6e1b6e449230658035d62`

## Tests

### MOB-5E ciblés

Run produit `34042238302` — **SUCCESS**

- 4 fichiers Vitest passés
- **12/12 tests passés**
- bridge mobile
- navigation Plus / RBAC
- `LibraryView`
- garde thème mobile
- build production Vite : ✅

Run HEAD final `34043911199` — **SUCCESS**

### CI générale

Run produit `34042238326` — **SUCCESS**

- Frontend tests & build : ✅
- Tests & durcissement : ✅
- Garde production : ✅
- M4-A Patient bridge : ✅
- M4-B Panoramic bridge : ✅
- M4-C Document bridge : ✅
- backend complet : **2994 passed, 8 skipped, 4 warnings**

Run HEAD final `34043911174` — **SUCCESS**

- T2 Runtime Browser `34043911191` — **SUCCESS**
- Mobile Library MOB-5E Cert `34043911199` — **SUCCESS**

Les 4 warnings sont les SAWarnings SuperAdmin déjà connus sur la coercition de sous-requêtes ; aucune relation démontrée avec MOB-5E.

## Certification BEFORE / AFTER

Baseline BEFORE exacte : `9cb740bc52efc9bf734c19fefc3c4f07470eba80`

Viewports exacts :

- 390×844
- 430×932
- 768×1024

### BEFORE

- Plus sans Bibliothèque : ✅
- navigation canonique : 5 boutons
- hauteur nav : 76 px
- overflow horizontal : 0
- erreurs runtime : 0

### AFTER

Pour les trois viewports, liste **et** détail :

- Bibliothèque visible : ✅
- 50 protocoles issus de la source partagée : ✅
- recherche `Extraction molaire` : ✅
- détail clinique source-derived : ✅
- navigation canonique : 5 boutons
- hauteur nav : 76 px
- overflow horizontal : 0
- erreurs runtime : 0

## Artifact

- run : `34042238302`
- artifact : `9992080508`
- nom : `mobile-library-mob5e-evidence`
- taille : `1,826,265` octets
- digest : `sha256:db3b5956c934701dbe6060781cedd87ad0171e52b85fe877095a58190abe671e`
- 14 fichiers de preuve

Captures inspectées :

- `before-plus-390x844.png`
- `before-plus-430x932.png`
- `before-plus-768x1024.png`
- `after-library-list-390x844.png`
- `after-library-list-430x932.png`
- `after-library-list-768x1024.png`
- `after-library-detail-390x844.png`
- `after-library-detail-430x932.png`
- `after-library-detail-768x1024.png`

## Comparaison visuelle

AFTER améliore le cockpit mobile sans dénaturer la bibliothèque desktop :

- hiérarchie search-first claire
- densité maîtrisée sur 390 px
- métadonnées cliniques lisibles
- onglets du détail tiennent sans débordement
- cartes et états de difficulté cohérents avec le langage Digital Crown
- nav fixe cohérente avec les lots précédents
- aucune dérive Science Hub / desktop rail

Le contenu peut naturellement défiler derrière la bottom nav fixe ; aucune perte d'accès ni overflow certifié n'a été observé.

## Score visuel

**9.4 / 10**

Justification : hiérarchie, cohérence, lisibilité et adaptation 390/430/768 sont solides. La densité du détail à 390 px reste élevée mais cohérente pour une surface clinique de consultation rapide.

## Warnings hors lot

- npm audit du frontend : vulnérabilités préexistantes observées pendant l'installation ; aucune attribution à MOB-5E démontrée.
- dépréciation Node.js 20 des GitHub Actions : infrastructure CI, non spécifique au lot.
- conflit de dépendances CI `httpx` déjà connu : CI complète néanmoins verte ; non résolu par MOB-5E.

## Verdict

**MOB-5E est certifié, mergé dans `master` via `b850cff2bd03dda667d6e1b6e449230658035d62`, avec gates finaux du HEAD `05cf642937210e70d70172503a142a45016d20f3` verts.**
