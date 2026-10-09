# HANDOVER CANONIQUE — Digital Crown / Facad 3.14 Quick Demo

**Date de capture :** 2026-10-09 (Africa/Casablanca).  
**Projet :** Digital Crown — benchmark produit, interface et céphalométrie face à Facad.  
**Repo :** [hraaaaf/Digital_crown](https://github.com/hraaaaf/Digital_crown).  
**Branche de travail :** `feat/cephalo-facad-direct-parity-runtime-probe` (ne pas merger).  
**HEAD de départ du handover :** `159946de89f31a3de7b099d1ef063d40701b398b`. **Après publication de ce fichier, relire le HEAD réel : il sera différent.**  
**Notion canonique :** page ID `3f377c663362817a8578e59905c65f66`.  
**Priorité de vérité :** repo actuel / scripts réels et runs GitHub + artefacts > notes Notion > handover ; ne pas inventer un résultat.

## 0. À FAIRE EN PREMIER — reprise sans recommencer

1. **Ne pas repartir de zéro, ni refaire les campagnes D0, D1B ou D2B déjà certifiées.** Lire CE document, le HEAD de branche, les scripts et les artefacts référencés. En cas de divergence entre ce document et les preuves, privilégier les preuves récentes.
2. **Consulter avant toute modification** le run McNamara D1C [#37862652488](https://github.com/hraaaaf/Digital_crown/actions/runs/37862652488), HEAD `159946de89f31a3de7b099d1ef063d40701b398b`. Au contrôle initial du **2026-10-09 00:02 UTC**, statut `in_progress` pendant l'installation du Quick Demo, **aucun artefact**. Ne pas dire green sans le vérifier.
3. Si terminé, récupérer son artefact `facad-314-d1c-McNamara-<SHA>`, examiner `d1c-editor-pilot-status.txt`, `d1c-editor-pilot.csv`, `d1c-McNamara-{measurements,lines,markers}.png` et `d3-app-copy-probe.txt`. **Un job vert ne vaut pas preuve de contenu** ; vérifier l'éditeur nommé McNamara, les vues capturées, `SAVE_BUTTON_NOT_INVOKED=true`, les deux hashes source/copie identiques avant et après.
4. Si McNamara réussit, **clore seulement le pilote D1C de trois définitions** (Steiner, Tweed, McNamara), pas les 65 analyses calculées. Concevoir l'extension d'inventaire des **62 autres définitions** avec isolation d'une définition par éditeur frais, preuve screenshot + UIA, sans charger de résultat dans le patient ni sauvegarder.
5. Si McNamara échoue, analyser la cause en artefacts/logs, corriger **la plus petite zone** (harness uniquement), relancer sur nouveau HEAD et fournir l'URL exacte du nouveau run. Ne pas re-jouer l'inventaire D0/D2B.
6. Documenter l'état dans Notion en **PRE/POST, maximum deux notes**, avec résultat/preuve/blocage/Next. Aucun merge ou déploiement sans accord.

## 1. COMMENT / OÙ FACAD EST INSTALLÉ

**Logiciel exact :** **Facad Quick Demo 3.14.1.1111**, application Windows native tierce (pas une dépendance Digital Crown et pas installée sur l'ordinateur personnel de l'utilisateur par ce projet).

**Installateur réellement utilisé (source officielle dans le workflow) :**  
`https://downloads.citodent.com/pub/Facad/Facad-Installer-3.14.1.1111.exe`

**Environnement :** job GitHub Actions **`windows-latest`** du workflow  
[.github/workflows/facad-314-quick-demo-bootstrap.yml](../../.github/workflows/facad-314-quick-demo-bootstrap.yml).

Le job : 
- analyse la syntaxe PowerShell des scripts **avant** installation (gate `Parser.ParseFile`) ;
- télécharge l'installeur ci-dessus dans `facad-quick-demo/Facad-Installer-3.14.1.1111.exe` ;
- extrait avec **7-Zip** `facad-quick-demo/outer/FacadNstaller.exe` et lance **uniquement « Quick demo installation »** dans l'interface ;
- cherche le `Facad.exe` installé sur le runner (cherche dans `C:\Program Files`, `C:\Program Files (x86)`, `C:\Facad`; ne pas supposer un emplacement fixe) ;
- extrait le paquet officiel `facad-quick-demo/outer/FacadRelease-3.14.1.1111.zip` en `facad-quick-demo/release/` ;
- identifie **l'exemple officiel** `facad-quick-demo/release/Examples/Robert-2.0.fcd` et **copie le répertoire Examples entier** vers `facad-quick-demo/d3-app-copy/` pour conserver les références relatives ;
- démarre `Facad.exe` **sur la COPIE** `facad-quick-demo/d3-app-copy/Robert-2.0.fcd`, et NON l'exemple original. Dossier patient de démonstration « Robert Example », radiographie/tracé pretreatment et exemple « Bergen short » ;
- extrait les preuves (captures, CSV, UIA tree, logs, SHA256), disponibles dans l'onglet **Artifacts** du run GitHub.

**Capitalisation essentielle :** les runners GitHub hébergés sont **éphémères**. L'installation physique ne persiste PAS entre deux jobs. Il faut **réutiliser le workflow et son bootstrap automatisé**, pas « retrouver une application installée » sur l'ordinateur de l'utilisateur, et surtout **ne pas redécouvrir comment installer Facad**. Pour gagner du temps, réutiliser les artefacts et tests déjà passés ; n'exécuter qu'un sous-lot non validé. Une optimisation d'une seule installation pour plusieurs sessions éditeur neuves pourra être étudiée, **après** preuve que chaque session et son stockage restent isolés.

**Licence et sécurité :** utiliser uniquement le choix officiel « Quick demo installation » déjà attesté ; ne jamais activer/contourner licence, exploiter une API cachée ou importer un patient réel. Ne pas modifier les sources d'exemples officielles. Vérifier SHA256 avant et après. **Le fichier identique ≠ isolation des autres bases/fichiers de Facad**, donc `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED` et `CLINICAL_EDIT_ALLOWED=false` restent vrais à ce stade.

## 2. ACQUIS AVEC PREUVES — NE PAS REFAIRE

| Lot | Dernière preuve utile | Ce qui est CERTIFIÉ | Ce qui NE L'EST PAS |
|---|---|---|---|
| D0 inventaire UI | [#37843736004](https://github.com/hraaaaf/Digital_crown/actions/runs/37843736004) **SUCCESS** | 9/9 menus principaux ouverts, 43 boutons UIA recensés et 25 commandes toolbar actives découvertes | pas l'exécution complète de toutes les actions |
| D1 découverte | [#37845377310](https://github.com/hraaaaf/Digital_crown/actions/runs/37845377310) **SUCCESS** ; [référence CSV](data/FACAD_314_D1_LATERAL_STANDARD_65.csv) | liste de **65 noms** d'analyses céphalométriques latérales onglet Standard | aucune validation de leurs calculs |
| **D1B catalogue** | [#37855445127](https://github.com/hraaaaf/Digital_crown/actions/runs/37855445127) **SUCCESS**, artefact #11583882056 | **65/65 éléments individuellement sélectionnés** par `SelectionItemPattern`, 65 captures/CSV ; onglet Local=0, `Cancel` et valeurs du profil Bergen short encore affichées | pas un `Load` clinique des 65 analyses ni leur justesse |
| D1C pilote Steiner | [#37857655276](https://github.com/hraaaaf/Digital_crown/actions/runs/37857655276) run global **FAILURE** | définition **Steiner** chargée et photographiée en éditeur non sauvegardé (1/3) | Tweed empêché dans ce run par modal overwrite ; McNamara non tenté |
| **D1C pilote Tweed** | [#37861203066](https://github.com/hraaaaf/Digital_crown/actions/runs/37861203066) **SUCCESS**, artefact #11585454878 | définition **Tweed** chargée dans un éditeur frais ; captures des onglets `Measurements`, `Lines and calc. points`, `Markers` ; `Save` non appelé, hashes source/copie identiques | ses calculs ou ses normes cliniques non certifiés ; **55/25/126 sont des nombres d'éléments TEXTE UIA**, pas des nombres de mesures |
| D2 visuel | [#37848294942](https://github.com/hraaaaf/Digital_crown/actions/runs/37848294942) **SUCCESS** | changements/restitutions de **Hard tissue, Profile, Ceph/Lines, Status bar** vérifiés par région d'image `BEFORE → AFTER → RESTORE`, retour pixel identique dans la zone testée | pas une preuve de toutes les 12 options ni de calculs ;
| **D2B inventaire View** | [#37852213309](https://github.com/hraaaaf/Digital_crown/actions/runs/37852213309) **SUCCESS**, artefact #11582837133 | **19/19 entrées View** inventoriées avec captures / états UIA ; deux sous-menus découverts : Markers, Toolbars ; aucun clic sur commande feuille | pas les 19 fonctions exécutées |
| D2C autre preuve visuelle | [#37854309934](https://github.com/hraaaaf/Digital_crown/actions/runs/37854309934) run global **FAILURE** ; [analyse de cause](FACAD_314_D2C_RED_ROOT_CAUSE_2026-10-08.md) | **Original positions** changement visible + restauration exacte dans la région du tracé ; source/copie inchangées | `Marker guide` et `Planned positions` **NON PROUVÉS** visuellement ; `TogglePattern` à `UNKNOWN` |
| D3 préflight sécurité | [#37852213309](https://github.com/hraaaaf/Digital_crown/actions/runs/37852213309), [#37861203066](https://github.com/hraaaaf/Digital_crown/actions/runs/37861203066) | copie jetable de Robert ; empreintes SHA256 original/copie égales avant/après les sessions lecture seule | **isolement applicatif incomplet ; édition, planning, sauvegarde BLOQUÉS** |
| D4 output | — | pas encore exécuté | report / exports / PDF / printing NON TESTÉS |
| D5 Digital Crown vs Facad | — | pas encore exécuté | aucun score de parité clinique ou UX final |

**SHA256 du Robert officiel attesté sur plusieurs runs :** `67A81AD8D2C2489FFE84A1DFBBB897761AE855ECE4EBF948C12AF232562EC089`. Utiliser les hashes **frais du run concerné** pour tout nouveau verdict, jamais une valeur historique comme preuve d'un run futur.

**Note D2 :** les six modes toolbar (SelectMove, Zoom, Measure distance, distance to line, angle 3pt, angle 4pt) ont été activés puis retournés vers SelectMove, **sans clic de mesure sur la radiographie**. Ce sont des smoke tests de mode, pas des mesures calculées.

## 3. SCRIPTS / ASSETS RÉUTILISABLES

- **Workflow unique bootstrap + tests :** `.github/workflows/facad-314-quick-demo-bootstrap.yml`. Trigger : push sur sa propre modification dans la branche, ou `workflow_dispatch`. Les commits de fichiers `docs/` et de scripts sans modification workflow **ne déclenchent pas automatiquement** le workflow du fait du filtre `paths:`.
- **Inventaire D1 :** `docs/audits/data/FACAD_314_D1_LATERAL_STANDARD_65.csv` (65 noms, zéro mesure certifiée).
- **D1B déjà passé :** `scripts/facad_314_d1b_catalog_selection.ps1`.
- **D1C éditeur mono-preset (harness actuel) :** `scripts/facad_314_d1c_editor_pilot.ps1`, paramètre `-ProfileName`, `ValidateSet('Steiner','Tweed','McNamara')`. Actuellement workflow paramétré **McNamara** ; pour étendre aux autres 62, ne pas oublier d'élargir ce `ValidateSet` de manière sûre et de fonder les résultats sur les noms EXACTS du CSV.
- **D2 commandes réversibles :** `scripts/facad_314_d2_view_probe.ps1` et `scripts/facad_314_d2_visual_gate.ps1`.
- **D2B inventaire lecture seule :** `scripts/facad_314_d2b_view_structure.ps1`.
- **D2C état/captures :** `scripts/facad_314_d2c_view_toggle.ps1`; état D2C **ouvert**, ne pas réutiliser `TogglePattern` seul comme oracle.
- **D3 préflight fichiers :** `scripts/facad_314_d3_sandbox_preflight.ps1`; `d3-app-copy-probe.txt` et `d3-sandbox-preflight.txt`.
- **Rapports détaillés précédents :** [D2 preuves](FACAD_314_D2_VISUAL_EVIDENCE_2026-10-08.md), [D2C cause RED](FACAD_314_D2C_RED_ROOT_CAUSE_2026-10-08.md), [ancien plan D2/D3](FACAD_314_D2_D3_READY_PLAN_2026-10-08.md). **Attention : ce dernier document est historiquement daté « PREPARED NOT RUN » et n'est plus le statut courant.**

**Structure d'artefacts à inspecter pour un run D1C :**  
`d1c-editor-pilot-status.txt`, `d1c-editor-pilot.csv`, `d1c-{profile}-selected-before-load.png`, `d1c-{profile}-measurements.png`, `d1c-{profile}-lines.png`, `d1c-{profile}-markers.png`, `d1c-{profile}-measurements-ui.txt`, `d3-app-copy-probe.txt`, `d3-sandbox-preflight.txt`.

**Précautions anti-faux vert :** lire le statut du job ET les artefacts, compter les lignes CSV et PNG, comparer les état et captures exacts. Une capture du catalogue n'est pas une définition chargée ; une définition chargée dans l'éditeur n'est pas un calcul effectué ; les textes UIA ne sont pas une liste de formules validées. Si dialog `Do you want to overwrite existing marker properties?` apparaît, **ne pas confirmer** ; fermer le process jetable et repartir sur un éditeur frais. Ce dialogue a précisément bloqué Tweed lorsque Steiner et Tweed étaient chargés dans le même éditeur.

## 4. ROADMAP RESTANTE, ORDONNÉE PAR VALEUR / SÉCURITÉ

**R0 — Maintenant : McNamara**. Inspecter le run #37862652488 ; attester `EDITOR_DEFINITION_LOADED_NOT_SAVED`, tableaux des onglets et SHA256. Corriger uniquement si nécessaire.

**R1 — D1C exhaustivité des définitions (restant : 62 après les trois pilotes)**. Faire un inventaire standardisé des 65 définitions avec une *vraie granularité métier* : mesures, type linéaire/angulaire, lignes, points construits/landmarks, référentiels et valeurs normales quand exposées. Chaque analyse = statut explicite `DISCOVERED`/`EDITOR_LOADED`/`DEFINITION_EXTRACTED`/`PATIENT_CALC_TESTED`/`PARITY_VERIFIED`; ne jamais confondre ces niveaux. Préférer un harness qui réutilise l'installation Windows mais ouvre **des processus et éditeurs isolés et ne réemploie aucune définition non sauvegardée**, après preuve de non-persistence partagée. Si ce n'est pas démontré, sessions CI fraîches, une analyse par run, sans clic destructif. S'inspirer des trois pilotes sans les refaire.

**R2 — D2 actions restantes**. Cartographier chaque option View restante comme `disabled`, `observable`, `visually reversible`, `modal/layout`, `unverified`. Ne pas attribuer PASS à Marker guide / Planned positions sans changement observable ou autre preuve UIA robuste. Mesures de distance/angle : utiliser uniquement cas de démonstration, après protocole d'isolement approuvé.

**R3 — D3 isolement applicatif**. Vérifier effectivement dossiers, fichiers, bases, registry et autres écritures de Facad pendant ouverture/fermeture d'exemple jetable ; original/copie hashés. **Aucune édition de landmark, planning ni Save** jusqu'à preuve que l'application ne peut altérer l'original ou les données partagées. Le clone `.fcd` seul n'est pas suffisant.

**R4 — D4 outputs réels**. Tests report, cephalometric table, format imprimable/exports, avec preuve de fichiers générés / inspectés, cohérence des unités, mise en page, origine des normes.

**R5 — D5 benchmark Digital Crown**. Auditer vraiment l'application/repo Digital Crown en plus de Facad : pour chaque fonction, `BEFORE → action → AFTER` sur même viewport et même cas; fonctionnalités, métriques, UX, accessibilité et risques cliniques. Comparer seulement des valeurs équivalentes avec calibration/références/landmarks précisés. Prioriser P0/P1/P2 et roadmap canonique. **Pas de score de parité inventé**.

## 5. DOCTRINE ET PORTES DE SORTIE

- **Objectif = preuve observable, pas CI vert de façade.** Toujours rapporter RESULTAT → PREUVE (run SHA + artifact/capture/CSV) → BLOCAGE → NEXT, avec liens de tous runs lancés.
- **Haut risque clinique / conformité :** exemple synthétique officiel uniquement ; aucune norme diagnostique copiée sans source médicale externe ; pas de données patient ni action irréversible.
- **Tests et revue adversariale :** à chaque lot significatif, deux perspectives (automatisation/preuves et clinique/safety) cherchent BLOCKER/MAJOR. Revue interne ≠ reviewer indépendant. `CONVERGED` exige deux revues propres au même HEAD, tests exécutés, preuve AFTER et confirmation.
- **CI gates :** REQUIRED / EXPERIMENTAL / HORS SCOPE. Ne pas élargir automatiquement des tests expérimentaux à des gates required.
- **Notion PRE/POST :** maximum deux notes par lot, avant réponse, avec identifiants et liens. Ce handover est la base de reprise, pas une validation du backlog restant.
- **AUCUN** merge, commit sur master, déploiement Vercel, activation licence, import patient réel ou changement du runtime de Digital Crown sans justification et accord adéquat.

## 6. PHRASE MAGIQUE À COLLER DANS LA NOUVELLE CONVERSATION

> Reprends immédiatement le benchmark **Digital Crown × Facad 3.14** à partir du handover canonique `docs/audits/FACAD_314_HANDOVER_CANONICAL_2026-10-09.md` sur `hraaaaf/Digital_crown`, branche `feat/cephalo-facad-direct-parity-runtime-probe`, et de la page Notion `3f377c663362817a8578e59905c65f66`. **NE RECOMMENCE PAS D0, D1B NI D2B.** Le logiciel Facad Quick Demo 3.14.1.1111 est déjà installable automatiquement dans GitHub Actions Windows via `.github/workflows/facad-314-quick-demo-bootstrap.yml` ; capitalise sur cet installer, les scripts, les runs et les artefacts. **Ta première action** : consulter et analyser le run McNamara **#37862652488**, obtenir ses captures, CSV et SHA256 ; s'il est réussi, clore uniquement le pilote D1C Steiner/Tweed/McNamara puis étendre efficacement l'inventaire des 62 définitions restantes, sans charger ni sauvegarder le patient. Si rouge, corrige la cause exacte et relance le sous-test ciblé ; donne toujours le lien du run. Respecte la séparation définition chargée / calcul clinique / parité, les gates D3 et les preuves BEFORE/AFTER/RESTORE. Mets à jour Notion PRE/POST, fais les revues adversariales, n'attends pas une nouvelle autorisation pour les actions réversibles sûres et **ne merge ni ne déploie**. Fournis directement résultat, preuve, blocage et Next.

---
**Dernier statut du run McNamara intégré dans ce fichier : en cours au premier contrôle de 2026-10-09 00:02 UTC. Ce statut doit être RAFRAÎCHI en reprenant.**
