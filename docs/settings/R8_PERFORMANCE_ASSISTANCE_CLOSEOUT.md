# R8 — Performance & Assistance — Closeout

Date : 2026-08-19
Repo : `hraaaaf/Digital_crown`
PR : `#183` — **CERTIFIÉ — READY TO MERGE**
HEAD produit certifié : `bfabc0cb4809b7cca2a0a9b4bee4cc93b669d482`

## Goal

Remplacer l’ancienne surface **IA & Système** par une configuration courte, vraie et utile : **Performance & Assistance**, sans nouvelle promesse IA et sans supprimer de données persistées encore compatibles.

## Résultat produit vérifié

- onglet renommé **Performance & Assistance** ;
- **Mode Performance** conservé car son downstream est réel ;
- **Arrière-plan animé** déplacé vers **Design & Ambiance**, où il relève réellement ;
- **Conseils cliniques contextuels** conservés, avec consommateurs réels `Sidebar` et `Step1Cephalo` ;
- indicateurs patients conservés sous le libellé factuel **Indicateurs de suivi patient** ;
- explication explicite du score backend : **60 % assiduité rendez-vous + 40 % encaissé/facturé**, valeur neutre 50 sans données, ajustement praticien possible ;
- aucun nouveau LLM/IA ;
- aucun champ persistant supprimé ;
- harness RBAC et harness IA alignés sur le nouveau libellé ;
- installation Chromium du harness IA simplifiée de `--with-deps chromium` à `chromium` après blocages répétés d’APT, sans changement produit.

## Preuves

### Gates produit / exact-head

Sur `bfabc0cb4809b7cca2a0a9b4bee4cc93b669d482` :

- Settings IA Visual #18 — run `32283895358` — **SUCCESS** ;
- Settings Branding Visual #65 — run `32283895390` — **SUCCESS** ;
- Settings RBAC Visual #124 — run `32283895238` — **SUCCESS** ;
- Settings Profile R2 Visual #24 — run `32283895463` — **SUCCESS** ;
- Settings Profile Team Read Truth #12 — run `32283895384` — **SUCCESS** ;
- T2 Runtime Browser #644 — run `32283895445` — **SUCCESS**.

### CI et équivalence produit

CI #1396 a terminé **SUCCESS** sur le parent `7ee15500f9d881e64721379423cda14737dd2b3f`.

Le compare `7ee155...` → `bfabc0...` contient exactement **un fichier de workflow** et **une substitution de commande** :

`npx playwright install --with-deps chromium` → `npx playwright install chromium` dans `.github/workflows/settings-ia-visual-cert.yml`.

Aucun fichier produit, test métier ou donnée n’a changé entre ces deux commits. La preuve CI #1396 est donc applicable au produit certifié `bfabc0...`. Le run CI exact-head #1398 peut continuer sans bloquer le chantier ; il n’est pas utilisé pour fabriquer une preuve inexistante.

### Preuve visuelle exact-head

Artifact IA exact-head :

- artifact `9376898431` ;
- digest `sha256:6b703e2c725b9bb5a71747ddcc958c837a1d227cfdec5b7c678f7548cb4ce2de` ;
- 5 captures : 1440 / 1024 / 768 / 430 / 390 px ;
- navigation et titre **Performance & Assistance** présents ;
- trois contrôles uniquement ;
- texte patient factuel 60/40 ;
- aucun faux vocabulaire IA ;
- aucun débordement horizontal observé.

Branding exact-head #65 est également **SUCCESS** ; l’arrière-plan animé est présenté dans **Design & Ambiance**.

## Score visuel

**9,5/10**.

Forces : simplification nette, hiérarchie très lisible, promesses alignées sur le comportement réel, responsive propre sur cinq viewports, séparation cohérente entre performance/assistance et ambiance visuelle.

Réserve : la surface mobile reste assez longue verticalement et le shell Réglages conserve une logique encore légèrement desktop-first ; rien de bloquant pour R8.

## Statut

**CERTIFIÉ — READY TO MERGE**.

Le lot ne sera comptabilisé dans l’avancement global qu’après preuve du merge et mise à jour post-merge.

Avancement chantier avant merge : **5/15 = 33,3 %**.

Aucun déploiement Vercel.
