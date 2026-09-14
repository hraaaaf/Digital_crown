# HANDOVER — DIGITAL CROWN / CÉPHALOMÉTRIE — R18 FINAL

**Date :** 2026-09-14  
**Repo :** `hraaaaf/Digital_crown`  
**Canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Canonical détaillé R18 :** `docs/CEPHALO_R18_SCIENTIFIC_CONCORDANCE.md`  
**Branche produit :** `fix/cephalo-r18-source-strict-concordance`  
**PR produit :** #494  
**Candidate produit certifié :** `39660fa45471dbcd8c773148172ec03a854c931f`  
**État de ce handover :** préparé avant merge ; compléter/revérifier le SHA de merge réel après #494.

## GOAL R18

Aligner strictement la céphalométrie scientifique et sa preuve visuelle :

`convention source/versionnée → calcul backend → calcul frontend → construction graphique correspondante → audit reproductible`.

Chaque analyse doit pouvoir être inspectée sans constructions étrangères, tout en conservant un mode global `Tous`.

## SUCCÈS PRODUIT OBSERVÉ

Sur le candidate produit `39660fa45471dbcd8c773148172ec03a854c931f` :

- Cephalo R18 Scientific Concordance #19 / run `34889128107` : **SUCCESS** ;
- concordance : `concordance_certified=true`, **0 divergence** ;
- Cephalo R18 Tracing AFTER #7 / run `34889128064` : **SUCCESS** ;
- artifact AFTER `10365503287` ;
- digest AFTER `sha256:7dc74cfeb29f18158d817d987fa33345498fc543528b81a1a89d69016146b804` ;
- T2 Runtime Browser #2992 : **SUCCESS** ;
- Cabinet Upgrade PostgreSQL #507 : **SUCCESS** ;
- Cephalo R15 AFTER #86 : **SUCCESS** ;
- Cephalo R15bis AFTER #47 : **SUCCESS** ;
- M6-I #1792 : **SKIPPED**, attendu pour ce scope ;
- reviews/comments/threads PR #494 : aucun élément bloquant observé avant le commit documentaire ;
- PR #494 : `mergeable=true` avant le commit documentaire ;
- aucun déploiement Vercel.

La CI générale #4081 du candidate produit était encore en cours au moment de préparer le commit documentaire. Le HEAD documentaire doit donc être certifié à son tour avant merge.

## CONTRAT SCIENTIFIQUE R18

### Géométrie fail-closed

- rayons/axes : produit scalaire + `acos` ;
- géométrie dégénérée : indisponible, jamais faux `0°` ;
- suppression de l'autorité implicite `atan2 % 180` là où elle produisait wrap/supplément erroné.

### Steiner

- U1/NA et L1/NB : angles d'axes ;
- U1-NA et L1-NB linéaires : `NOT_COMPUTABLE` sans landmark coronaire requis ;
- aucun substitut silencieux via bord incisif.

### CRANIOM

Les mesures définies comme obtuses conservent explicitement leur supplément clinique après calcul robuste de l'angle de base.

### Ricketts E-line

- V1 historique reste lisible et non réécrit ;
- V2 active : plus courte distance/perpendiculaire à Prn-Pog' ;
- Frankfort sert à l'orientation du signe, pas à la direction de mesure ;
- IDs/méthodes V2 versionnés ;
- références enregistrées : DOI `10.1016/S0002-9416(68)90278-9`, PMCID `PMC6007603`, `PMC10973926`, `PMC12569150`.

### Limite volontaire

`RICKETTS_FACIAL_AXIS_DEG_V1` reste bloqué tant que la convention de landmarks n'est pas source-lockée.

## BEFORE / AFTER UI

### BEFORE figé

- run `34882384184` / #3 : SUCCESS ;
- HEAD `26d0aaf7c1b674227de310715ef35ccf27c82c04` ;
- 390x844 / 768x1024 / 1280x900 ;
- sélecteur absent, constructions superposées ;
- artifact `10362879498` ;
- digest `sha256:586528cc04dbf3e90ae71ea71e65a89542c48f6cfeeda333adbbf005d3412954`.

### AFTER final candidat

- run `34889128064` / #7 : SUCCESS ;
- HEAD `39660fa45471dbcd8c773148172ec03a854c931f` ;
- artifact `10365503287` ;
- digest `sha256:7dc74cfeb29f18158d817d987fa33345498fc543528b81a1a89d69016146b804` ;
- 15 captures, mêmes viewports et même fixture ;
- `invalidCount=0` ;
- zéro page/console error ;
- zéro overflow ;
- cinq modes valides : Tous, Steiner, Tweed, McNamara-COM, Ricketts.

### Correction mobile

