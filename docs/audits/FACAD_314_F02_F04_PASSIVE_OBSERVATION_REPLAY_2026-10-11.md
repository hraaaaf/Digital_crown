# FACAD 3.14 — F02.2 / F02.3 → F04.1 : replay probant des surfaces passives (2026-10-11)

**Périmètre :** reverse engineering fonctionnel **observable et autorisé**, par relecture d'artefacts Windows réels existants. **PAS une nouvelle session FACAD**, ni une interaction sur le poste Robert (OFFLINE), ni un test de calcul. Aucune modification produit Digital Crown.

## Sources exactes, contrôle d'intégrité

| Source | SHA du ZIP vérifié après téléchargement | Contenu |
|---|---|---|
| [run Windows #37964215530](https://github.com/hraaaaf/Digital_crown/actions/runs/37964215530), artefact #11632079894 | `0ea15aa6bed1794ad656cd5a25cab41d322889aedbd2a0bc82576393f719` | F02.2 ancienne observation de menu |
| [run Windows #37967170536](https://github.com/hraaaaf/Digital_crown/actions/runs/37967170536), artefact #11634502406 | `e8db415cda6c4dbc27cdca1eaa25bd6f6200a95a428c902726998a4fc79c1574` | 47 membres ; F02.2 + F02.3 ; captures UIA/PNG 1024×768 |

La seconde archive a été **téléchargée, ouverte et relue** le 2026-10-11, avec analyse du CSV UIA des 30 commandes applicatives, des données F02.2, de quatre snapshots UIA BEFORE/AFTER, de 6 captures PNG et du manifeste de contrôle de l'exemple officiel. Le collecteur hors-ligne a fait échouer ses assertions en cas de compteurs, libellés, garde-fous ou stabilité non conformes. Les tests de relecture passent ; ils **ne remplacent pas des interactions non exécutées**.

**Source UIA :** 4 snapshots F02.2/F02.3 avant/après sont strictement identiques octet-par-octet (SHA256 `1cdd845f2400d11b94a49091e838fb6124f55cb811f004196076cf89ed4f308d`). Les images sont aux mêmes 1024×768 ; les captures après fermeture de menu ne sont pas un test de toggle. Sur cette session déjà exécutée, le manifeste indique `SOURCE_UNCHANGED_AFTER_F02_2=True` et `COPY_UNCHANGED_AFTER_F02_2=True` pour le cas d'exemple. **L'isolation du stockage applicatif reste `UNVERIFIED`**, donc ce constat ne permet aucune édition.

## F02.2 — Marker guide / Planned positions : OBSERVÉS, comportement INCONNU

| Commande View | Activée UIA | Visible UIA | TogglePattern | Action feuille |
|---|---|---|---|---|
| Marker guide | True | True | **On** | **Aucune** |
| Planned positions | True | True | **On** | **Aucune** |

Les deux lignes sont authentifiées dans `f02-2-targets.csv` (verdict `UIA_OBSERVED_NO_LEAF_CLICK`). Leurs états `On` sont des valeurs d'interface et ne prouvent pas qu'une activation changerait/laisserait stable l'affichage de tracé. `F02_2_VISUAL_BEHAVIOR_PROVEN=false`. Le jalon F02.2 demeure **OPEN**.

## F02.3 — Tracing / View : deux menus effectivement ouverts, rien activé

- Menu **Tracing** : **10 commandes applicatives** recensées, dont Tracing information, New tracing, Duplicate tracing, Select tracing, Close tracing, Close other tracings, Close all tracings, Allow multiple tracings open, Detach profile photo, Lock. Deux entrées système additionnelles sont exclues du décompte.
- Menu **View** : **20 commandes applicatives** recensées, dont Image/Tracing manager, Tracing image, Profile photo, Analysis, Harmony box, Generate predicted photo, Predicted photo, Original positions, Planned positions, Marker guide, Image, Image #2, Profile, Hard tissue, Markers, Marker names, Ceph/Lines, Bindings, Toolbars, Status bar. Deux entrées système exclues.
- Sur les captures réelles F02.3 `f02-3-tracing-menu.png` et `f02-3-view-menu.png`, les entrées ci-dessus sont visibles ; aucune commande feuille sélectionnée. `LEAF_CLICK_INVOKED=false`, `SAVE_INVOKED=false`, `PATIENT_LOAD_INVOKED=false`, `F02_3_FULL_VISUAL_BEHAVIOR_PROVEN=false`.

**Conclusion :** preuve robuste de la disponibilité des commandes, **pas** de leur effet, ni de la gestion des couches soft/teeth, superpositions ou simulation. F02.3 demeure **OPEN**.

## F04.1 — Nouveau sous-inventaire passif, uniquement ce qui est visible

Le panneau d'analyse de l'exemple officiel affiche deux onglets `ControlType.TabItem`, **Values** et **Properties**, dans **7 fichiers UIA** chacun, sans activation de l'onglet Properties pendant ce lot.

Les libellés d'exposition `Analysis Values`, `Analysis Properties`, `Marker Positions` et `Object Values` ne figurent pas sous leur nom exact comme `ControlType.MenuItem` dans les captures passives consultées. **C'est `NOT_OBSERVED_IN_PASSIVE_MENU_CAPTURE`, pas la preuve que FACAD ne propose pas ces fonctions.** Il faudra ouvrir leurs surfaces de prévisualisation en environnement démontré sûr (aucun Save/Export). F04.1 reste **OPEN_PARTIAL**.

## Deux revues adversariales internes — pas de revue indépendante humaine

**A / Provenance & science : 8/10** pour le catalogue de commandes source-pinné et le refus explicite d'inventer leur résultat ; **0/10** pour conventions mathématiques, export numérique ou parité fabricant. Danger : traiter l'état UIA `TogglePattern On` comme comportement exécuté ; bloqué.

**B / Sécurité & observabilité : 7/10** pour les captures et hashes BEFORE/AFTER du bundled example, 0 clic feuille, 0 Save/Load ; **3/10** pour couverture *fonctionnelle complète* F02/F04. Danger : assimiler la stabilité du fichier exemple à une isolation de stockage ; bloqué. Le runner était jetable, le poste distant actuel est **OFFLINE**. Aucun nouveau Windows run produit ici.

**Verdicts :** `F02.2=OPEN`, `F02.3=OPEN`, `F04.1=OPEN_PARTIAL`, `FAC03_D3=OPEN_RED`, `CLINICAL_EDIT_ALLOWED=false`, `FAC05=NOT_TESTED`, `CONVERGED=false`. Roadmap FACAD **19/39=48,7 %**, globale **39/99=39,4 %**, inchangées.

## Prochain essai ayant de la valeur

Sur FACAD Quick Demo officiel autorisé et poste **sûr**, isolé, sans patient et sans opérations de sauvegarde : relever les contrôles `Values/Properties`, `Marker Positions/Object Values`, montrer BEFORE/AFTER sur les **mêmes 1024×768**, capturer UIA et classify effects ; essayer les commandes de changement d'état seulement **si restauration et non-interférence D3 sont démontrées**, sinon rester en observation passive. Archiver et vérifier hashes ; ne jamais assimiler menu inventorié à comportement validé.

**L'apport de ce lot est un registre d'observation réutilisable, non un pourcentage gagné sans critère complet.**
