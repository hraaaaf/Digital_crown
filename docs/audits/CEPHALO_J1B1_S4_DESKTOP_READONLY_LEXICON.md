# CEPH J1.B1-S4 — Affichage du lexique 38 + 2 dans la revue manuelle Desktop

Statut : **PR DRAFT / SOURCE_LOCK_REQUIRED / NON CLINIQUE / NO MERGE**.

## GOAL

Afficher dans l'écran **Step1 Desktop** le catalogue de revue des repères SRPose38 :
- **38** canaux (index réseau 0–37 / n° challenge 1–38) avec noms FR/EN et synonymes du registre scientifique S3, y compris les sept associations numérotées explicitement citées par les organisateurs ;
- **2** constructions supplémentaires `Occ_Ant` et `Occ_Post` : pas des canaux du réseau, pas de conversion ou de création automatique ;
- recherche localisée, statut de présence de coordonnées sur le tracé *sans prétendre que le point est validé*, repère actif simplement indiqué ;
- **aucune action d'édition depuis le lexique**, aucun calcul/diagnostic, aucun enregistrement, aucune API ni modification des coordonnées ; le mécanisme existant d'édition manuelle reste inchangé.

## BEFORE → Goal → implémentation → AFTER

**BEFORE sur la base [PR #1284 DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1284) à SHA `dbc714355a5d0eda832e2e2006237b4d7136335e` :** le catalogue scientifique S3 existe en JSON/Markdown mais n'est pas accessible dans le workbench Step1. Les 38 étiquettes et les deux IDs occlusaux existent déjà dans `REQUIRED_LANDMARKS`; ne pas inventer deux canaux neuronaux.

**AFTER candidat S4 :** contrôle `<details>` replié par défaut dans la barre latérale Step1 Desktop, libellé « Lexique des 38 repères · FR/EN » ; panneau accessible au clavier, recherche FR/EN/synonymes/ID, liste défilante avec noms, code, provenance textuelle et état « Coordonnée chargée (non validée) » ; mention explicite **« aucun point automatique certifié cliniquement »**. L'entrée « Pos » retrouve `Pog_soft`, mais ne la certifie pas comme sortie anatomique du checkpoint. `Occ_Ant` / `Occ_Post` sont dans leur propre section « constructions », indépendants des 38 canaux du modèle.

**Priorité UX :** ne pas masquer les radiographies, respecter la disposition de la barre latérale Desktop et l'ergonomie des 40 libellés. Le panneau reste fermé par défaut.

**Vérifications visuelles :** diff BEFORE/AFTER du code + tests DOM accessibles ; **captures de navigateur réelles aux mêmes viewports non produites dans ce lot tant qu'un workflow de rendu n'est pas prouvé**. Aucune note visuelle inventée. Avant tout merge, demander/rechercher une preuve de captures Desktop représentative et revue humaine si le gate UI l'exige.

## SUCCESS / PROOF technique cible

1. Parser les 38 entrées de `frontend/src/features/ortho/cephaloLandmarkReviewLexicon.ts` et comparer intégralement index, ID, FR/EN, synonymes, catégorie de preuve aux **38 JSON scientifiques S3** : interdiction des faux noms, swaps, doublons et preuves abusives. Vérifier strictement la composition existante `REQUIRED_LANDMARKS = 38 détecteur + 2 occlusaux`.
2. Vitest composant : rendu 38+2, recherche FR/EN/synonyme `Pos`, surlignage simple actif, état « coordonnée présente non validée », recherche sans résultat, aucune mutation des coordonnées ni commande clinique dans le panneau.
3. Vitest intégration réelle du wrapper Step1 : composant monté dans la barre latérale, pli fermé à l'ouverture puis ouverture par clic/keyboard.
4. Source-guard 7 tests négatifs : index permuté, ID falsifié, traduction inventée, fausse preuve d'auteur, synonyme enlevé, canal manquant et politique clinique changée → échec fermé.
5. Build frontend/test ciblé GitHub Linux et Windows ; fail-closed si CI échoue. Aucune donnée de patients ou ONNX dans ce lot.

## Portée & portes humaines

Ce lot reste sur une branche DRAFT empilée sur PR #1284→#1282→#1281→#1276, distincte du durcissement clinique DRAFT #1277. Un lexique de noms, même complet, **ne valide pas** la vérité anatomique/accuracy de SRPose38. Aucune nouvelle mesure diagnostique, ni activation automatique, ni autorisation d'utiliser des patients réels. `backend/scientific_assets.json` : `anatomical_mapping_validation=SOURCE_LOCK_REQUIRED`, `clinical_activation_authorized=false` inchangés. Aucun installateur ni déploiement et aucune fusion.

Fichiers canoniques : `docs/audits/CEPHALO_J1B1_S3_38_LANDMARK_TERMINOLOGY.json` pour la science ; `frontend/src/features/ortho/cephaloLandmarkReviewLexicon.ts` pour le rendu UI vérifié en CI ; ce document pour les preuves de S4.
