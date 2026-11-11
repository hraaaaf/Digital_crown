# Digital Crown — LOT08.2-H — SRPose38 : octets réels et sélection PyInstaller (LAB uniquement)

## Décision

**Objectif :** déterminer si le véritable modèle **SRPose38** peut être obtenu depuis l'artefact historique GitHub, vérifié au niveau des octets, chargé par ONNX Runtime CPU et **sélectionné pour l'intégration Desktop** selon la même politique que `DigitalCrown.spec`. Le cabinet utilisateur **ne doit pas** télécharger ni fournir un ONNX séparément : une distribution légale devra embarquer les assets dans l'installable.

**Périmètre autorisé par GO :** tests sur runner GitHub hébergé jetable ; pas de copie de patients ; pas de build d'EXE ; pas de bundle de redistribution ; pas de merge, de déploiement ni de démarrage clinique.

## Provenance et identités gelées

- SHA CODE_CERTIFIED du master : `bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4` ; [run officiel #42897412850](https://github.com/hraaaaf/Digital_crown/actions/runs/42897412850) 6/6 SUCCESS ; [ZIP CODE #13802971225](https://github.com/hraaaaf/Digital_crown/actions/runs/42897412850/artifacts/13802971225), SHA256 ZIP `4302e9d3b22cf71b40619587d597c8939dddf4199d5322714f6e3851c9f611f4`. Code signé par GitHub Sigstore ; re-vérification indépendante de la signature exigée avant composition officielle.
- Source poids existante (ne pas publier à nouveau) : [GitHub Actions #34281082926](https://github.com/hraaaaf/Digital_crown/actions/runs/34281082926), artifact `cephalo-srpose38-onnx-parity` ID `10077697721`, ZIP SHA256 d'après API GitHub `ad1caa8ee1474a1405305fc91a29eaa3c0c5b20572095faad0c2e63723284e17`.
- Fichier attendu dans l'archive : `srpose38-tta-1024.onnx`, 267484931 octets, **SHA256 du fichier** `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb` ; un hash de ZIP n'est pas un hash du modèle.
- Registre scientifique : `backend/scientific_assets.json` ; `cephalo_sota` épinglé à cet ONNX ; `cephalo_legacy` et `panoramic` non épinglés. On ne fabrique aucun pin manquant.

## Succès attendu du LAB (pas une certification commerciale)

- Contrôler run source GitHub SUCCESS, artifact ID/nom/digest/existence et SHA master certifié inchangé.
- Télécharger le ZIP existant **uniquement** dans `$RUNNER_TEMP` ; refuser les noms supplémentaires, symlinks, mauvaise taille ou mauvais SHA du modèle.
- Vérifier le registre et le contrat du runtime et le **même sélecteur** `iter_runtime_asset_files` utilisé dans `DigitalCrown.spec`, sur une copie **éphémère** ; pas de working tree ni d'installateur modifié.
- Charger l'ONNX réel avec `CPUExecutionProvider` sur entrée zéro synthétique ; confirmer une sortie de 38 heatmaps et des valeurs finies. Aucun landmark de patient et aucune prétention de précision diagnostique.
- Ne publier **que** un petit rapport de métadonnées JSON. Ne jamais attacher l'ONNX, le bundle de modèles, une image ou du patient à la PR/artifacts du nouveau run. Effacer les octets téléchargés et les fichiers temporaires après l'exécution.

## Risques non levés et arrêt obligatoire

La licence **Apache-2.0 du code source ne prouve pas la redistribution commerciale des poids externes**. `docs/audits/CEPHALO_VNEXT_LOT04_SRPOSE38_LICENSE_AUDIT.md` reste `WEIGHT_LICENSE_EXPLICITNESS_UNRESOLVED`. La roadmap Céphalo J1.B1 et [PR #1276 DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1276) notent l'absence de preuve source index→nom anatomique des 38 canaux ; les 21 réassignations historiques restent sans certification.

En conséquence, même si le LAB est vert : **aucun ZIP runtime distribué, aucun `INSTALLABLE_CERTIFIED`, aucune activation de céphalo automatique clinique**. Les modèles ONNX sont destinés à être embarqués **lors d'une future composition légalement autorisée et validée**, mais les tests techniques ne remplacent ni consentement du titulaire des poids, ni cartographie anatomique, ni validation médicale.

**NEXT exact après succès labo :** obtenir l'accord explicite de redistribution du checkpoint modèle exact ; clarifier les modèles `cephalo_legacy`/`panoramic` réellement nécessaires et leur provenance ; vérifier Sigstore hors CI sur le code certifié ; construire ensuite un bundle runtime ciblant **le même SHA** via `backend/scripts/certify_runtime_assets.py` et composer l'`INSTALLABLE_CERTIFIED` selon `backend/scripts/create_release.ps1` sans l'activer. Toute installation en VM et a fortiori clinique restera soumise à gate humaine.
