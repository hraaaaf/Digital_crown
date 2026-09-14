# DIGITAL CROWN — FINALISATION PRODUIT

**FICHIER CANONIQUE DE PILOTAGE GLOBAL — HORS CÉPHALOMÉTRIE**

Baseline de création : `master@dca24d01ca5591d4255f3ac85f79a32ab6d673c1`.

## Périmètre

Ce fichier fusionne le pilotage des chantiers Digital Crown restants en un seul programme maître.

**Exclusion explicite : la Céphalométrie reste un chantier séparé et n'entre ni dans le score global, ni dans le Next exact, ni dans les priorités de ce fichier.**

## Goal global

Obtenir un Digital Crown non-Céphalo cohérent, certifié et exploitable en cabinet réel.

## Méthode de score

Axes inclus : Document Studio 100 %, Dossier Patient UX 100 %, Clinique multi-praticiens 100 %, Portabilité 89,2 %, Mobile Terrain 70 %, Sécurité / Anti-piratage 60 %.

Calcul : `(100 + 100 + 100 + 89,2 + 70 + 60) / 6 = 86,53 %`.

**Indice global courant : 86,5 %.**

Le benchmark Competitive / Media reste un KPI séparé et n'entre pas dans ce calcul.

## État consolidé

### L1 — Document Studio — FERMÉ
P1→P6 actifs certifiés ; T1 transversal mergé via PR #465.

### L2 — Dossier Patient UX — FERMÉ
UX1-A/B PR #467 et UX1-C PR #468 mergées ; 390 / 768 / 1280 certifiés.

### L3 — Clinique multi-praticiens — FERMÉ
P3 final PR #463 mergée ; HEAD certifié `30e5c235cebdb9f4e460b03a0687856336149c08` ; merge `f16fc658dad0ee4ff67a919568359f1e90d4e2da` ; CI #3763, PostgreSQL #216 et T2 #2701 SUCCESS. Axe : 100 %.

### L4 — Portabilité — HUMAN GATE
`149/167 EP = 89,2 %`. P13 physique `0/13 EP`. Fermeture requiert Windows 11 cabinet réel + stockage hors machine + Apple Silicon + closure guard.

### L5 — Mobile Terrain — HUMAN GATE
Baseline 70 %. Gates physiques iPhone/Android/biométrie/Push restent non substituables.

### L6 — Sécurité / Anti-piratage — BLOQUÉ EXTERNE
Baseline 60 %. Accès control-plane production requis pour les mutations réelles et la chaîne OWNER/licences.

### L7 — Release / CI — ACTIF TRANSVERSE
Packaging #450/#451 mergés ; Document History #469 fermé ; P3 #463 fermé. Rechercher uniquement les dettes release/CI encore réellement ouvertes lors des closeouts suivants.

### L8 — Competitive / Media — C5 FERMÉ
- PR #478 `feat(media): add C5 compare search filters` : **MERGED**.
- HEAD candidat certifié : `9e1b5eb87dddb85725f027156829dabfc3bb1fdb`.
- Merge commit : `9b1abcdde9eeab769376a8033ea69b5afb5db38b`.
- Base exacte certifiée : `master@7bdd8d781d03daca7840df719fe5bc145f02703d` ; candidat `ahead 1 / behind 0` avant merge.
- Scope final : exactement 4 fichiers C5 ; aucun fichier scientifique Céphalo.
- BEFORE : Media C5 Visual #5 / artifact `10328060830` ; overlap sticky aux 3 viewports.
- AFTER exact-head : Media C5 Visual Certification #20 / run `34825626946` **SUCCESS**.
- Artifact : `media-c5-visual-certification`, id `10340057867`, digest `sha256:b890cc8150253e4ea3d07da66e9d5be87e8d821eece287e53e4e49c2a1a65238`.
- AFTER : 3/3 captures PASS sur 390×844 / 768×1024 / 1280×900 ; sticky overlap false ; workspace overlap false ; overflow false ; page errors 0 ; HTTP 5xx 0.
- Géométries finales : 390 `headerBottom=205`, `workspaceTop=213`, `panelTop=513` ; 768 `headerBottom=213`, `workspaceTop=379`, `panelTop=590` ; 1280 `headerBottom=288`, `workspaceTop=422`, `panelTop=660`.
- Test ciblé C5 : 2/2 PASS ; frontend build PASS.
- Score visuel final inspecté : Hiérarchie 9,5 ; Clarté 9,8 ; Cohérence design system 9,7 ; Densité/respiration 9,4 ; Responsive 9,6 ; **moyenne 9,6/10**.
- Exact-head gates : CI #3906 SUCCESS ; T2 #2829 SUCCESS ; P7 #1465 SUCCESS ; PostgreSQL #344 SUCCESS ; Media C4 Visual #50 SUCCESS ; UX1-C #54 SUCCESS ; Billing #109 SUCCESS. M6-I #1629 SKIPPED attendu.
- Audit PR avant merge : reviews 0 ; threads 0 ; comments 0 ; mergeable true ; 4 fichiers C5 ; zéro Céphalo.
- Fonctionnalités fermées : recherche locale, filtres type + repère temporel, sélection de 2 médias, comparaison responsive, viewer plein écran C4 conservé, import C4 conservé.
- Aucun déploiement Vercel.
- Le KPI Competitive global n'est pas recalculé à C5 : le scorecard n'autorise le gain Media `6,0 → 8,5` qu'après fermeture complète du Lot C.

## Chemin critique unique

1. **Fermer Competitive/Media C6 puis C7, sans reprendre C4/C5 et sans toucher au chantier scientifique Céphalo.**
2. **Exécuter les gates physiques** : Portabilité P13 puis Mobile Terrain, selon disponibilité du matériel réel.
3. **Fermer Sécurité** dès que l'accès control-plane production permet l'exécution réelle des mutations autorisées.
4. **Certification globale non-Céphalo** : master propre, CI transverse verte, docs canoniques cohérents, inventaire explicite des human/external gates résiduels.

## Next exact

**Ouvrir un nouveau lot dédié Competitive / Media C6 — capture smartphone contrôlée (5 EP), conformément au scorecard canonique ; ne pas démarrer C7 dans la même fenêtre et ne pas toucher à la Céphalométrie.**

## Règles de continuité

- Une fenêtre = un lot principal jusqu'à son closeout, puis HANDOVER + STOP.
- Une CI en cours n'arrête pas le programme ; faire le travail indépendant restant.
- Aucun lot déclaré fermé sans preuve exacte.
- Aucun déploiement Vercel sans autorisation explicite.
- Les chantiers Céphalo ne sont ni modifiés, ni scorés, ni priorisés depuis ce fichier.

## Repères courant

- master avant merge C5 : `7bdd8d781d03daca7840df719fe5bc145f02703d`
- C5 PR #478 : **MERGED**
- C5 HEAD certifié : `9e1b5eb87dddb85725f027156829dabfc3bb1fdb`
- C5 merge : `9b1abcdde9eeab769376a8033ea69b5afb5db38b`
- Media C5 Visual #20 : **SUCCESS**, score 9,6/10
- CI #3906 : **SUCCESS**
- T2 #2829 : **SUCCESS**
- P7 #1465 : **SUCCESS**
- PostgreSQL #344 : **SUCCESS**
- indice global : **86,5 %**
- Céphalométrie : **hors périmètre**
- prochain gate logiciel : **Competitive / Media C6 — capture smartphone contrôlée (5 EP)**
- human gates : **Portabilité P13 + Mobile Terrain**
- external gate : **Security control-plane production**
