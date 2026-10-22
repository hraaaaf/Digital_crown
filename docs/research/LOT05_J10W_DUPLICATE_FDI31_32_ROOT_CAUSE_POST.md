# LOT05/J10W — POST / diagnostic des 28 radiographies à revoir, FDI31/32 et faux positifs

**22 octobre 2026 — Recherche académique isolée.** Ce rapport utilise les seuls labels YOLO textuels de la source AKUDENTAL et les agrégats expérimentaux J10V ; **aucune lecture clinique des images ni preuve de licence commerciale n'a été obtenue.** Aucune image, aucun identifiant d'examen, aucune coordonnée de boîte individuelle et aucun nom de fichier de radiographie ne figurent dans le présent rapport.

## Sources vérifiées et provenance

- Upstream `melihoz/AKUDENTAL@92e2cc3ae5eebc9de509311a3edefb7106fca7dd`, 333 radiographies source réparties dans le fold_0 : **266 train / 33 val / 34 test**.
- [J10W — diagnostic réel de tous les 333 labels](https://github.com/hraaaaf/Digital_crown/actions/runs/39874616585) : **SUCCESS**, source épinglée et clonée en *sparse-checkout TXT uniquement*. Audit J10W sur code SHA `7f3e6d09a81b184b89dd0f292e21b676aa8c8827`. Six tests intégralement synthétiques **PASS**. Aucun téléchargement de pixels. Nettoyage `J10W_TEMPORARY_SOURCE_LABELS_REMOVED` confirmé.
- [J10V — vraie évaluation val + test interne](https://github.com/hraaaaf/Digital_crown/actions/runs/39873048174) : 96 train ×3 époques, 33 val, 34 test interne, test **non indépendant par patient**. Ces 34 exemples test ont **déjà été consultés** pour analyse d'erreurs ; ne pas réutiliser leurs scores pour sélectionner/régler un modèle puis présenter le même test comme un *test intact*.

## 31 doublons FDI : **30/31 paires spatialement disjointes**

Calcul IoU entre toutes les boîtes ayant le **même label FDI sur la même image** :

| Mesure | Valeur exacte |
|---|---:|
| Images signalées | **28 / 333** |
| Instances excédentaires de même FDI | **31** |
| Paires examinées | **31** |
| IoU < 0,30 (boîtes séparées ou faiblement chevauchantes) | **30** |
| 0,30 ≤ IoU < 0,70 | **0** |
| IoU ≥ 0,70 (boîtes fortement superposées) | **1** |
| Médiane de l'IoU des paires | **0** |

Répartition déjà confirmée : entraînement **25 anomalies dans 23 images** ; validation **3 dans 3** ; test interne **3 dans 2**. Contrairement à la présomption initiale, la majorité des doublons **ne sont pas deux boxes identiques superposées**. Deux régions différentes portent la même numérotation FDI. Cela peut provenir d'une erreur de numérotation, d'une condition anatomique ou d'une convention source particulière : **impossible de trancher à partir des seules coordonnées**. Aucune classe ni dent ne doit être corrigée/supprimée automatiquement.

La seule paire IoU ≥ 0,70 est aussi **non adjugée médicalement** : son signal de recouvrement peut représenter une erreur de création de polygones ou autre cause. La revue doit rester humaine et être documentée sur un poste local privé.

## FDI31/32 : la rareté des annotations est réfutée, taille proche des controlatérales

| FDI | Train : instances | Validation : instances | Test : instances | Aire médiane bbox normalisée |
|---|---:|---:|---:|---:|
| **31** | **254** | **30** | **31** | **0,0029362** |
| **32** | **259** | **32** | **31** | **0,0035112** |
| 41 (controlatérale) | 253 | 31 | 31 | 0,0029586 |
| 42 (controlatérale) | 257 | 31 | 32 | 0,0035440 |
| 11 (incisive maxillaire) | 255 | 30 | 31 | 0,0054132 |
| 12 (incisive maxillaire) | 253 | 32 | 31 | 0,0043359 |

L'aire 31 ≈ 41, et 32 ≈ 42 ; **ni manque de données d'entraînement ni petitesse relative à la controlatérale n'expliquent à elles seules l'échec 31/32**. Les incisives inférieures sont cependant plus petites que les supérieures en coordonnées normalisées, et le détecteur MobileNetV3 320 px peut manquer de finesse spatiale : hypothèse, pas preuve.

Analyse J10V du *test interne 34 images* (IoU ≥0,5, score ≥0,25) :
- **FDI 31 :** 0 vrai positif exact / 31 GT, **0 prédiction portant FDI31 au seuil**. En appariement spatial indépendamment du label, **2 GT FDI31 seulement** furent localisées : prédites FDI32 (1) et FDI41 (1).
- **FDI 32 :** 0 vrai positif exact / 31 GT ; **24 faux positifs portant FDI32**, 1 GT FDI32 localisée spatialement mais prédite FDI33.
- **FDI 41 :** 12 vrais positifs exacts et 19 manqués / 31 GT ; **FDI 42 :** 3 TP / 29 FN (32 GT). Le problème affecte largement la région incisive mandibulaire, bien que de façon asymétrique.

**Ne pas diagnostiquer à ce stade une inversion automatique gauche/droite ou un bug de mapping :** ces hypothèses nécessitent contrôle humain de l'orientation et des annotations source. Le mapping FDI 0–31 → 11–48 et le décalage +1 pour le fond du modèle ont déjà des tests structurels, mais pas de validation clinique d'orientation.

## FDI24 : faux positifs et confusions avec la prémolaire voisine

| FDI | Train | Val | Test | Nombre de FP sur test J10V au seuil 0,25 |
|---|---:|---:|---:|---:|
| **24** | **221** | 30 | 31 | **70** |
| 25 | 216 | 28 | 25 | **42** |

J10V : parmi les dents GT **FDI25 spatialement localisées**, **13 ont été classées FDI24**, confusion fréquente, alors que FDI24 a 15 TP exacts sur le test interne. Cela suggère une confusion locale entre prémolaires voisines, **non une simple absence de classe**. Ne pas choisir un filtre/NMS/calibrage à partir des résultats des 34 images test ; réserver réglages aux 33 images de validation, puis **obtenir une nouvelle cohorte indépendante**.

## Préparer réellement la revue des 28 radiographies sans les exposer

Le script `experiments/lot05_j10w_akudental_duplicate_fdi_root_cause.py` fournit l'option **`--private-review-manifest`**. À exécuter **seulement sur un poste privé autorisé** avec les 333 labels en local, et une destination JSON locale inexistante. Le fichier contiendra la liste de **28 cas numérotés à revoir**, split et étiquettes FDI répétées ; **ne jamais le placer dans GitHub, Actions, Notion, un chatbot ou des logs publics**.

```bash
python experiments/lot05_j10w_akudental_duplicate_fdi_root_cause.py \
  --labels-dir /recherche/AKUDENTAL/AKUDENTAL/folds/fold_0/labels \
  --private-review-manifest /dossier_prive/revue_fdi_a_confirmer.json
```

**Protocole dentiste :** ouvrir chaque panoramique et ses deux boîtes FDI de même classe sur station privée, vérifier (a) convention droite/gauche et miroir, (b) présence / absence, nombre et anatomie des dents, (c) dent incluse, surnuméraire, transposition, images incertaines et contexte cliniquement plausible, (d) position et précision de chaque polygone ou bbox. Pour chacun, consigner **validé / anomalie probable / indéterminé** et la raison par le professionnel ; ne jamais autocorriger les vérités terrain ou exploiter les patients du cabinet pour ce projet.

## Statut et prochain jalon

**QA DOCUMENTAIRE ET GÉOMÉTRIQUE TERMINÉE, REVIEW CLINIQUE 0/28.** Entraîner plus longtemps ou changer la résolution avant de comprendre les erreurs de régions incisives et prémolaires pourrait seulement sur-ajuster le corpus. Le test interne de 34 images a été *consommé analytiquement* ; toute amélioration doit être sélectionnée sur validation, puis vérifiée sur **un autre test indépendant**. Licence des données **CC BY-NC-SA 4.0** déclarée ; aucune autorisation commerciale acquise. **PR DRAFT ; pas de merge, pas de Vercel/Production ni modèle clinique distribué.**
