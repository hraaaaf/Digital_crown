# DIGITAL CROWN — CÉPHALOMÉTRIE DIAGNOSTIQUE

**FICHIER CANONIQUE DE REPRISE**

## POINTEUR COURANT

- **Fenêtre :** R18 — concordance scientifique source-strict + tracés par analyse.
- **Repo :** `hraaaaf/Digital_crown`.
- **Branche :** `fix/cephalo-r18-source-strict-concordance`.
- **PR :** #494 — `fix(cephalo): source-strict R18 scientific concordance`.
- **Candidate produit certifié :** `39660fa45471dbcd8c773148172ec03a854c931f`.
- **État canonique au moment de ce commit documentaire :** **CANDIDAT CLOSEOUT PRÉ-MERGE**. Ne déclarer R18 mergé/clos qu'après CI du HEAD documentaire, merge #494 et vérification `master` post-merge.
- **Canonical détaillé R18 :** `docs/CEPHALO_R18_SCIENTIFIC_CONCORDANCE.md`.
- **Audit scientifique/UX R18 :** `docs/audits/CEPHALO_R18_SOURCE_STRICT_TRACING.md`.
- **Handover R18 → R19 :** `docs/handovers/2026-09-14-cephalo-r18-final-handover.md`.
- **Archive canonique pré-R18 :** `docs/archive/CEPHALO_DIAGNOSTIC_SPEC_PRE_R18.md`.

L'archive pré-R18 est une copie blob-exacte du précédent fichier canonique complet. Elle conserve les contrats détaillés historiques R0→R17 ; le présent fichier est volontairement recentré sur la reprise fiable, les invariants et le pointeur courant.

## PROTOCOLE R / FENÊTRES — OBLIGATOIRE

À compter de R16 :

- **1 fenêtre de conversation active = 1 numéro R distinct** ;
- une fenêtre conserve son R jusqu'à son closeout ou handover ;
- toute nouvelle fenêtre prend le R suivant, même si le sujet fonctionnel continue ;
- chaque R possède scope, état, preuves Git/CI, handover final et prompt de reprise ;
- **un R n'est pas clos tant que le handover final et le prompt de la fenêtre suivante n'existent pas** ;
- reprise : `lire AGENTS.md → STATE.md → ce canonical → handover courant → vérifier master/HEAD/PR/CI → agir` ;
- aucune feature suivante n'est inventée pour remplir la numérotation.

## GOAL GLOBAL

`cas patient → image → landmarks → constructions → mesures → analyses → findings → synthèse diagnostique → problem list → objectifs → options thérapeutiques → validation praticien → plan final`

## INVARIANTS NON NÉGOCIABLES

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

- donnée absente ou géométrie non calculable → `UNKNOWN` / `NOT_COMPUTABLE`, jamais faux `0` ;
- mesure, norme et interprétation restent séparées ;
- `EVALUABLE != selected` ;
- `BLOCKED != DROPPED` ;
- validation finale R14 uniquement avec preuve praticien autoritaire ;
- aucune norme, classe, diagnostic, indication ou traitement n'est inventé ;
- aucune source legacy ou renderer ne devient autorité clinique par commodité ;
- toute migration scientifique garde version/provenance explicites.

## GATE SCIENTIFIQUE / CLINIQUE / ARCHITECTURE

Toute décision significative modifiant un contrat scientifique, clinique ou UX doit préserver :

1. **preuve scientifique :** construction/formule/convention explicites et sourcées ;
2. **fail-closed :** géométrie dégénérée ou données manquantes restent indisponibles ;
3. **traçabilité :** IDs/version/source/provenance auditable ;
4. **séparation des couches :** affichage ne change jamais la mesure ;
5. **human gate :** aucune conclusion ou décision thérapeutique autonome.

Une revue interne n'est jamais présentée comme un avis d'expert humain externe.

## DISCIPLINE UI/UX

Tout changement visuel suit :