Le premier AFTER a révélé un vrai conflit tactile 390 entre le badge calibration et le sélecteur. Le sélecteur a été déplacé sous l'en-tête mobile, puis `McNamara / COM` a été abrégé en `COM` uniquement sous `sm` afin de garder les cinq choix simultanément visibles. Le harness n'a pas été assoupli pour cacher le défaut.

### Score visuel/HFE

**9,4/10** après inspection réelle des captures 390 / 768 / 1280. Les vues par analyse sont nettement plus lisibles et cohérentes. Le mode `Tous` reste volontairement dense comme vue d'inspection globale.

## ARCHITECTURE TRACING

- moteur historique inchangé dans `frontend/src/features/ortho/CephaloTracingLayerBase.tsx` ;
- contrôleur R18 dans `frontend/src/features/ortho/CephaloTracingLayer.tsx` ;
- filtre landmarks + ghosts + constructions par analyse ;
- corrections manuelles fusionnées dans le dataset complet ;
- constructions Ricketts dures et Wits ajoutées sans modifier les calculs ;
- sélection de tracing locale au viewer ; aucun faux couplage avec `etape3Data.selectedAnalysis`.

## ARCHIVE CANONIQUE

Le canonical historique complet pré-R18 est conservé blob-exact dans :

`docs/archive/CEPHALO_DIAGNOSTIC_SPEC_PRE_R18.md`

Le fichier courant `docs/CEPHALO_DIAGNOSTIC_SPEC.md` est recentré sur les invariants, les repères historiques et la reprise R18/R19.

## CLOSEOUT R18 RESTANT

1. certifier le HEAD documentaire créé avec ce handover ;
2. vérifier PR #494 : mergeable, reviews/threads, master courant ;
3. merger #494 si tous les gates requis sont verts ;
4. vérifier `master` post-merge et le SHA réel ;
5. mettre à jour le closeout documentaire avec le merge réel si nécessaire ;
6. aucun déploiement Vercel.

## Y A-T-IL UN R19 ?

**Aucune feature R19 fonctionnelle n'est pré-planifiée.**

Le protocole `1 fenêtre = 1 R` impose toutefois que toute nouvelle fenêtre de reprise prenne R19. R19 est donc uniquement une fenêtre procédurale tant qu'aucune instruction utilisateur ou source canonique ne définit un nouveau chantier.

## PROMPT COMPLET DE REPRISE R19

Tu es dans une nouvelle fenêtre de conversation : **R19 — reprise contrôlée post-R18**.

1. Lire `AGENTS.md`, puis `STATE.md`, puis `docs/CEPHALO_DIAGNOSTIC_SPEC.md`, puis `docs/handovers/2026-09-14-cephalo-r18-final-handover.md`.
2. Vérifier avant toute modification :
   - repo `hraaaaf/Digital_crown` ;
   - `master` courant ;
   - PR #494 et son état réel ;
   - candidate produit R18 `39660fa45471dbcd8c773148172ec03a854c931f` ;
   - SHA de merge R18 réel si #494 est mergée ;
   - runs R18 finaux et éventuel closeout documentaire post-merge ;
   - présence sur master de `docs/CEPHALO_R18_SCIENTIFIC_CONCORDANCE.md` et de ce handover.
3. Préserver les invariants : `landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`, fail-closed, `NOT_COMPUTABLE` reste indisponible, `EVALUABLE != selected`, `BLOCKED != DROPPED`, aucune conclusion clinique ou thérapeutique fabriquée.
4. Ne jamais réinterpréter silencieusement Ricketts E-line V1 ; toute nouvelle convention reste versionnée.
5. Ne pas réintroduire les linéaires Steiner U1-NA/L1-NB sans landmark coronaire source-locké.
6. Ne pas présenter `RICKETTS_FACIAL_AXIS_DEG_V1` comme certifié sans source-lock de sa convention de landmarks.
7. **Aucune nouvelle feature céphalométrique n'est pré-autorisée.** Identifier le prochain chantier uniquement depuis une instruction explicite utilisateur ou une source canonique existante.
8. Si aucun nouveau chantier n'est défini, ne modifier aucun code.
9. Aucun déploiement Vercel sans autorisation explicite.

**Goal R19 procédural :** vérifier le closeout R18 réel puis reprendre uniquement sur un chantier explicitement défini.  
**Succès :** master/PR/CI/docs concordants ; soit prochain chantier explicite identifié, soit absence de chantier confirmée.  
**Preuve :** SHAs/PR/runs/docs exacts revérifiés au début de la fenêtre.

## NEXT EXACT

Certifier le HEAD documentaire R18, merger #494 si vert, vérifier master post-merge, puis enregistrer le SHA réel dans le closeout.

## DÉPLOIEMENT

Aucun déploiement Vercel effectué ni autorisé.
