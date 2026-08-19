# R9-A — Journal d’Audit humanisé — Closeout

Date : 2026-08-19
Repo : `hraaaaf/Digital_crown`
PR : `#185` — **MERGED**
Merge : `bda7f99aa95e9341f5154293618c35949bcae331`
HEAD produit certifié : `f20cfe39eeddf28152c1cc106c17eb6727edf11b`

## Goal

Humaniser **Réglages → Sécurité & Backup → Journal d'Audit** sans modifier la collecte backend, sans inventer d’identité utilisateur et sans perdre les valeurs techniques utiles.

## Résultat produit vérifié

- actions connues présentées en français lisible avec code brut secondaire ;
- sévérités `Information / Attention / Critique` ;
- ressources rendues lisibles avec identifiant conservé ;
- utilisateur affiché sous forme `Utilisateur #id`, aucun nom inventé ;
- valeurs inconnues conservées brutes en fallback ;
- détails et IP accessibles explicitement ;
- filtres backend et comportement fail-closed conservés ;
- aucune modification de la collecte backend ;
- cartes responsives jusqu’à 1279 px, table à partir de `xl` ;
- défaut réel 1024 corrigé : baseline `1250 > 1024`, tentative intermédiaire `1196 > 1024`, final `1024 = 1024`.

## Preuves exact-head

Sur `f20cfe39eeddf28152c1cc106c17eb6727edf11b` :

- Settings R9 Audit Log Visual Certification #4 — run `32298910047` — **SUCCESS** ;
- Settings Audit Read Truth Visual Certification #5 — run `32298910027` — **SUCCESS** ;
- T2 Runtime Browser Certification #678 — run `32298910025` — **SUCCESS** ;
- CI #1434 — run `32298910106` — **SUCCESS** ;
- Settings R9 Audit Log Visual Baseline #6 — run `32298910078` — **SUCCESS**.

## Preuve visuelle exact-head

Artifact AFTER :

- artifact `9382283739` ;
- digest `sha256:24f2a588924482b15ee0fe506e92c8b2a1ba3b703b5b6425312e11e4d4f3912b` ;
- HEAD artifact `f20cfe39eeddf28152c1cc106c17eb6727edf11b` ;
- 5 captures inspectées : 1440 / 1024 / 768 / 430 / 390 px ;
- métriques finales : `scrollWidth == clientWidth` sur les cinq viewports ;
- fichiers `errors.txt` vides sur les cinq viewports ;
- action connue, utilisateur, sévérité, fallback inconnu et détails visibles ;
- aucun overflow horizontal observé.

## Incidents de certification

AFTER #1 et #2 ont échoué sur des sélecteurs Playwright ambigus liés au DOM responsive. Le harness a été corrigé sans code produit.

AFTER #3 a ensuite révélé le vrai défaut produit à 1024 px (`1196 > 1024`). Le correctif final est limité à deux breakpoints Tailwind : cartes `xl:hidden`, table `hidden xl:block`.

## Score visuel

**9,6/10**.

Forces : lecture praticien nettement meilleure, détails explicites, fallback technique honnête, responsive propre sur cinq viewports, zéro perte d’information.

Réserve : à 1024 px la page Réglages globale conserve une composition assez verticale, mais le Journal d’Audit lui-même reste lisible, stable et sans overflow.

## Statut

**CLOSED — CERTIFIÉ — MERGED**.

Avancement chantier après merge : **7/15 = 46,7 %**.

Aucun déploiement Vercel.