`BEFORE réel → Goal → référence → implémentation → AFTER mêmes viewports → comparaison → tests → score visuel/HFE`

Viewports de référence : **390 / 768 / 1280+**. Touch, clipping, overflow et lisibilité sont vérifiés proportionnellement au risque. Aucun déploiement Vercel sans autorisation explicite.

## HISTORIQUE R0 → R17

Les contrats détaillés restent dans `docs/archive/CEPHALO_DIAGNOSTIC_SPEC_PRE_R18.md`. Repères de reprise :

- **R0 typed read-path :** PR #400, merge `5f453d906c0562e53c921c683bb16c1a6deb3536`.
- **R10 registre normatif :** candidate `9ffd36306ec6fa09b71d590e078af01db67e6888`, CI #3431, T2 #2411, PR #431, merge `d0bdfc4fa47346f27e432139e6785177da4deef3`, closeout `2ac6ac538c79eb95a3988f2e6da9854b76dbd422`.
- **R11 diagnostic multiaxial :** candidate `6916dee975acb83d13acd540d5d2e4a8f839a478`, CI #3477, T2 #2452, PR #437, merge `bc66b58b6ee4459362d3bd52150877908bdc996c`.
- **R12 problem list + objectifs :** candidate `dc04d759191828afe85c643719165e7d4fcc916e`, CI #3500, T2 #2465, PR #441, merge `02d4be759e4ddbc24293340c6c10848174ace07a`.
- **R13 options thérapeutiques :** candidate `7fd6fdae604010510b74e5fe908dc76a425a71cf`, CI #3526, T2 #2489, PR #444, merge `4740b463e49f8ddee9dbb704faaecd086c389beb`.
- **R14 validation clinique finale :** candidate `017a7eaf7d293c5a7af19fb44987a2d5ff3f675c`, CI #3581, T2 #2536, PR #447, merge `2f1f1d88bf6027988a398967bed5e65883b729aa`.
- **R15 Studio clinique :** candidate `f70d62df584a38a7deb8341dc608ad14274c3dec`, CI #3783, T2 #2715, PostgreSQL #230, PR #458, merge `258762da7aff8e7fd481990e96f32b761d635234`.
- **R15bis refinement UI/UX :** candidate `89c852bf95426623b942a90823db69bc85501b10`, CI #3856, T2 #2784, PostgreSQL #299, score 9,62/10, PR #477, merge `127ed256c690f8cc9464bee68b8cd26c29f4129a`.
- **R17 restitution PDF autoritaire :** candidate `58dcd4bfa2901f36e3d9b30e97629c87db89f80b`, CI #3931, T2 #2850, PostgreSQL #365, P3 #37, PR #481, merge `f0aafd9278791becdc6980e3804022231553cfd7`, handover `docs/handovers/2026-09-14-cephalo-r17-final-handover.md`.

## R18 — CONCORDANCE SCIENTIFIQUE SOURCE-STRICT + TRACÉS

### Goal

Pour une même téléradiographie et les mêmes landmarks :

`convention scientifique versionnée = calcul backend = calcul frontend = construction graphique visible = preuve d'audit`

### Décisions scientifiques verrouillées

- angles de rayons/axes robustes par produit scalaire + `acos`, fail-closed sur géométrie dégénérée ;
- Steiner U1/NA et L1/NB : angles d'axes ;
- distances Steiner U1-NA / L1-NB en mm : `NOT_COMPUTABLE` tant que le landmark coronaire requis n'existe pas ; aucun substitut silencieux par bord incisif ;
- conventions CRANIOM explicitement obtuses : supplément clinique conservé après calcul robuste de l'angle de base ;
- Ricketts E-line V1 historique reste lisible ; V2 active utilise la plus courte distance/perpendiculaire à Prn-Pog', Frankfort ne servant qu'à l'orientation du signe ;
- IDs E-line V2 versionnés ; snapshots V1 non réécrits ;
- `RICKETTS_FACIAL_AXIS_DEG_V1` reste bloqué tant que sa convention de landmarks n'est pas source-lockée.

