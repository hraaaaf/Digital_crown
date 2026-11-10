# LOT08.2-I — SRPose38 embarqué, activation clinique interdite par défaut (non-clinical LAB)

## Décision / objectif

**Décision propriétaire :** conserver SRPose38 comme modèle de céphalométrie et **l'embarquer à terme dans l'installable Desktop**. Le propriétaire traite séparément les droits et questions juridiques ; **ne pas relancer ce sujet comme prérequis aux travaux techniques internes**.

**Risque technique prioritaire :** `sota_vision_service.py` initialise actuellement SRPose38 à l'import. Une installation contenant simplement `srpose38-tta-1024.onnx` pourrait donc activer l'inférence sur de vrais patients, malgré l'absence de mapping anatomique officiellement validé. `vision_service.py` peut aussi initialiser CephLD-CCA PyTorch en fallback. Le contrôle d'intégrité des 267 Mo seul n'est pas un GO clinique.

**Goal du lot :** rendre impossible l'activation automatique céphalo dans une application figée PyInstaller / environnement de cabinet, même lorsque le modèle est présent, tout en préservant les laboratoires synthétiques strictement isolés. Empêcher les analyses vides/refusées de produire des dossiers persistés. **Aucune activation clinique et aucune suppression de modules.**

## Contrat d'exécution proposé

`backend/services/cephalo_runtime_gate.py` est un contrôle **stdlib-only** indépendant de la présence des poids :

- **DENY** systématique dans un exécutable figé (`sys.frozen` ou `sys._MEIPASS`), même avec des variables `ENVIRONMENT=test` trompeuses ;
- **DENY** dans tout environnement autre que `test` / `rehearsal` ; donc `production`, `development`, absence d'environnement ;
- **DENY** si `DIGITALCROWN_ISOLATED_RUNTIME` n'est pas explicitement `1` ou `true` ;
- **ALLOW LAB uniquement** : base `sqlite:///:memory:` avec isolation explicite ; ou SQLite sur runner GitHub Actions lui-même avec `GITHUB_ACTIONS=true`. Une base cabinet locale persistante et un simple opt-in utilisateur ne permettent pas d'activer une inférence ;
- la vérification a lieu **avant** chargement ONNX (`SOTAVisionEngine._initialize_engine`), **à chaque inférence** (`SOTAVisionEngine.predict_landmarks`, `VisionEngine.predict_landmarks`) et **avant fallback PyTorch** (`VisionEngine._initialize_legacy_engine`). Les changements d'environnement en cours de session ne réactivent pas une instance déjà chargée ;
- `CephaloService.process_new_radio` refuse une liste de repères vide avec erreur explicite avant toute requête ou écriture DB ; le routeur `upload_radio` supprime déjà le média temporaire en cas d'exception.

**Ce verrou est un HOLD temporaire intentionnel**, et non une politique clinique d'activation définitive. Toute future activation produit nécessitera une décision et des preuves propres à Digital Crown, dont la fiabilité anatomique. Ne jamais le remplacer par une simple variable `CEPHALO_AUTO_ENABLED=1` sans gate médicale autorisée. Il n'empêche pas les flux manuels distincts déjà existants.

## Success observable / preuve exigée

- Scope GitHub : uniquement les **8 fichiers** annoncés, sans modèle, patient, migration, modification d'installateur ni fusion.
- TEST Linux : environnement production même avec ONNX et flags d'activation → aucun chargement/session, aucune lecture patient ni fallback ; un moteur refusé retourne `FAILED` + repères vides + avertissement.
- TEST Windows GitHub hébergé : processus simulé figé `sys.frozen` et `sys._MEIPASS` refuse même les flags LAB.
- TEST backend : entrée synthétique SQLite mémoire autorisée en laboratoire ; refus du dépôt/écriture lorsqu'aucun repère valide.
- Régression : tests SRPose38 geometry/runtime, lazy PyTorch, persistance Céphalo et apex, plus suites CI candidate. Aucun patient réel.
- Ne pas publier ni retélécharger ONNX pour ce lot : **LOT08.2-H** a déjà validé les octets réels du modèle, sa sortie CPU 38 canaux et le sélecteur PyInstaller au [run #42910489876](https://github.com/hraaaaf/Digital_crown/actions/runs/42910489876), 2/2 SUCCESS ; méta-preuve [#13805984797](https://github.com/hraaaaf/Digital_crown/actions/runs/42910489876/artifacts/13805984797) sans poids.

## Limites et prochain jalon

La correction modifie le code de l'application : **le CODE_CERTIFIED précédent sur master SHA bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4 ne certifie pas cette branche**. Les tests verts d'une PR DRAFT ne rendent pas un installable utilisable. Aucun merge, déploiement, publication de modèle ou activation clinique sans gates explicitement autorisés.

**Next technique après succès de cette PR :** préparer un essai *Windows Desktop jetable* avec l'ONNX intégré à une candidate de laboratoire mais avec inférence bloquée, puis produire la preuve que le package contient effectivement le modèle avec son hash, sans publier les poids ni l'installateur. En parallèle, le propriétaire gère ses droits ; l'évaluation scientifique des 38 identités anatomiques J1.B1 reste un gate médical distinct.

**Statut de cette PR : LAB DRAFT — NO_INSTALLABLE_GO / clinical_release=false.**
