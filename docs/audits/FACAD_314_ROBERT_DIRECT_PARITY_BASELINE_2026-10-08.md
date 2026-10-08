# Facad 3.14 Quick Demo ↔ Digital Crown — preuve d'éditeur et baseline de parité

**Date :** 2026-10-08  
**Statut :** INVENTAIRE DIRECT OBSERVÉ + AUDIT DE CODE DIGITAL CROWN ; **PARITÉ CLINIQUE NON VALIDÉE**  
**Périmètre :** échantillon **Robert Example** distribué avec Facad Quick Demo. Aucune donnée d'un patient réel, aucun changement clinique, aucun contournement de licence.  
**Branche d'exploration :** `feat/cephalo-facad-direct-parity-runtime-probe`.  
**CI :** [run #37841266986](https://github.com/hraaaaf/Digital_crown/actions/runs/37841266986), **SUCCESS** sur commit `03220c036ebc65896ff5fd307a4e0d74ac063d52` ; artefact GitHub Actions **#11578251769**, `facad-314-quick-demo-bootstrap-03220c036ebc65896ff5fd307a4e0d74ac063d52`.

## 1. Preuves directes — Facad, pas inférences marketing

Artefacts du run, dans l'archive : `robert-open-probe.txt`, `robert-after-screen.png`, `clinical-tracing-probe.txt`, `pretreatment-after-screen.png`, `pretreatment-after-ui-tree.txt`, `clinical-menu-probe.txt`, `menu-{file,edit,view,tools,help}-screen.png`, `menu-{file,edit,view,tools,help}-items.txt`.

- **Séquence observée** : dossier d'exemple Robert ouvert → Image/Tracing manager → vignette Pretreatment tracing double-cliquée → deux fenêtres internes : **Pretreatment tracing … Tracing** et **Pretreatment tracing … Analysis**.
- **Preuve instrumentée** : `MANAGER_WINDOW_COUNT=1`, `PRETREATMENT_LABEL_COUNT=2` (deux doublons superposés), `PRETREATMENT_DEDUPED_LABELS=2`, `PRETREATMENT_LABEL_DOUBLE_CLICKED=true` ; arbres UIA après interaction exposant réellement les deux fenêtres et les lignes de mesures.
- **Capture AFTER** : téléradiographie latérale d'exemple à droite avec contours et repères rouges, traits de constructions noirs ; fenêtre d'analyse à gauche contenant l'analyse intitulée **Bergen short**, tableau `Ceph name / Value / Norm / Unit / Dev O`, puis tableau `Name / Sag [mm] / Ver [mm] / Rot [°]` (mouvements et landmarks). Onglets **Values** et **Properties**.
- **Cinq menus inspectés sans sélection d'action** : File, Edit, View, Tools, Help ; `MENU_*_COUNT=1`, `MENU_*_CAPTURED=true` pour chacun. Les entrées capturées par menu et les captures visuelles sont annexées à l'artefact. Les menus **Tracing, Cephalometry, Image, Window** sont visibles dans la barre, mais leurs sous-menus **non encore explorés**.
- **Actions observées dans les menus** (la présence n'atteste pas le succès opérationnel) : `File > New/Edit ceph analysis…, Edit report, Print report, Save patient` ; `View > Analysis, Original positions, Planned positions, Generate predicted photo, Predicted photo` ; `Tools > Calibrate…, Measure, Plan, Split hard tissue, Reset planned movement, Get rotation center`.
- **Barre d'outils UIA** : `{FCD_Calibrate}`, `{FCD_Measure_distance}`, `{FCD_Measure_angle_3pt_Par}`, `{FCD_Plan}`, `{FCD_Split_hard_tissue}`, `{FCD_Place_marker}`, `{FCD_Draw_hard_tissue}`, `{FCD_Blend_images}` ; présence uniquement, aucune validation de calcul ou sauvegarde.
- **Interdiction méthodologique** : ni ce run vert ni une capture unique ne certifient la validité des mesures, l'exactitude normative, la précision des landmarks, l'équivalence Facad↔Digital Crown, les fonctions de prédiction ni une supériorité UX.

## 2. Données de mesure relevées, exemple fourni par Facad

Toutes les valeurs ci-dessous sont **affichées par l'interface Facad**, non recalculées. Les « Norm » sont celles **affichées par le profil Bergen short**, **sans validation scientifique/populationnelle** et ne doivent jamais être importées automatiquement dans Digital Crown.

| Libellé Facad | Valeur affichée | Référence affichée | Unité | Digital Crown : identité candidate et limites |
|---|---:|---:|---|---|
| SNA | 67,7 | 82 ± 3 | ° | `M_SNA_DEG_V1` — identité nommée ; accord sur données communes non testé |
| SNB | 78,4 | 80 ± 3 | ° | `M_SNB_DEG_V1` — idem |
| ANB | −10,7 | 2 ± 2 | ° | `M_ANB_DEG_V1` — idem |
| SNPog | 80,8 | 81 ± 3 | ° | définition et convention à identifier ; aucune assimilation automatique à un autre angle |
| NSBa | 126,8 | 130 ± 5 | ° | géométrie/identité source à vérifier |
| ML/NSL | 33,9 | 32 ± 4 | ° | **ne pas assimiler** silencieusement à GoGn–SN : plan mandibulaire exact non vérifié |
| NL/NSL | 4,5 | 8,5 ± 3 | ° | plan palatin/nasal et convention à verrouiller |
| ML/NL | 29,4 | 23,5 ± 5 | ° | construction et angle exacts à verrouiller |
| InterIncisal | 140,9 | 130 ± 10 | ° | `M_INTERINCISAL_DEG_V1` : candidat, axes/conventions à comparer |
| ILs/NSL | 100,1 | 102 ± 6 | ° | axe incisif sup./SN à qualifier, **différent a priori d'U1/NA** |
| ILi/ML | 85,1 | 94 ± 4,5 | ° | `M_IMPA_GOME_DEG_V1` : candidat **non équivalent sans preuve du plan ML** |
| Pog-NB | 4,7 | 4 ± 2 | mm | `M_POG_NB_MM_V1` existe ; identité anatomique explicitement requise |

Vérification arithmétique interne limitée : `67,7 - 78,4 = -10,7`. Cela confirme seulement la cohérence des **trois chiffres affichés** ; ni landmark, ni construction ni protocole certifiés.

## 3. Base Digital Crown — sources effectivement lues sur `master`

Source code lue sur l'arbre GitHub `master@c3b094d8e5e8ba52ca40e7521927c0c5d60326a9` :

- [`frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx`](../../frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx) : modes `all, steiner, tweed, mcnamara, com, ricketts` ; lignes Steiner et Tweed avec IDs `M_*` ; lignes `Co_A`, `Co_Gn`, `ANS_Me` sur McNamara, `Ligne_E_Ls`, `Ligne_E_Li` sur Ricketts. Les identifiants de lignes ne constituent pas une preuve qu'elles calculent toutes une valeur.
- [`backend/services/cephalo_engine.py`](../../backend/services/cephalo_engine.py) : moteur déterministe de géométrie brute, sans normes/diagnostic automatiques. Présence de SNA/SNB/ANB, mais **pas de preuve de calcul sur l'exemple Facad**.
- [`backend/services/cephalo_measure_registry.py`](../../backend/services/cephalo_measure_registry.py) : registre des mesures canoniques et statuts de provenance ; `M_POG_NB_MM_V1` reste marqué `GEOMETRY_COVERED_EXPLICIT_IDENTITY_REQUIRED`.
- [`frontend/src/features/ortho/CephaloWorkspace.tsx`](../../frontend/src/features/ortho/CephaloWorkspace.tsx) : workflow « Céphalométrie → Moulages → Synthèse clinique → Documents & stratégie » et historique. C'est une **architecture produit différente** du bureau Facad à deux fenêtres ; ni meilleure ni moins bonne sans étude d'usage comparée.
- [`frontend/src/features/ortho/components/Step1CephaloBase.tsx`](../../frontend/src/features/ortho/components/Step1CephaloBase.tsx) et [`CephaloTracingLayerBase.tsx`](../../frontend/src/features/ortho/CephaloTracingLayerBase.tsx) : VTO interactif/overlays via offsets d'images/points. Le libellé UI actuel `SIMULATION PRÉDICTIVE EN TEMPS RÉEL` dépasse les garanties du contrat de visualisation ; **ne pas présenter un simple déplacement graphique comme une prédiction validée**.
- [`docs/audits/CEPHALO_VNEXT_LOT06_SCALABLE_ANALYSIS_ARCHITECTURE.md`](CEPHALO_VNEXT_LOT06_SCALABLE_ANALYSIS_ARCHITECTURE.md) : packs extensibles par registre, appartenance `PROVISIONAL_MEMBERSHIP` et non approbation scientifique générale.
- [`docs/audits/CEPHALO_SCIENTIFIC_COMPLETENESS_AUDIT.md`](CEPHALO_SCIENTIFIC_COMPLETENESS_AUDIT.md) : dette scientifique source-lock, normes UI historiques et nécessité d'un human gate ; **attention au risque de fuite normative des overlays**.

## 4. Matrice fonctionnelle, niveaux de preuve stricts

Légende : **FACAD OBSERVÉ** = visible sur capture/UIA ; **FACAD MENU SEUL** = commande accessible, comportement non testé ; **DC CODE** = présence dans le dépôt uniquement ; **NON TESTÉ** = impossible d'affirmer la parité.

| Capacité | Facad, preuve | Digital Crown, preuve disponible | Conclusion |
|---|---|---|---|
| Radiographie latérale + tracé superposé | **FACAD OBSERVÉ** : capture pretreatment AFTER | **DC CODE** : tracing SVG et workspace | Parité visuelle **NON TESTÉE** à même image/viewport |
| Mesures + colonnes valeurs/normes/écarts | **FACAD OBSERVÉ** : Bergen short et 12 mesures | **DC CODE** : Workbench, mesures canoniques, référence séparée | Noms communs ≠ géométrie, normes ou interprétations équivalentes |
| Tracés landmark / tissus durs et mous | **FACAD OBSERVÉ** : overlays rouges, liste de landmarks | **DC CODE** : calques et reticles | Précision et complétude anatomique **NON TESTÉES** |
| Mouvements planifiés par structures en mm / rotation en ° | **FACAD OBSERVÉ** : table `Sag / Ver / Rot`, lignes Mandible, Maxilla, incisives, molaires, etc. | **DC CODE** : états VTO et déplacements schématiques | **Écart de workflow à étudier**, pas équivalence clinique |
| Positions originales et planifiées simultanées | **FACAD MENU SEUL** et cases cochées dans View | **DC CODE** : projections T1/T2 présentationnelles et overlays | Confrontation graphique sur fixture commune requise |
| Analyse personnalisée | **FACAD MENU SEUL** : New/Edit ceph analysis | **DC CODE** : architecture générique 401 packs testés, membership provisoire | Personnalisation runtime **NON TESTÉE** |
| Rapport/édition/impression | **FACAD MENU SEUL** : Edit report, Print report | **DC CODE** : étape Documents & stratégie et PDF | Workflow + fidélité de sortie **NON TESTÉS** |
| Predicted photo | **FACAD MENU SEUL** : Generate predicted photo | **DC CODE** : VTO et ghost face | **Aucune prédiction clinique validée** des deux côtés par cette investigation |
| Contrôles de zoom/mesure/calibration | **FACAD MENU SEUL / UIA toolbar** | **DC CODE** : calibration et studio | Test de précision / conservation d'échelle requis |

## 5. Priorités et gates pour la suite

**P0 — Safety / sémantique clinique**
1. Digital Crown : ne pas qualifier le VTO graphique de « prédictif » sans modèle et validation ; mettre une formulation **simulation illustrative, non prédictive** tant que la chaîne scientifique manque. Ne pas modifier ici sans lot produit dédié.
2. Garder les normes Facad *Bergen short* strictement dans la colonne « affichées par Facad » : jamais source normative Digital Crown sans contexte population/âge/sex/source versionnée.
3. Valeurs Facad *Robert* ≠ « golden truth ». Pas de conclusion de parité numérique avant import autorisé du même cas, calibration, landmarks comparables, conventions identiques, revue humaine.

**P1 — Fonctionnalité clinique / UX**
4. Inventorier les menus **Tracing / Cephalometry / Image / Window** par **lecture passive** (un seul run d'exploration si vraiment nécessaire) et l'onglet Analysis Properties.
5. Définir fixture commune non personnelle, provenance et droits d'utilisation ; comparer d'abord trois mesures robustes **SNA/SNB/ANB** puis, seulement si définitions et points validés, interincisal et autres.
6. Comparer sur captures réelles aux **mêmes viewports** la capacité à poser, corriger, visualiser un point, retrouver une ligne et expliquer une mesure ; mesurer clics/temps/erreurs sous protocole.
7. Vérifier le workflow de `planned positions` de Facad **sans sauvegarder**, établir la distinction observé/plannifié/simulé, puis adapter une cible Digital Crown sans promesse clinique exagérée.

**P2 — Complétude et rapports**
8. Analyser rapport Facad sur exemple uniquement et comparer information/provenance/PDF avec le document Digital Crown, sous autorisation d'usage.
9. Étendre la matrice des analyses à partir de sources primaires, **sans transférer automatiquement** valeurs/normes, et en conservant états `UNKNOWN / NOT_COMPUTABLE`.

**Gate de fermeture du benchmark :** même fixture autorisée, comparaison visuelle réelle et données calibrées, protocoles scientifiques vérifiés, tests de non-régression exécutés, revue indépendante ou « revue indépendante interne » explicitée, zéro défaut significatif, preuves AFTER à même HEAD. Pour ce lot, seule la **baseline de navigation/observation Facad** est fermable.

## 6. Deux perspectives adversariales — revue documentaire interne

- **A : validité clinique** — BLOCKER si tableau de valeurs observées traité comme protocole scientifique, si `ML/NSL` est assimilé à `SN-GoGn`, si `ILi/ML` est déclaré Tweed-équivalent, si normes importées ou si « predicted photo »/VTO devient prédiction revendiquée. Ces amalgames sont explicitement interdits dans cette baseline.
- **B : preuve/automation** — BLOCKER si un CI vert remplace la capture d'éditeur, si la présence d'un menu est considérée comme une fonctionnalité testée, si des ressources privées/patient réel sont utilisées ou si un run de plus redémarre Windows sans objectif nouveau. Source + artifact, portée et limites sont explicites.

**Résultat :** inventaire direct Facad et crosswalk de code Digital Crown **documentés** ; **parité numérique, scientifique, UX et rapport = OUVERTE**. Aucune modification de runtime, aucun merge ni déploiement.