Références R18 enregistrées dans le code/audit : DOI `10.1016/S0002-9416(68)90278-9`, PMCID `PMC6007603`, `PMC10973926`, `PMC12569150`.

### Preuves mathématiques

Candidate produit : `39660fa45471dbcd8c773148172ec03a854c931f`.

- `Cephalo R18 Scientific Concordance Audit` #19, run `34889128107` : **SUCCESS** ;
- hard gate : `concordance_certified=true`, **0 divergence** ;
- première certification source-strict : run `34881504311` / #5, 0 divergence sur 90 comparaisons.

### BEFORE UI figé

- workflow `Cephalo R18 Tracing BEFORE` #3, run `34882384184` : **SUCCESS** ;
- product HEAD `26d0aaf7c1b674227de310715ef35ccf27c82c04` ;
- viewports `390x844`, `768x1024`, `1280x900` ;
- sélecteur absent, constructions superposées ;
- artifact `10362879498` ;
- digest `sha256:586528cc04dbf3e90ae71ea71e65a89542c48f6cfeeda333adbbf005d3412954`.

### AFTER UI final candidat

- workflow `Cephalo R18 Tracing AFTER` #7, run `34889128064` : **SUCCESS** sur `39660fa45471dbcd8c773148172ec03a854c931f` ;
- artifact `10365503287` ;
- digest `sha256:7dc74cfeb29f18158d817d987fa33345498fc543528b81a1a89d69016146b804` ;
- mêmes viewports 390/768/1280 et même fixture déterministe que BEFORE ;
- modes `Tous / Steiner / Tweed / McNamara-COM / Ricketts` ;
- `invalidCount=0`, zéro erreur page/console, zéro overflow horizontal ;
- 390 : les cinq modes sont simultanément visibles ; `McNamara / COM` est abrégé `COM` uniquement sur mobile ;
- score visuel/HFE après inspection réelle : **9,4/10**.

### Architecture tracés

- moteur historique conservé dans `CephaloTracingLayerBase.tsx` ;
- contrôleur R18 dans `CephaloTracingLayer.tsx` ;
- filtrage des landmarks/ghosts et constructions par analyse ;
- corrections manuelles d'un sous-ensemble fusionnées dans le jeu complet ;
- Ricketts : profil cutané/E-line + constructions dures disponibles ;
- McNamara/COM : Wits et constructions dédiées ;
- sélecteur R18 local au viewer : aucune fausse synchronisation avec `etape3Data.selectedAnalysis` n'est revendiquée.

### Certifications complémentaires candidate produit

Sur `39660fa45471dbcd8c773148172ec03a854c931f` :

- T2 Runtime Browser #2992 : **SUCCESS** ;
- PostgreSQL #507 : **SUCCESS** ;
- Cephalo R15 AFTER #86 : **SUCCESS** ;
- Cephalo R15bis AFTER #47 : **SUCCESS** ;
- M6-I #1792 : **SKIPPED**, attendu pour ce scope ;
- CI générale #4081 était encore en cours avant le commit documentaire de closeout ; la CI du HEAD documentaire devient l'autorité pré-merge.

## NEXT EXACT

1. Certifier le HEAD documentaire de closeout : CI générale + R18 scientific + R18 AFTER et certifications pertinentes.
2. Vérifier PR #494 : mergeable, reviews/threads, drift `master`.
3. Merger #494 uniquement après gates verts.
4. Vérifier `master` post-merge et SHA réel.
5. Enregistrer le merge réel dans le closeout documentaire si nécessaire.
6. R19 est uniquement la prochaine fenêtre procédurale ; aucune nouvelle feature céphalométrique n'est pré-planifiée sans instruction explicite.

## SÉQUENCE RESTANTE

`HEAD documentaire vert → merge #494 → master post-merge vérifié → closeout final R18 → R19 procédural uniquement`

## DÉPLOIEMENT

Aucun déploiement Vercel effectué ni autorisé dans R18.
