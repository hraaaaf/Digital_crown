## DIGITAL CROWN — 10/11/2026 ~23:05 UTC — LOT08.2-I UPDATE : VERROU SRPOSE38 NATIF VERT / CODE CANDIDATE EN COURS

**DECISION :** Le propriétaire conserve SRPose38 comme modèle à embarquer dans une future version Desktop et gère séparément les droits juridiques. Le lot courant s'occupe **uniquement** du verrou médical fail-closed et de l'intégrité du packaging ; ne pas demander à nouveau de preuve juridique pour avancer sur des tests techniques sûrs.

**HEAD / périmètre vérifié :** [PR #1279 DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1279) HEAD exact `bafcced99ac7a6fd10fc9074ed0c4061a3485186`, comparé à master `bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4` inchangé : **9 fichiers** bornés (gates services / tests / workflows, `scripts/check_lazy_pytorch_contract.py`, documentation), aucun modèle ONNX ni EXE ni migration, aucune donnée patient ni fusion.

**PROUVÉ sur HEAD exact :**
- [LOT08.2-I PR #42917551538](https://github.com/hraaaaf/Digital_crown/actions/runs/42917551538) et [push #42917542546](https://github.com/hraaaaf/Digital_crown/actions/runs/42917542546) **SUCCESS chacun 3 jobs/3** : source/scope, backend ciblé, déni natif Windows. Le moteur SRPose38 dans le package reste non activé cliniquement ; absence de mode produit override via env ; fallback CephLD-CCA interdit hors LAB et sortie vide non persistée.
- [Portability P5 #42917551523](https://github.com/hraaaaf/Digital_crown/actions/runs/42917551523) **SUCCESS sur Windows et macOS**. Correctifs historiques sans affaiblir le HOLD : test `check_lazy_pytorch_contract` clarifié entre refus clinique total et WinError1455 de PyTorch en LAB isolé ; le message prévoit la pose **manuelle des repères** lorsque le moteur est désactivé.
- Sur SHA exact, dernière inspection globale GitHub : **14 runs SUCCESS, 1 SKIPPED** biométrie, **0 FAILURE**, **1 in_progress** : [Cabinet CODE_CERTIFIED candidate regression #42917551292](https://github.com/hraaaaf/Digital_crown/actions/runs/42917551292). De ce run, PostgreSQL/rehearsal + frontend CI **SUCCESS**, full backend regression encore **in_progress**. C'est une régression candidate, **PAS** le workflow officiel CODE_CERTIFIED et aucun artifact installable.

**Objectif LOT08.2-H acquis indépendamment :** [run #42910489876](https://github.com/hraaaaf/Digital_crown/actions/runs/42910489876) 2/2 SUCCESS sur vrai fichier SRPose38 ONNX, 267484931 octets, SHA256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`, ORT CPU + sélection PyInstaller 1 fichier ; seul rapport métadonnées [#13805984797](https://github.com/hraaaaf/Digital_crown/actions/runs/42910489876/artifacts/13805984797), **sans republier les poids**.

**GATES encore ouverts :** full backend du candidat en cours ; cette PR DRAFT n'est pas fusionnée, son code n'est **pas** CODE_CERTIFIED officiel. Aucune candidate Windows réellement assemblée avec ONNX n'a encore été vérifiée comme packagée. La correspondance scientifique des 38 canaux aux identités anatomiques J1.B1 reste non validée ; aucune activation clinique de la Céphalo autorisée. `LOT08 OPEN / NO_INSTALLABLE_GO`.

**NEXT exact (effort estimé, non %)** : ⚡ inspecter conclusion full backend #42917551292 ; 🟡 préparer une FUE Windows Desktop jetable qui contrôle **le modèle véritable intégré**, le SHA depuis le package et le HOLD auto-inférence avec tests négatifs / sans patients ni publication du modèle ou de l'EXE ; 🟡 traiter les exigences d'un candidat CODE_CERTIFIED sur un master futur après human gate de merge ; 🔴 gate anatomique/usage clinique séparé. Aucun merge, déploiement, installation clinique ou migration sans GO spécifique.

---

## DIGITAL CROWN — 10/11/2026 22:47 UTC — LOT08.2-I HEAD ACTUEL : PLACEMENT MANUEL EXPLICITE / CI EN FILE

**PR DRAFT #1279** HEAD `bafcced99ac7a6fd10fc9074ed0c4061a3485186`, base `master@bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4` (CODE_CERTIFIED officiel SHA identique). Scope 9 fichiers exacts, aucun modèle, EXE, patient ou migration. Verrou d'inférence céphalo : refus dans produit figé `sys.frozen`/`_MEIPASS`, environnements non-LAB, DB non isolée et avant init ONNX/vision/legacy ; CephaloService refuse une sortie vide sans persister. Compromis produit intentionnel : SRPose38 sera embarqué mais ne sera **pas activé en clinique** avant gate médical séparé.

**Correction précédente vérifiée :** P5 ancien HEAD `bf04024` macOS [#42916942362](https://github.com/hraaaaf/Digital_crown/actions/runs/42916942362) FAIL durant `python -m scripts.portability_p5_check --runtime --fail-closed` : `AssertionError: Cephalo missing-model path must require manual placement`. Le test de sécurité attend `manuel` ; message HOLD révisé sur SHA courant ajoute `Placement manuel des repères requis.`, et `test_cephalo_runtime_activation_gate.py` vérifie explicitement l'indication. Aucun assouplissement du gate, aucune activation, aucune suppression de test. Autre ancien échec P5 Windows/macOS WinError1455 déjà corrigé en test LAB isolé sans essais PyTorch en production.

**CI courant encore non conclu** : [P5 #42917551523](https://github.com/hraaaaf/Digital_crown/actions/runs/42917551523), [LOT08.2-I PR #42917551538](https://github.com/hraaaaf/Digital_crown/actions/runs/42917551538), [LOT08.2-I push #42917542546](https://github.com/hraaaaf/Digital_crown/actions/runs/42917542546), [CODE candidate #42917551292](https://github.com/hraaaaf/Digital_crown/actions/runs/42917551292) tous QUEUED ou PENDING lors de ce contrôle. Ne pas attribuer d'anciens SUCCESS au nouveau SHA. CODE_CERTIFIED master reste validé et inchangé ; code candidat non certifié.

**Juridique** : propriétaire prend en charge les droits du checkpoint ; ne pas bloquer les actions techniques internes à ce sujet ni demander une confirmation redondante. Cela ne constitue pas une autorisation de redistribution des octets ni une validation clinique, donc aucun modèle/EXE publié.

**NEXT EXACT** : suivre verdict final 3 jobs dédiés Linux/Windows/backend, P5, CODE candidate sur `bafcced99` ; corriger si rouge, préparer FUE Windows isolé d'empaquetage SRPose38 avec modèle intégré + comportement auto-HOLD et rapport métadonnées seulement. Aucune fusion, installation cabinet, déploiement, migration ou patient réel. `LOT08 OPEN / NO_INSTALLABLE_GO`.

---

## DIGITAL CROWN — 10/11/2026 22:44 UTC — LOT08.2-I : NATIVE PYTORCH CONTRACT SÉPARÉ EN CABINET DENY / LAB WINERROR, CI OUVERTE

**État de code :** [PR #1279 DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1279) HEAD `bf04024ec519db4a285ca4b0b10ed39a63d2f316` sur master `bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4`, inchangé. Diff **9 fichiers ciblés** (4 services backend, test backend, test contrat lazy PyTorch, deux workflows, guide). Pas de modèle ni installateur ni patient réel publié ; aucune migration ou fusion.

**Incident reproductible sur ancien HEAD d28ae9 :** [P5 Native Dependency #42915867686](https://github.com/hraaaaf/Digital_crown/actions/runs/42915867686) échoué sur macOS+Windows à `check_lazy_pytorch_contract.py` ("Legacy fallback attempt was not recorded"). Nouveau verrou clinique empêche l'**essai même** en production, or test précédent supposait un essai. **Réparation non permissive :** `check_clinical_runtime_never_attempts_legacy_pytorch` exige un refus sans import ; `check_winerror_1455_fail_closed` vérifie toujours le legacy *en LAB isolé SQLite in-memory*, import torch retournant WinError 1455, `legacy_init_attempted=True`, `torch/model=None`, `is_ready=False`. Régression initiale ni annulée ni marquée verte.

**CI exact HEAD restant :** P5 [#42916942362](https://github.com/hraaaaf/Digital_crown/actions/runs/42916942362) en cours ; dédié [#42916942438](https://github.com/hraaaaf/Digital_crown/actions/runs/42916942438) PENDING ; push dédié [#42916932317](https://github.com/hraaaaf/Digital_crown/actions/runs/42916932317) QUEUED ; régression CODE candidate [#42916942522](https://github.com/hraaaaf/Digital_crown/actions/runs/42916942522) QUEUED ; zéro échec actuel à ce constat mais **aucun succès global déclaré**. Ancien CODE_CERTIFIED sur master reste intact.

**Règle propriétaire :** gestion des droits légaux par propriétaire, ne pas bloquer tests ni demander d'acte juridique ; ne pas redistribuer les poids ni activer inférence clinique sans validation médicalement fondée. Le modèle prévu est SRPose38 embarqué local, prouvé techniquement LOT08.2-H, mais cette branche n'est ni CODE_CERTIFIED ni INSTALLABLE_CERTIFIED.

**NEXT exact :** vérifier tous les verdicts de ce SHA (Linux/Windows/backend + P5 + candidate), corriger si rouge ; si verts, lancer un FUE de packaging isolé sur runner Windows avec modèle SRPose38 temporaire, signature/hash et interdiction auto-inférence, rapport de preuves métadonnées uniquement. Aucun merge, installation clinique ni déploiement. `LOT08 OPEN / NO_INSTALLABLE_GO`.

---

## DIGITAL CROWN — 10/11/2026 22:35 UTC — LOT08.2-I : CANDIDAT SRPose38 EMBARQUÉ MAIS INFÉRENCE CLINIQUE STRICTEMENT BLOQUÉE — CI PENDING

**Décision/propriétaire** : droits/licences du checkpoint SRPose38 pris en charge par le propriétaire ; poursuivre les travaux techniques sans demander sa validation juridique. SRPose38 reste le poids à embarquer ultérieurement dans l'installable local. Aucun droit de diffusion présumé. La sécurité patient exige que la présence d'un modèle ne déclenche jamais automatiquement une inférence clinique non validée.

**Résultat de code DRAFT (pas VALIDÉ CI)** : [PR #1279](https://github.com/hraaaaf/Digital_crown/pull/1279) HEAD exact `d28ae9aa0d2e22722849d4e88382abe3b568458d` sur master CODE_CERTIFIED `bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4`, toujours inchangé. Diff vérifié **8 fichiers** : module de gate stdlib, SOTA ONNX, Vision/legacy fallback, CephaloService empty nonpersistent, tests synthétiques, parité GitHub isolée, workflow Linux/Windows, guide. Pas de fichiers modèle / installer / patients ni d'écriture clinique.

**Intention de sécurité testable** : `backend/services/cephalo_runtime_gate.py` DENY si `sys.frozen` ou `sys._MEIPASS`, `ENVIRONMENT` autre que `test/rehearsal`, non isolé ou base persistante locale. Seulement test SQLite en mémoire isolé ou SQLite sur runner GH Actions isolé. Verrou présent à la construction, à la prédiction et avant le fallback legacy PyTorch ; CephaloService refuse résultat vide avant persistence. Les variables d'environnement ne sont pas un GO clinique.

**CI** : premier push de workflow [#42915402191](https://github.com/hraaaaf/Digital_crown/actions/runs/42915402191) et ancien workflow parité [#42915404086](https://github.com/hraaaaf/Digital_crown/actions/runs/42915404086) FAILED sans jobs (erreur YAML `DATABASE_URL: sqlite:///:memory:` : deux-points terminal non cité). Reproduit avec parseur YAML et corrigé par valeurs citées. GitHub a reconnu workflow `LOT08.2-I embedded SRPose38 default-deny and no-patient safety FUE` ; [run push #42915861212](https://github.com/hraaaaf/Digital_crown/actions/runs/42915861212) et [run PR #42915867892](https://github.com/hraaaaf/Digital_crown/actions/runs/42915867892) étaient PENDING / aucun job disponible au dernier contrôle. Pas de fausse validation sur ces runs ; suivre Scope, Linux, Windows, targeted backend et CI candidate.

**PREUVE préexistante distincte** : [LOT08.2-H #42910489876](https://github.com/hraaaaf/Digital_crown/actions/runs/42910489876) 2/2 SUCCESS sur SRPose38 réel (267484931 octets, SHA256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`, ORT CPU 38, PyInstaller sélecteur). N'est pas une validation clinique ni INSTALLABLE_CERTIFIED.

**NEXT EXACT** : lire les jobs du nouveau HEAD #1279, diagnostiquer chaque échec. Quand les 3 jobs dédiés + tests produit exact HEAD sont verts, préparer un FUE de véritable empaquetage Desktop Windows isolé, embarquant l'ONNX sans publier poids/installeur et sans l'activer ; aucune fusion, déploiement, migration ou patient réel. `LOT08 OPEN / NO_INSTALLABLE_GO`.

---

## DIGITAL CROWN — 10/11/2026 22:01 UTC — LOT08.2-H FINAL LAB TECHNIQUE VERT / CLINICAL HOLD

**Résultat prouvé :** [PR DRAFT #1278](https://github.com/hraaaaf/Digital_crown/pull/1278) HEAD exact `12668fbe6474c6fa2f577c1212d51dee16d317e8` sur master `bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4` (CODE_CERTIFIED run #42897412850 toujours 6/6 SUCCESS). Compare master→HEAD : **3 fichiers additionnels LAB uniquement** : workflow, script test, document qualité. Aucun code clinique, ni scientific_assets.json, ni DigitalCrown.spec modifié. PR DRAFT/non fusionnée ; master inchangé.

**Preuve principale :** [run GH-hosted push #42910489876](https://github.com/hraaaaf/Digital_crown/actions/runs/42910489876) COMPLETED/SUCCESS **2/2 jobs** sur ce SHA ; run GH pull_request [#42910500771](https://github.com/hraaaaf/Digital_crown/actions/runs/42910500771) SUCCESS. Job source negative-gates PASS ; job original-weight real CPU+packaging selector PASS. Source originelle [#34281082926](https://github.com/hraaaaf/Digital_crown/actions/runs/34281082926) artefact #10077697721, 7 fichiers exacts (ONNX + six documents de provenance/parité) vérifiés et pas de fichiers supplémentaires ; sélection d'**un seul ONNX** dans scratch. Taille mesurée **267484931 octets**, SHA256 réel calculé sur les octets **a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb**. La provenance du ZIP GitHub était `ad1caa8ee1474a1405305fc91a29eaa3c0c5b20572095faad0c2e63723284e17` (différent, ne pas confondre).

**Preuve CPU et sélecteur :** ONNX Runtime `CPUExecutionProvider` uniquement, entrée zéro synthétique **[1,3,1024,1024]**, sortie mesurée **[1,38,1024,1024]**, finie ; source vérificateur canonique `backend/runtime_asset_certification.py` exécuté sans charger le backend ORM, choix identique au sélecteur du packaging PyInstaller, **selected_files=1**, pin `cephalo_sota` vérifié ; `cephalo_legacy` et `panoramic` **toujours non épinglés scientifiquement**. Négatifs nom, mauvaise taille, SHA et symlink PASS. Rapport de métadonnées seulement [artefact #13805984797](https://github.com/hraaaaf/Digital_crown/actions/runs/42910489876/artifacts/13805984797), 761 octets, SHA256 ZIP `d0d136e6105b3ea827ae1e41d2348c0ac919cb7b1974d9598a734a830fbfd5e5`. ONNX source, ZIP poids et rapports bruts ont été effacés du runner ; **aucun poids republié**.

**Historique réel des échecs conservé :** premier run #42906987734 FAILED (supposition un fichier au lieu des sept), run #42908535624 FAILED malgré les sept fichiers + hash réel PASS (import automatique backend → `ModuleNotFoundError: sqlalchemy` dans runner minimal). Correctif de stratégie : charger *exactement* les modules source stdlib-only requis sans lancer `backend/__init__` ni installer toute l'ORM ; même sélecteur productif exécuté avec succès sur #42910489876. Aucun assouplissement hash/validité et aucun placeholder de modèle.

**BLOCAGE réel / décision sécurité :** SRPose38 doit être inclus dans la distribution Desktop **uniquement après validation légale et clinique**. Licence de redistribution commerciale des poids externes `WEIGHT_LICENSE_EXPLICITNESS_UNRESOLVED`. Mapping 38 canaux vers identités anatomiques J1.B1 non sourcé ([PR #1276 DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1276)). **Attention :** `sota_vision_service.py` initialise SOTAVisionEngine à l'import ; si le poids embarqué est présent, le runtime céphalo est immédiatement disponible. Un embed sans gate de fonction médicale sûr et testé activerait une inférence anatomique non validée. **NO_INSTALLABLE_GO** ; zéro `runtime_asset.zip`, zéro installateur, aucune migration, aucune activation patient. Sigstore code re-vérification externe toujours requise avant composition.

**NEXT exact :** demander autorisation explicite du titulaire des poids pour distribution commerciale du checkpoint SHA `fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc` / ONNX SHA exact ; verrouiller le mapping clinique officiel de J1.B1 ou maintenir inference désactivée via gate certifié ; vérifier le complément `panoramic`/legacy selon fonctionnalités autorisées. Quand gates médical/juridique franchis, préparer runtime assets pour master CODE_CERTIFIED sans données patients, vérifier Sigstore, composer une `INSTALLABLE_CERTIFIED` non activée et faire rehearsal en VM jetable sous Human Gate. Sans ces preuves, rester OPEN.

---

## DIGITAL CROWN — 10/11/2026 — LOT08.2-H : SRPose38 model-weight retrieval & packaging selector FUE-0

**Décision propriétaire** : SRPose38 est conservé. Les modèles nécessaires doivent être **intégrés dans l'installable Desktop local**, et non fournis manuellement par le cabinet. Aucune autorisation de redistribution clinique/commerciale n'est présumée.

**Faits vérifiés** : CODE_CERTIFIED master exact `bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4` ([run #42897412850](https://github.com/hraaaaf/Digital_crown/actions/runs/42897412850), 6/6 SUCCESS), inchangé. Artefact SRPose38 source [run #34281082926](https://github.com/hraaaaf/Digital_crown/actions/runs/34281082926), ID #10077697721, ZIP digest `ad1caa8ee1474a1405305fc91a29eaa3c0c5b20572095faad0c2e63723284e17`, non expiré lors du contrôle. La preuve CI historique source produit un `srpose38-tta-1024.onnx`, taille `267484931` octets, SHA fichier `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`. Le ZIP comprend **7 fichiers** prouvés par le bloc complet `actions/upload-artifact@v4` du run source : ONNX, marqueur SHA, JSON et log de parité, hash checkpoint, SHA source SRPose, SHA source challenge. La première lecture limitée à quatre lignes était erronée.

**Exécution autorisée** : [PR DRAFT #1278](https://github.com/hraaaaf/Digital_crown/pull/1278), final HEAD au dernier contrôle `443602164d532eeeda383e2f3b1d6c04ddb4405f`, base master exact, diff strict de **3 fichiers** : script quality, workflow GitHub Actions, documentation. Test source négatif initial SUCCESS ; premier job de récupération réelle [#42906987734](https://github.com/hraaaaf/Digital_crown/actions/runs/42906987734) FAILED car il supposait erronément un seul fichier dans le ZIP. Échec conservé. Le log original complet a prouvé les sept fichiers ; nouveau gate attend 7 noms exacts, hash le vrai ONNX, ne copie que le poids dans un scratch puis vérifie `iter_runtime_asset_files` (sélecteur commun à DigitalCrown.spec), le registre et une inférence ORT CPU sur entrée zéro. Le test de refus de symlink a été renforcé. Aucune diffusion des octets : rapport JSON uniquement, effacement scratch. [run push #42907591802](https://github.com/hraaaaf/Digital_crown/actions/runs/42907591802) et [run PR #42907599925](https://github.com/hraaaaf/Digital_crown/actions/runs/42907599925) : tests source-only SUCCESS, extraction réelle REFUSÉE car manifeste 4 fichiers incomplet ; [run push #42908426561](https://github.com/hraaaaf/Digital_crown/actions/runs/42908426561) : erreur de syntaxe YAML (deux-points non échappés dans le nom d'étape), corrigée sans affaiblir le gate. Nouveau [run push #42908535624](https://github.com/hraaaaf/Digital_crown/actions/runs/42908535624) et [run PR #42908545331](https://github.com/hraaaaf/Digital_crown/actions/runs/42908545331) QUEUED au dernier contrôle. Aucun verdict complet revendiqué avant preuve.

**RISQUE CLINIQUE CRITIQUE découvert dans master** : `backend/services/sota_vision_service.py` construit automatiquement `sota_vision_engine = SOTAVisionEngine()` en important le module et charge le fichier ONNX compatible dès qu'il est présent ; `backend/services/vision_service.py` utilise ce moteur en premier. Donc **embarquer le modèle sans autre gate active réellement l'inférence céphalométrique automatique**, alors que la correspondance anatomique 38 canaux est en HOLD J1.B1 ([PR DRAFT #1276](https://github.com/hraaaaf/Digital_crown/pull/1276)) et que la licence commerciale des poids est NON ÉTABLIE (`WEIGHT_LICENSE_EXPLICITNESS_UNRESOLVED`). **Interdiction de composer/distribuer une release clinique avec ce modèle tant que la licence, la preuve anatomique ou un gate clinique explicitement sûr et testé ne sont pas validés.** Aucune protection ne doit être inférée du seul hash/packaging.

**NEXT exact** : terminer les vrais jobs du LOT08.2-H, fournir hash réel et preuve sélecteur, puis traiter le blocage juridique de redistribution et la barrière runtime céphalométrique explicitement fail-closed. Seule une release INSTALLABLE_CERTIFIED conforme, validée et autorisée peut ensuite embarquer/activer les modèles en pratique ; aucun merge, déploiement, patient ou installer pour l'instant. **LOT08 OPEN / NO_INSTALLABLE_GO**.

---
## DECISION CANONIQUE DE GOUVERNANCE — 2026-11-09 — FUE À LA PLACE DE REVUE INDEPENDANTE DE CODE

**Décision propriétaire 2026-11-09 — FUE remplace la revue indépendante de code comme gate standard.** La preuve requise est une FUE-0/I/G réellement exécutée, proportionnée au risque, avec scénarios négatifs/sécurité et oracles explicites, résultats inspectables, artefacts et SHA/HEAD exacts. Aucun reviewer indépendant, double review A/B, agent externe ou validation fictive n'est requis **en plus** de cette FUE pour un merge logiciel. Une FUE verte ne vaut pas automatiquement autorisation de merge, acte médical, restauration réelle, installation, validation humaine clinique/réglementaire/physique ou déploiement ; ces gates explicites restent inchangés. Les sections historiques qui imposent une revue indépendante de code sont supersédées prospectivement ; leurs constats et preuves restent archivés.

**Effet immédiat pour LOT05 / J7 et les lots V1.5 à venir :** un reviewer indépendant absent ne bloque plus une PR lorsque la FUE et les contrôles spécialisés applicables sont exécutés avec preuves exact-HEAD ; un backend CI encore en cours/rouge, une faille prouvée, ou une autorisation humaine requise continue à bloquer. Les anciennes mentions « fresh independent review », « separate reviewer », « two reviewers » ci-dessous conservent leur valeur d'historique et **ne sont plus un gate prospectif**. La roadmap/Notion et `AGENTS.md` sont autorités.

# STATE — DigitalCrown

## LOT08.2-G — 2026-11-10 — INVENTAIRE RÉEL DES ASSETS REQUIS : REGISTRE ANALYSÉ, OCTETS LOCAUX NON VÉRIFIÉS

**Source de vérité lue sur master bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4 :** backend/scientific_assets.json, blob 6ee96e9e816888349abea8384c32d01b6231d116, asset_policy external-not-versioned, **3 entrées** : (1) cephalo_sota ÉPINGLÉE, canonical_path backend/ai_models/srpose38-tta-1024.onnx, 267484931 octets, SHA256 a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb ; (2) cephalo_legacy NON ÉPINGLÉE ; (3) panoramic NON ÉPINGLÉE. Une entrée non épinglée ne constitue pas une validation scientifique, même si le futur ZIP en fige les octets.

**Code certifié existant :** run officiel #42897412850 6 SUCCESS sur SHA master exact, artifact CODE_CERTIFIED #13802971225 digest archive 4302e9d3b22cf71b40619587d597c8939dddf4199d5322714f6e3851c9f611f4, attestation GitHub #65996882 log Rekor 3793453724 ; aucune signature re-vérifiée localement à ce stade.

**Outils canoniques vérifiés :** backend/scripts/certify_runtime_assets.py prend --code-release-dir (ZIP CODE extrait), --ai-models-dir (root de fichiers scientifiques locaux), --output (runtime-assets-<SHA12>.zip). Il lit et vérifie le CODE_CERTIFIED, copie strictement la sélection runtime également retenue par DigitalCrown.spec, calcule tous les SHA256 et lie le ZIP à SHA code et digest backend/scientific_assets.json. backend/runtime_asset_certification.py vérifie manifest/certificat/fichiers, pins des assets connus et déclare les non-pinnés séparément. backend/scripts/create_release.ps1 exige ZIP CODE+runtime et gh attestation verify avec repo/workflow/ref/commit exacts avant composition ; n'active pas cabinet.

**Blocage véridique :** absence d'accès autorisé aux OCTETS des modèles locaux dans le runner GitHub et dans les connecteurs de ce lot, aucun fichier source modèle ni bundle externe effectivement récupéré ou haché. Ne pas prétendre que le modèle de 267 MB est présent sur le poste ni que les deux non épinglés sont validés. AUCUNE composition INSTALLABLE_CERTIFIED n'a été lancée.

**NEXT unique et exact :** sur l'ordinateur détenteur des assets autorisés, réaliser inventaire read-only du dossier backend/ai_models réel, vérifier présence/taille/SHA256 du srpose38-tta-1024.onnx comparés au registre, inventorier la sélection complète sans données patient ; confirmer provenance/autorisation des deux autres modèles. Extraire CODE_CERTIFIED #13802971225 dans dossier jetable, vérifier le contenu et l'attestation Sigstore, puis exécuter backend/scripts/certify_runtime_assets.py avec SHA strictement lié au CODE. Stop si absence, divergence, provenance ou autorisation insuffisante. Ne pas fusionner ni installer : NO_INSTALLABLE_GO.

## LOT08.2-G — 2026-11-10 — CODE_CERTIFIED OFFICIEL SUR MASTER : SIX JOBS SUCCESS / INSTALLABLE TOUJOURS BLOQUÉ

**Goal atteint : CODE_CERTIFIED** pour master exact **bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4**. [Workflow officiel Cabinet Certified Release #42897412850](https://github.com/hraaaaf/Digital_crown/actions/runs/42897412850), workflow_dispatch manuel du propriétaire 2026-11-10 20:39:20 UTC, tentative 1, COMPLETED/SUCCESS à 20:59:27 UTC. GitHub HEAD master inchangé.

**Six jobs terminal SUCCESS :** Exact immutable master HEAD ; Backend full certification ; Independent 14-script PostgreSQL 18 legacy-migration gate ; PostgreSQL 18 upgrade + preservation ; Frontend tests + production build ; Emit attested CODE_CERTIFIED universal artifact. Aucun job FAIL/SKIP sur ce run.

**Preuves d'artefacts :** [CODE_CERTIFIED ZIP #13802971225](https://github.com/hraaaaf/Digital_crown/actions/runs/42897412850/artifacts/13802971225), nom code-certified-dc-cabinet-bb3c92b9b8c7-run42897412850, 6372554 octets, GitHub artifact SHA256 **4302e9d3b22cf71b40619587d597c8939dddf4199d5322714f6e3851c9f611f4** ; [frontend artifact #13801886061](https://github.com/hraaaaf/Digital_crown/actions/runs/42897412850/artifacts/13801886061), SHA256 **40bac5b6a11cc1260de8eb57695b9ff87bfda9514b87570ec54e34145fbc2fa9**. Log de l'émetteur : PACKAGE_IMPORT_SMOKE=PASS ; status CERTIFIED_RELEASE_OK pour BASIC/GOLD/ELITE ; certification_level CODE_CERTIFIED, run ID et commit SHA exact.

**Signature/provenance :** action GitHub actions/attest@v4 a attesté release-content.sha256 au digest **19b27f49884d6f37e8f8dc380dbda7a7a3ed49d00e8f8c26928d2eb29e663d86** ; signature via Public Good Sigstore, log Rekor **3793453724**, [attestation GitHub #65996882](https://github.com/hraaaaf/Digital_crown/attestations/65996882). Création/signature prouvées par logs du job vert ; **vérification cryptographique hors CI par gh attestation verify non effectuée dans ce contrôle** et toujours obligatoire avant composition.

**Ce qui reste BLOQUÉ :** ZIP CODE_CERTIFIED n'est pas un INSTALLABLE_CERTIFIED, GitHub Releases [] au contrôle ; bundle d'assets runtime/modeles autorisés au même SHA absent/non vérifié ; pas de vérification des digests/registre scientifique des modèles ou des binaires locaux, ni composition/installation Windows. Ne pas utiliser d'assets non attestés, ni de données patients. Script de composition officiel backend/scripts/create_release.ps1 exige deux ZIPs, vérification Sigstore par GitHub CLI ou trust root et contrôle strict des contenus avant tout stage.

**NEXT exact :** inventorier sur la machine propriétaire les assets runtime autorisés sans donnée patient, créer/certifier un runtime-assets bundle lié exactement à ce SHA, télécharger CODE_CERTIFIED #13802971225 et valider attestation Sigstore avec gh attestations ; puis seulement décider une composition INSTALLABLE_CERTIFIED en préproduction isolée, sous gate humain si nécessaire. Aucun merge de PR #1266/#1273/#1274/#1275, aucun déploiement, activation clinique, migration ou installation. LOT08 OPEN / NO_INSTALLABLE_GO.

## LOT08.2-G — 2026-11-10 20:40 UTC — CABINET CERTIFIED RELEASE OFFICIEL DÉCLENCHÉ, EN COURS

**Résultat vérifié** : après action manuelle du propriétaire, [workflow_dispatch #42897412850](https://github.com/hraaaaf/Digital_crown/actions/runs/42897412850) créé le 10 novembre 2026 à 20:39:20 UTC sur **master exact bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4**, attempt 1, status in_progress. Branche master inchangée.

**Premiers jobs :** Exact immutable master HEAD SUCCESS ; Independent 14-script PostgreSQL 18 legacy-migration gate SUCCESS ; Backend full certification, PostgreSQL 18 upgrade + preservation et Frontend tests + production build encore en cours. Zéro artefact listé lors du contrôle initial. Cela ne prouve **pas** encore CODE_CERTIFIED ; attendre succès global terminal et attestation/archive sur SHA exact.

**Notion :** page LOT08 et roadmap parent actualisées suite à la vérification.

**NEXT exact :** inspecter le verdict complet, jobs et logs ; si SUCCESS, attestations GitHub/Sigstore et archive CODE_CERTIFIED + digest ; si FAILURE analyser et corriger avant tout nouveau run. Ensuite seulement valider les assets externes runtime même SHA en vue INSTALLABLE_CERTIFIED, après gates. Aucun merge, déploiement ou installable autorisé. LOT08 OPEN / NO_INSTALLABLE_GO.

## LOT08 — 2026-11-10 — LOT08.2-G CODE_CERTIFIED : TENTATIVE DE DÉCLENCHEMENT BLOQUÉE (ACTION HUMAINE PRÉCISE)

**Dernier GO du propriétaire :** autorise à déclencher la certification CODE officielle sur `master` exact, puis à inventorier les assets certifiés correspondants. **Ne couvre pas** merge #1273/#1274/#1275, installation Windows réelle, migration clinique, restauration de données réelles ou activation du cabinet.

**Avant action, constat source vérifié :** `master@bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4` inchangé ; [workflow Cabinet Certified Release](https://github.com/hraaaaf/Digital_crown/actions/workflows/cabinet-release-certification.yml) exige `workflow_dispatch` depuis `refs/heads/master` et input `commit_sha` de 40 caractères **identique au HEAD courant**. Historique des runs `workflow_dispatch` : aucun nouveau CODE certifié sur ce SHA. Les succès PostgreSQL/PR et l'ancien CODE #40598411922 sur `98f0199dde54123d1caf3b41443c47a000c3b39f` ne constituent pas cette certification.

**Tentative d'exécution réellement faite / blocage non contourné :** le connecteur GitHub expose les runs/artifacts en lecture et les changements repository/PR mais **aucun déclenchement de workflow**. Le Browser Chat connecté ne permet pas de piloter un navigateur (extension originaire absente) ; le connecteur Opera liste seulement un onglet page d'accueil et n'expose pas d'action click/form. Tentative d'ouvrir la page Actions via TinyFish sur profil utilisateur connecté, avec instruction stricte **workflow officiel, branche master, SHA ci-dessus, une seule soumission et aucun autre changement**, **REFUSÉE AVANT LE DÉMARRAGE** : porte-monnaie TinyFish insuffisant (-0,04 USD). Ce n'est PAS un GitHub run démarré. Aucun frais, aucun paiement/auto-reload lancé, aucune autre action GitHub, aucune release ni installation.

**NEXT exact et solution gratuite préférée :** le propriétaire authentifié ouvre [Cabinet Certified Release](https://github.com/hraaaaf/Digital_crown/actions/workflows/cabinet-release-certification.yml), clique **Run workflow**, choisit **master**, saisit **`bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4`** dans `commit_sha`, valide une seule fois. Ensuite contrôler **run ID, HEAD, cinq gates, attestation Sigstore et artefact CODE_CERTIFIED** ; seulement après preuve, inventorier les modèles/assets runtime externes, certifier leur provenance/digest même SHA et composer un `INSTALLABLE_CERTIFIED` via la procédure officielle, sous human gates applicables. Ne jamais substituer le vieil artefact, un certificat fabriqué ou une CI PR verte. **LOT08 OPEN / NO_INSTALLABLE_GO / master inchangé**.

## LOT08 — 2026-11-10 — LOT08.2-G — GATE INSTALLABLE ET VRAI SQLCIPHER : FUE-LAB VALIDÉ, VM INSTALLATION BLOQUÉE

**GO utilisateur** : autorisation de **préparer** une recette d'un vrai `INSTALLABLE_CERTIFIED` avec SQLCipher et rollback sur VM entièrement isolée, sans merge, installation d'artefact non certifié, données patients ni activation cabinet. La décision unique 08.2-G porte sur un gate **fail-closed de provenance exacte** et l'essai de primitives SQLCipher en CI jetable, pas sur une certification produit.

**Master/certification réellement inventoriés** : `master@bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4` confirmé inchangé. Résultat API GitHub Releases = **[]**. Inventaire des workflow_dispatch GitHub : **aucun `Cabinet Certified Release` réussi sur ce SHA master** ; dernière certification CODE trouvée [run #40598411922](https://github.com/hraaaaf/Digital_crown/actions/runs/40598411922) (2026-10-27) au **SHA historique `98f0199dde54123d1caf3b41443c47a000c3b39f`** ; artefact ancien `code-certified-dc-cabinet-98f0199dde54-run40598411922` (#12778323883) SHA256 `72bfc5fd9aa4505ceb5d02d8e31058784723481ec487e6c4b00bd1b2298706f1`. **CODE_CERTIFIED d'un ancien SHA ≠ master actuel et ≠ INSTALLABLE_CERTIFIED**. Le run [Cabinet Upgrade PG #42851885842](https://github.com/hraaaaf/Digital_crown/actions/runs/42851885842) SUCCESS au master ne déclenche pas la certification CODE officielle. Aucune composition/assets runtime certifiés exact SHA présentés. Il est donc **interdit d'exécuter le vrai installateur**, même sur VM, tant que la chaîne exacte n'existe pas.

**PR et périmètre** : [PR #1275 DRAFT / NO MERGE](https://github.com/hraaaaf/Digital_crown/pull/1275), HEAD exact `0073694c2c1bc07cc022c5c7acd267b51b2aec45`, base master SHA ci-dessus. Diff GitHub borné **5 nouveaux fichiers uniquement** : `scripts/quality/lot08_2_g_installable_gate.py` (CLI read-only qui refuse sans artefact et importe uniquement pour une release complète le véritable `backend.release_certification.verify_installable_release_directory`), `queue_core/tests/test_installable_gate_08_2_g.py` (artefacts forgés, manquants, historiques, SHA incorrect, refus), `scripts/quality/lot08_2_g_sqlcipher_lab.py` (trois bases SQLCipher synthétiques chiffrées, cold clone et erreurs négatives), `.github/workflows/v15-08-2-g-installable-vm-readiness-fue.yml` (Linux/Windows), `docs/quality/V15_08_2_G_INSTALLABLE_VM_REHEARSAL_GATE.md` (contrat de preuve et NEXT). Aucun runtime, installateur, script d'activation, données ou modèle réel modifié.

**SUCCESS / PROOF CI exact-HEAD** : [Actions run #42874447553](https://github.com/hraaaaf/Digital_crown/actions/runs/42874447553) COMPLETED/SUCCESS, **3 jobs** Linux Queue/gate, Windows fail-closed et Linux vrai SQLCipher **SUCCESS**. Linux **198 passed, 3 skipped, 4 subtests passed**, préflight diff strict 5 paths, `LOT08G_EXACT_HEAD_FIVE_FILE_SOURCE_ONLY_PASS` ; ausencia d'artefact `BLOCKED_NO_INSTALLABLE_GO` testée en code sortie **3** et résultat `LOT08G_NO_REAL_INSTALLABLE_FAIL_CLOSED=PASS`. Artifact JUnit/gate #13792015064 digest SHA256 `1515f884fc5fdc2f76989b2f95de703e83d332a2c8ec439a045d2f45ad405c6a`.
- **Windows 2022** : **18 tests négatifs PASS** ; refuse un artefact absent/incomplet/forgé/historique ; aucun exécutable installé/lancé ; `LOT08G_WINDOWS_NO_INSTALLABLE_FAIL_CLOSED_PASS`, artifact #13790976592 SHA256 `24e37f9abc7896a67a24721d01c5e0ed8bc2cb987fae1912ecd5d3dfab446d39`.
- **Linux vrai SQLCipher natif** : `PRAGMA cipher_version` vérifié, trois fichiers indépendants **réellement chiffrés** et nouveaux, lecture standard SQLite et mauvaise clé refusées, copie à froid vers dossier nouveau, intégrité/fichier tamper/divergence epochs/écrasement refusés, `LOT08G_REAL_SQLCIPHER_THREE_DB_COLD_RESTORE_LAB_PASS`. Oracle SIGKILL existant `scripts/ci/cb03_g7_real_sqlcipher_sigkill.py` **réel** pre-commit rollback et post-commit durabilité vérifié sur **UNE base** SQLCipher : `CB03_G7_REAL_SQLCIPHER_SIGKILL_PASS`. Artifact métadonnées seulement #13790388987 SHA256 `7a535bf0cf89443c259ca1f24b92fff302f7e1a0cdc8dc79170c4e3f88264675`. [PR #1275 commentaire de closeout](https://github.com/hraaaaf/Digital_crown/pull/1275#issuecomment-6775653938).

**Corrections et historique non maquillé** : première [#42873614371](https://github.com/hraaaaf/Digital_crown/actions/runs/42873614371) Linux/Windows negatives FAIL en import du runtime clinique (environnement CI minimal dépourvu d'`email-validator` et `sqlalchemy`) alors que SQLCipher passait. Correction : pré-vérifier les 7 fichiers obligatoires avant import du vérificateur clinique et **NE PAS accepter un artefact réel via un mock** (mocks confinés aux tests) ; appel canonique complet pour vraie candidate. Deuxième [#42874133352](https://github.com/hraaaaf/Digital_crown/actions/runs/42874133352) Windows du gate retour 3 correct mais shell GitHub PWSh propageait 3 comme échec final ; après assertion de l'exit 3, normalisation `$global:LASTEXITCODE=0` du runner uniquement, sans changer la décision. Final FUE SUCCESS au SHA `007369...`. Ces runs rouges restent historiques, pas requalifiés.

**Frontières NON acquises** : tests portent sur primitives SQLCipher Linux en sandbox synthétique, NON sur SQLCipher installé Windows, EXE `DigitalCrown.exe` installé, installateur Inno Setup certifié, application clinique migrée, fichiers patients, vrai schéma, DB+WAL+médias avec rollback global, RPO/RTO et reprise d'une panne réelle. Le SIGKILL validé est **une transaction d'une DB**, ne garantit **aucune atomicité multi-DB**. Gate read-only ne certifie/promeut/active rien. **`LOT08 OPEN / NO_INSTALLABLE_GO / CODE_CERTIFIED non attribué à master`.**

**NEXT EXACT / blocage à lever** : déclencher le workflow officiel [Cabinet Certified Release](https://github.com/hraaaaf/Digital_crown/actions/workflows/cabinet-release-certification.yml) en `workflow_dispatch` sur **master@bb3c92b9...` avec input `commit_sha` exact 40 caractères ; le connecteur GitHub courant est READ-ONLY pour workflows (pas de dispatch disponible). Après succès, certifier les modèles/assets externes sur le même SHA et composer/attester le vrai `INSTALLABLE_CERTIFIED` via procédure officielle ; soumettre un **GO humain de recette d'installation Windows sur VM jetable** après vérifications de provenance et restore sans patient. Sinon BLOQUÉ. Ne pas déployer Vercel/Cloudflare, ne pas merger #1275 ni #1266 sur master sans autorisation séparée.

## LOT08 — 2026-11-10 — LOT08.2-F : ACTIVATION WINDOWS PER-USER ET RESTORE À FROID (FUE-I LAB SUCCÈS, NO MERGE)

**Décision/Goal :** vérifier le mécanisme actuellement codé dans `installer/DigitalCrown.iss` et `run.py` : l'installateur exige `INSTALLABLE_CERTIFIED`, s'installe dans `{localappdata}` avec `PrivilegesRequired=lowest`, sans `[Run]`/tâche/service/raccourci auto, l'identité de release étant vérifiée avant choix du profil absolu et premier boot. Le laboratoire démontre en outre un **vrai processus Windows standard non administrateur** avec SQLite, puis refuse toute restauration sur processus actif et clone des trois SQLite synthétiques **seulement après arrêt**. *Aucun installable/product run, aucun vrai cabinet*.

**Source et autorisation :** GO propriétaire « Go » pour avancer l'essai de sécurité Desktop, sans autorisation de merge, production, installation, migration patient ou QR clinique. `master` confirmé inchangé à `bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4`. [PR #1274 DRAFT/NO MERGE](https://github.com/hraaaaf/Digital_crown/pull/1274) HEAD exact `40237d063b3950222adb0a041537de05268372a8`, diff = **5 fichiers nouveaux LAB seulement** : `.github/workflows/v15-08-2-f-user-profile-cold-restore.yml`, `queue_core/tests/test_activation_source_08_2_f.py`, `scripts/quality/lot08_2_f_activation_source_lab.py`, `scripts/quality/lot08_2_f_user_process_probe.py`, `scripts/quality/lot08_2_f_windows_user_profile_lab.ps1`.

**SUCCESS/PROOF exact SHA** : [GitHub FUE run #42868750131](https://github.com/hraaaaf/Digital_crown/actions/runs/42868750131) COMPLETED/SUCCESS, Linux et Windows deux jobs SUCCESS. Linux `LOT08F_FIVE_FILE_EXACT_HEAD_SOURCE_ONLY_PASS=40237d...`, régression Queue Core complète **189 PASS / 3 SKIP / 4 sous-tests PASS** ; artifact JUnit Linux #13789290525 SHA256 `1c2590d45c71137f06fbcc592be3f2648cacef10521046ab865bdef2590c7722`. Windows Server 2022, tests source `9 PASS`, véritable lancement `Start-Process -Credential -LoadUserProfile` du script LAB sous **user local standard**, vérification dans le processus de son SID via `whoami /user`, création des trois SQLite par ce user. Parent observe véritable verrou SQLite `BEGIN IMMEDIATE` et refus `COLD_SNAPSHOT_REQUIRES_STOPPED_OWNER`, `CreateFileW` depuis guest local refuse lecture et écriture ; arrêt contrôlé puis 3 backups SQLite à froid en nouveau répertoire, PRAGMAs intégrité et epochs identiques, refus `RESTORE_NEVER_OVERWRITE` et `CROSS_STORE_EPOCH_MISMATCH`. Logs `REAL_ACTIVE_USER_SQLITE_WRITER_LOCK=PASS`, `WINDOWS_DIFFERENT_STANDARD_USER_READ_WRITE_DENIED_PASS`, `LOT08F_OFFLINE_COLD_CLONE_EPOCH=0`, `LOT08F_REAL_STANDARD_USER_TOKEN_AND_COLD_RESTORE_LAB_PASS`. Artifact Windows #13788481795 SHA256 `0a15e493ab68a8fd32a52b424cf7c674ea0cb1452dfde46a23a15cb3c2ae4fa5`. [PR scope #42868758017](https://github.com/hraaaaf/Digital_crown/actions/runs/42868758017) SUCCESS. [PR preuve détaillée](https://github.com/hraaaaf/Digital_crown/pull/1274#issuecomment-6774864483).

**Échecs historiques / correction** : [#42867971394](https://github.com/hraaaaf/Digital_crown/actions/runs/42867971394) FAILED car la fixture tentait une modification NTFS sur SQLite encore ouvert, puis le cleanup masquait l'erreur originale ; [#42868473483](https://github.com/hraaaaf/Digital_crown/actions/runs/42868473483) FAILED lors du renommage Windows des SQLite du stage, à cause de connexions non fermées : `sqlite3.connect` utilisé comme gestionnaire de contexte transactionnel ne ferme PAS le handle. Après diagnostic, retrait de la modification ACL sur fichier actif, contrôle d'accès OS réel, `contextlib.closing` partout sur les connexions de snapshot et nettoyage renforcé, preuve FINAL vert à SHA `40237d...`. Jamais compter les deux runs rouges comme succès.

**Frontières/NO GO** : pas de `DigitalCrown.exe` installé, pas d'Inno Setup réel, aucune release `INSTALLABLE_CERTIFIED`, pas de SQLCipher/clé patient, ni Windows profil réel cabinet, réseau/Kiosk/physique ; les trois SQLite sont des fixtures sans secrets. Un clonage à froid n'est **pas** la preuve d'atomicité 3-DB en cas de crash ou d'arrêt de writers inconnus, ni une sauvegarde chiffrée/signée, ni un RPO/RTO mesuré. `LOT08 OPEN / NO_INSTALLABLE_GO / CODE_CERTIFIED NON ACQUIS`. PR #1274 reste DRAFT, aucune fusion sur master.

**NEXT EXACT :** décider/protéger le profil d'activation explicitement approuvé par utilisateur ; seulement avec certificats et GO séparés, tester l'installable certifié sur VM isolée en vérifiant le binaire réel + fichiers SQLCipher + conservation/rollback ; poursuivre par LOT08.4 API et LOT08.5/08.6 UI sur contrat clinique validé, sans activation QR autonome.

## LOT08.2-E — 2026-11-10 — ARCHITECTURE ACTUELLE RECONCILIÉE / SCM LAB ≠ INSTALLATEUR PRODUIT

**Fait vérifié dans master `bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4` après les FUE #1273 :** [`installer/DigitalCrown.iss`](https://github.com/hraaaaf/Digital_crown/blob/bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4/installer/DigitalCrown.iss) impose sept attestations `INSTALLABLE_CERTIFIED`, `PrivilegesRequired=lowest`, et sections `[Run]` et `[UninstallRun]` **sans démarrage automatique ni création de tâche/service** ; les commentaires du script l'interdisent explicitement avant le parcours d'activation contrôlé. [`run.py`](https://github.com/hraaaaf/Digital_crown/blob/bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4/run.py) exige un profil d'environnement absolu explicite, des dossiers isolés et `--initialize-new-cabinet` pour le premier boot. Les anciennes indications du guide on-premise sur tâche planifiée à l'installation ne décrivent **pas** le code actuel de l'installeur et ne doivent pas être suivies.

**Impact sur résultat 08.2-E :** le vrai service SCM éphémère LocalService testé en Windows GitHub est une **preuve de capacité NTFS/Windows**, pas l'identité d'un service créé par l'installateur produit (aucun service n'est créé automatiquement). Ne pas changer l'installateur pour correspondre à l'expérience ; garder PR #1273 DRAFT/NO MERGE. Ce constat est aussi commenté sur [PR #1273](https://github.com/hraaaaf/Digital_crown/pull/1273#issuecomment-6773290990).

**Next exact corrigé :** identifier/valider le **profil d'activation réel choisi** (processus explicite par utilisateur ou service/tâche séparément autorisé), puis tester principal Windows effectif et ACL/SQLCipher des dossiers de ce profil sur VM jetable certifiable. En parallèle, formaliser la quiescence de tous writers inter-DB avant sauvegarde/restauration, avec refus des états partiels ; ne pas inférer atomicité multi-fichiers ni readiness clinique de la FUE LAB.

## LOT08 — 2026-11-10 — LOT08.2-E — SERVICE WINDOWS RÉEL EN VM + SNAPSHOT SYNTHÉTIQUE FUE VERT / DRAFT

- **GO utilisateur :** « Go » après closeout source master LOT08.2-D, autorisation d'avancer au **LOT08.2-E** sur risques Windows réel/service et restauration synthétique. **Aucune autorisation de merge, migration patient, installateur, déploiement ni QR clinique.**
- **Master vérifié inchangé** : `bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4`. Nouvelle [PR #1273 DRAFT / NO MERGE](https://github.com/hraaaaf/Digital_crown/pull/1273), branche `feat/v15-08-2-e-windows-service-snapshot-fue0-20261110`, exact HEAD `131e1746f8d0abe8f1a15d1788ad88a42f5a31af`. Diff GitHub depuis master : **5 fichiers neufs uniquement** : `scripts/quality/lot08_2_e_snapshot_lab.py`, `scripts/quality/lot08_2_e_service_probe.py`, `scripts/quality/lot08_2_e_windows_service_lab.ps1`, `queue_core/tests/test_snapshot_08_2_e.py` et `.github/workflows/v15-08-2-e-windows-service-snapshot-lab.yml`. Aucune source clinique/runtime, configuration patient, SQL migration, ni paquet changé.
- **SUCCÈS OBSERVABLE / PROOF** : [GitHub run #42856459283](https://github.com/hraaaaf/Digital_crown/actions/runs/42856459283) COMPLETED/SUCCESS sur le SHA ci-dessus, **deux jobs Linux/Windows SUCCESS**. Préflight Linux `LOT08_2_E_BOUNDED_FIVE_FILE_EXACT_HEAD_PASS=131e1746...`; Queue Core complet **187 pass, 3 skipped, 4 subtests pass**. JUnit Linux artifact #13784100169, SHA256 `335be88c73a4fe3d3373b57f4d08536488ede47e59ef4673b4e041500640b0ff`.
- **Windows vrai SCM temporaire** : GitHub-hosted Windows Server 2022 (et NON poste cabinet), création / lancement d'un vrai service éphémère via Windows SCM sous `NT AUTHORITY\\LocalService`, `sc sidtype unrestricted`; le process du service vérifie lui-même son SID LocalService `S-1-5-19`, son propre SID `NT SERVICE\\<name>` et ouvre/écrit **trois SQLite synthétiques sous ce token effectif**. `CreateFileW` sous un utilisateur local non approuvé renvoie ACCESS_DENIED en lecture ET écriture. Log `REAL_SCM_SERVICE_PER_SID_WRITE_AND_GUEST_DENY=PASS` puis `WINDOWS_REAL_SERVICE_IDENTITY_LAB_PASS`. Le script supprime service, utilisateur jetable et fichiers temporaires dans `finally`; artefact ne contient aucun credential/SID/path nominatif.
- **SQLite cohérence inter-processus coopérative** : Linux et Windows lancent un **deuxième processus writer actif** avec verrou OS fichier `msvcrt.locking`/ `fcntl.flock`, quiescence coopérative pendant trois appels `sqlite3.backup`, epoch commune par DB dans manifeste + hash SHA256, stage puis renommage dossier, restauration en **nouveau dossier seulement**, contrôle `integrity_check`. Négatifs : commit interrompu entre DBs → epochs divergents et backup refusée ; backup interrompue → staging supprimé ; fichier tamper/missing → restore refusée ; manifest epoch falsifié/extraneous file → refus ; restore vers répertoire existant → refus sans modification. Sur Windows **7 tests pass en 12.11s**, preuve JSON+JUnit artifact #13783880420, SHA256 `8ce46c2124bf373f9034606f412d2d93009376d590e50f5f32f06b9425ef9724`.
- **Restriction IMPÉRATIVE** : vraie identité de service **sur VM runner uniquement**, pas le service Desktop réellement installé. Seuls writers **coopérants** protégés ; transactions sur 3 SQLite restent **non atomiques après crash entre commits** ; test ne prouve pas power-loss, anti-tamper de manifeste (SHA non authentifié), snapshot cohérent avec writer non coopérant, récupération des données de cabinet, RPO/RTO mesuré, protection du secret clé, installation ni hardware. `LOT08 OPEN / NO_INSTALLABLE_GO / CODE_CERTIFIED NON ATTRIBUÉ`. PR #1273 reste **DRAFT** jusqu'à GO de merge distinct.
- **NEXT EXACT** : recette en VM Windows isolée de l'identité du service réellement installable, contrôle ACL après start/stop/reboot et stratégie de gel de writers non coopérants ; scénario restauration multiprocess/échec power interruption avec rollback cohérent et RPO/RTO. Ensuite API 08.4, UI 08.5/08.6, LOT09/10. Aucune promotion clinique sans human gate explicite.

## LOT08 — 2026-11-10 — HUMAN GO / GITHUB MERGES VERIFIED / NO CLINICAL RELEASE

- **GO explicite propriétaire** : « Go » en réponse à la décision unique d'intégration contrôlée des PR #1264 puis #1271 vers `master`. Autorisation de merge logiciel source/LAB uniquement : aucune installation, activation QR clinique, migration patient, déploiement Vercel, production, packaging ou promotion CODE_CERTIFIED.
- **Avant fusion** : `master@027a82aca4cc37308f6323e759283c4ca0e45fad`. PR #1264 HEAD `88ebec4244519182ee6445056ba47702f305bd14`, cinq fichiers LAB, 9 CI SUCCESS + 1 SKIPPED, FUE-0 exact SHA SUCCESS. Marquée ready après GO, merge commit GitHub **`e74eb2bc68eb25e77bd5f7fb50b27b96e2c4bd96`** ; master vérifié à ce SHA ; comparaison #1264 HEAD contre nouveau master = **0 fichier différent**. [PR #1264 MERGED](https://github.com/hraaaaf/Digital_crown/pull/1264).
- **Réconciliation post-#1264** : PR #1271 automatiquement rebasée en cible `master` (sans changer la source). Un seul fichier workflow est ensuite renforcé pour vérifier les QUATRE SHA Git des sources et tests d'appareils hérités de #1264, en plus des huit SHA sources Queue/QR/Windows. Nouveau HEAD **`252e9251d9faecc53dd86eaaa7d978c670556769`** ; le diff PR contre nouveau master demeure exactement **9 fichiers additionnels**, aucun fichier device dupliqué.
- **Preuves FUE au HEAD de #1271 final** : [run #42851374489](https://github.com/hraaaaf/Digital_crown/actions/runs/42851374489) COMPLETED/SUCCESS ; Linux Ubuntu `180 passed / 3 skipped / 4 subtests passed`, préflight diff 9 fichiers + 12 Git blobs PASS ; Windows Server 2022 véritable ACL NTFS avec deux identités locales temporaires + Win32 `NTFS_3_FILES_ADMIN_AND_SERVICE_RW_GUEST_DENIED=PASS`, `2 passed` backup/restore + `33 passed, 4 subtests passed` QR/device, toutes bases synthétiques ; artifacts Linux JUnit [#13780168502](https://github.com/hraaaaf/Digital_crown/actions/runs/42851374489/artifacts/13780168502) `sha256:880cd4de35aaf36e4492c9a524508bf2894e780a62399cc162fabc0004b6f72d` et Windows JUnit/JSON [#13779394729](https://github.com/hraaaaf/Digital_crown/actions/runs/42851374489/artifacts/13779394729) `sha256:1618aebb06cf00ba474cbb8a0c1cbaed5e9d5f28f1e87c46a61b900f6aadccf4`. Scope Gate #42851757706 COMPLETED/SUCCESS, PR `mergeable_state=clean`, aucune faille constatée dans ce périmètre ; M6-I antérieure SKIPPED non comptée.
- **Deuxième fusion réalisée** : #1271 marquée ready, méthode `merge`, expected SHA figé. [PR #1271 MERGED](https://github.com/hraaaaf/Digital_crown/pull/1271) au SHA de merge **`bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4`**. GitHub master relu à ce SHA. Comparaison `252e9251...` → master : +2 commits d'historique/merge, **ZÉRO différence de fichiers**. Comparaison base initiale `027a82ac...` → master final : **14 fichiers uniques** (5 de #1264 + 9 de #1271), aucun duplicate de sources device.
- **Anciennes PR nettoyées** : #1265, #1267 et #1270 chacune fermées CLOSED / NOT MERGED, commentaire d'archivage/provenance explicite. Pas de suppression des preuves/branches ni merge de leurs copies. [PR #1266 documentaire](https://github.com/hraaaaf/Digital_crown/pull/1266) reste DRAFT/NON MERGED ; ce STATE est sa documentation candidate, pas une modification de master.
- **CI post-merge distincte** : le push master de #1264 a lancé Cabinet Upgrade PostgreSQL Certification #42851045154 (COMPLETED/SUCCESS au dernier contrôle). Celui du nouveau master a lancé [#42851885842](https://github.com/hraaaaf/Digital_crown/actions/runs/42851885842), désormais **COMPLETED/SUCCESS** après lecture GitHub des deux jobs. Job PostgreSQL 18 + gardes de release **SUCCESS**, 25 tests ciblés PASS ; job Windows PowerShell 5.1 **SUCCESS**. Les journaux PostgreSQL contiennent des erreurs SQL `column ... already exists` observées au cours des essais de migration et la commande de tests a néanmoins terminé exit 0 ; il ne faut pas les interpréter comme migration clinique autorisée. Ces contrôles ne constituent ni installation, ni sauvegarde physique, ni CODE_CERTIFIED.
- **Frontières critiques** : l'ACL testée est celle de comptes éphémères dans un runner, pas celle du vrai service Windows Desktop ; trois `sqlite3.backup` au repos ne prouvent pas un snapshot cohérent inter-fichiers avec écriture simultanée, coupure électrique ou RPO/RTO. Aucun QR clinique, patient, Agenda LOT09, appareil physique LOT10, HTTP production, gestion réelle des clés, migration clinique ni installateur certifié. LOT08 **OPEN**, `NO_INSTALLABLE_GO`, `CODE_CERTIFIED` final non attribué.
- **NEXT exact** : vérifier post-merge master CI #42851885842, puis avancer la recette sécurité Windows du vrai service + récupération SQLite sous conditions réelles, 08.2-E, API 08.4, UI 08.5/08.6, LOT09/10 et preuve installable sous gates humains séparés. Aucun nouveau merge documentaire ni déploiement implicite.

## LOT08 — 10/11/2026 — RECONCILIATION SINGLE-SOURCE / WINDOWS LAB — DRAFT GREEN, NO MERGE

- **Décision unique / GO limité** : reprendre LOT08.2-D et réconcilier les PR sans duplication. Aucun merge master, activation QR clinique, migration, installation, Vercel ou test patient réel autorisé. Priorités : sécurité des accès locaux, intégrité Queue et réversibilité.
- **Provenance GIT vérifiée** : master `027a82aca4cc37308f6323e759283c4ca0e45fad` identique à la base. PR #1264 OPEN/DRAFT SHA `88ebec4244519182ee6445056ba47702f305bd14` ; #1265 OPEN/DRAFT SHA `f6e4df6553826aca06d2f01fc83674baf5018634` ; #1267 OPEN/DRAFT SHA `aca36e8a483ff5f8e8f92d68a5d3ffb7996b4e92`. Quatre fichiers device de #1264 copiés dans #1267 identiques octet pour octet et en SHA blob. #1267 descend du commit #1265 mais ne doit pas être mergée telle quelle.
- **Preuve Windows synthétique** : [PR #1270 DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1270) HEAD `ca5c094c0e26604dc9429169e6b0e3eafed1f9b0` ; [run Windows #42836466725](https://github.com/hraaaaf/Digital_crown/actions/runs/42836466725) COMPLETED/SUCCESS, vrais contrôles NTFS CreateFileW sous impersonation, service local RW / autre compte non privilégié DENIED sur trois SQLite synthétiques ; tests de restauration SQLite quiescée **2 PASS**, QR/device **33 PASS + 4 sous-tests**, manifestes [#13774012052](https://github.com/hraaaaf/Digital_crown/actions/runs/42836466725/artifacts/13774012052).
- **Réconciliation source unique réellement préparée** : [PR #1271 DRAFT empilée sur #1264](https://github.com/hraaaaf/Digital_crown/pull/1271), HEAD `5e587c788aba9ac779e2c0df43cb42413fd1d5e9`, diff GitHub **ahead 9/behind 0, exactement neuf fichiers** par rapport à #1264. Les quatre sources device de #1264 restent héritées une seule fois. Provenance contrôlée des huit autres fichiers via SHA Git : 4 Queue #1265, 2 QR #1267 et 2 FUE Windows #1270 ; neuvième fichier = workflow de vérification.
- **CI réconciliée exactement sur HEAD** : [GitHub run #42837343615](https://github.com/hraaaaf/Digital_crown/actions/runs/42837343615) **COMPLETED/SUCCESS**, deux jobs Linux+Windows. Linux : **180 PASS / 3 SKIPPED / 4 sous-tests**, preflight neuf chemins + huit hashes Git PASS. Windows : NTFS Win32 réel LAB PASS ; backup/restauration **2 PASS** ; QR/device **33 PASS + 4 sous-tests**. Artifacts Linux JUnit **#13773563335** digest SHA-256 `9de9a19dcc79b98eeda37392160e3a77542116739f41cec74b4f8cec63267628` et Windows JUnit/JSON **#13774732135** digest `70e2e67844724db5d8aa3062bcd8cf298c55a302475ca9e1181a1b59eac0bbf4`.
- **Limites :** ce succès est uniquement un FUE-I LAB synthétique. Les ACL sont testées pour des utilisateurs Windows jetables, pas pour l'identité du vrai service Desktop ni l'installateur. La sauvegarde `sqlite3.backup` de trois fichiers au repos ne certifie PAS un snapshot distribué lorsque plusieurs bases reçoivent des écritures, ni RPO/RTO/coupure électrique. QR clinique/caméra physique, gestion des secrets Windows, parcours Agenda LOT09, hardware LOT10 et certification finale sont NON TESTÉS/NON AUTORISÉS. Toutes les PR restent DRAFT, `NO_INSTALLABLE_GO`, LOT08 OPEN.
- **NEXT exact (HUMAN GATE)** : valider l'ordre de fusion distinct #1264 d'abord, puis rebaser/re-cibler #1271 sur master et recontrôler CI exact SHA ; ne JAMAIS fusionner #1265/#1267/#1270 en plus (historique redondant). Avant tout installable : ACL identité effective Windows, stockage de secrets, restauration cohérente sous contraintes réalistes, FUE interfaces 08.2-E / 08.4–08.6, LOT09/10, `CODE_CERTIFIED` complet et GO clinique/production distinct.

## LOT08.2-D — QR JOIN FUE-I SUCCESS — 2026-11-10

- **GO propriétaire** : « Okay go » pour jonction LAB auth→device→Queue et preuve de consommation QR atomique/anti-rejeu/révocation concurrente. **NO_MERGE, NO_INSTALLABLE_GO, aucune donnée patient réelle, aucune migration/déploiement/activation clinique**.
- **BASE et provenance** : master préflight `027a82aca4cc37308f6323e759283c4ca0e45fad`, branch proof `feat/v15-08-2-d-qr-atomic-lab-20261110` créée à partir du HEAD exact PR #1265 `f6e4df6553826aca06d2f01fc83674baf5018634`; 2 fichiers source appareil et 2 fichiers de test copiés exactement depuis HEAD PR #1264 `88ebec4244519182ee6445056ba47702f305bd14`. Pas de merge entre PR. [PR d'intégration #1267 DRAFT, NE PAS MERGER telle quelle](https://github.com/hraaaaf/Digital_crown/pull/1267), HEAD `aca36e8a483ff5f8e8f92d68a5d3ffb7996b4e92`.
- **Code LAB uniquement** : `queue_core/service/kiosk_qr_lab.py`, trois fichiers `*-synthetic.sqlite` imposés et distincts (auth / appareils / Queue), initialisation EXPLICITE du store QR Queue sur fichier synthétique sous garde console locale, pas d'endpoint HTTP. Émission QR par Reception autorisée et visite APPOINTMENT existante : token opaque non tracé, empreinte SHA-256 seule persistée, TTL 5–30 min et rotation. Consommation par Kiosk appairé : locks `auth BEGIN IMMEDIATE` → `devices BEGIN IMMEDIATE` → `queue BEGIN IMMEDIATE`, sans réentrée ; acteur `DEVICE`, méthode `KIOSK_QR`, `check_in` domaine, `validate_atomic_transition`, CAS Queue. En **une seule transaction Queue**, code QR consommé et reçu idempotent + visite versionnée + événements ARRIVED et WAITING_ENTERED. Replays avec autre clé refusés, retries même device/clé dans fenêtre 7 jours sans deuxième arrivée. Aucun commit atomique distribué entre DB revendiqué.
- **Genuine GitHub FUE-I** : [run #42822206750](https://github.com/hraaaaf/Digital_crown/actions/runs/42822206750) **COMPLETED/SUCCESS** au HEAD exact `aca36e8a483ff5f8e8f92d68a5d3ffb7996b4e92`: **10 tests FUE ciblés PASS ; 178 tests Queue Core PASS, 3 SKIPPED et 4 subtests PASS**. JUnit [#13767118085](https://github.com/hraaaaf/Digital_crown/actions/runs/42822206750/artifacts/13767118085), archive SHA-256 `d6c52d5f39eebad24630ac5613209a50d849870c12cdf796151d1bb67344f1f6`. Le code du test relance un processus Python séparé : SIGKILL après SQL de consommation QR, avant COMMIT, relecture SQLite PLANNED/version 0/0 events/QR non consommé puis check-in de reprise SUCCESS. FUE concurrence : un seul gagnant sur scans différents ; révocation Kiosk bloquée jusqu'à commit ; Wall/tenant/expire/roles/replay refusés.
- **Limites impératives** : prototype indépendant et non intégrable en clinique sans changements de contrats et gates propres : `initialize_lab()` n'est pas une migration autorisée, suffixe de fichier synthétique ne remplace pas ACL OS, vrai appareil/QR caméra, sécurité transport, preuve de sauvegarde/restauration, coupure électrique, inter-processus Kiosk/moteur sous conditions adversariales, mapping avec Agenda LOT09, installation matérielle LOT10. **PR #1267 est une juxtaposition DRAFT des PR #1264/#1265, PAS un merge candidate** ; la réconciliation de diff et des suites PR globales reste à faire avant un éventuel GO de fusion distinct.
- **NEXT exact** : vérifier les runs PR-transverses sur HEAD de #1267 après création ; préparer garde Windows ACL/stockage local/restauration sur LAB, puis découper et intégrer le QR dans des PR de production contrôlées **seulement après décision humaine séparée**. 08.2-E et 08.4–08.6 non clos. Certification `CODE_CERTIFIED` officielle à la fin de tout LOT08.

## LOT08 — OS KILL & DEVICE REVOKE GUARD — 2026-11-10

- **Décision propriétaire** : « Next » après la clôture des premiers FUE-I ; poursuite en DRAFT sans merge, migration, installation ou déploiement. Base master recontrôlée `027a82aca4cc37308f6323e759283c4ca0e45fad`.
- **08.3 PR #1265** : branche `feat/v15-08-3-atomic-commit-guard-fue0-20261110`, dernier HEAD source `f6e4df6553826aca06d2f01fc83674baf5018634`. FUE nouvelle : un **vrai processus enfant Python distinct**, utilisant `AuthorizedLocalQueue.perform` sur SQLite isolé, réalise `db.flush()` pour la visite et les 2 événements avant commit ; le parent le tue réellement (`process.kill()`, SIGKILL Linux), rouvre ensuite le fichier et prouve PLANNED version 0 / zéro événement, puis check-in de reprise valide version 2 / 2 événements. [Run exact SHA #42818314843](https://github.com/hraaaaf/Digital_crown/actions/runs/42818314843) **SUCCESS : 145 PASS, 3 SKIPPED**, artifact JUnit #13764853528. Ne prouve NI coupure d'alimentation, NI RPO/RTO de backups.
- **08.2-C PR #1264** : branche `feat/v15-08-2-c-device-pairing-fue0-20261110`, dernier HEAD `88ebec4244519182ee6445056ba47702f305bd14`. Nouveau garde INTERNE `_guarded_device_session` dans `DurableDeviceStoreLab` prend les verrous **auth BEGIN IMMEDIATE puis devices BEGIN IMMEDIATE**, contrôle la session vivante et garde les locks tant que l'appelant est dedans. Trois tests : la révocation admin attend la sortie du garde, mauvais tenant/révocation préalable refusés, exception libère les verrous. [Run exact SHA #42819299776](https://github.com/hraaaaf/Digital_crown/actions/runs/42819299776) **SUCCESS : 147 PASS, 3 SKIPPED, 4 subtests**, JUnit #13765538815. `require()` demeure un simple contrôle ponctuel, **interdit pour une mutation QR**.
- **Contrat 08.2-D/08.4 PR #1266** : même branche documentaire `docs/v15-08-2d-08-4-qr-api-contract-20261110`, section dédiée à la prévention TOCTOU et aux verrous **auth → devices → queue**. La future arrivée Kiosk doit garder ces locks jusqu'au commit Queue, sans rappeler `AuthorizedLocalQueue.perform` qui reprendrait le verrou auth ; toutes les écritures (QR consommé + version visite + ARRIVED + WAITING_ENTERED + idempotence) doivent se situer dans **un seul fichier SQLite Queue / une transaction**. Le fichier devices n'est que lu sous verrou. Pas de garantie mensongère de commit atomique distribué entre trois fichiers SQLite.
- **PROOF CI au dernier relevé** : PR #1265 SHA exact 7 SUCCESS / 1 SKIPPED / 0 ACTIVE ; PR #1264 SHA exact 5 SUCCESS / 1 SKIPPED et 2 runs LOT07 transverses encore actifs, aucun FAIL constaté. Les deux FUE ciblées sont SUCCESS. Tous trois PR restent DRAFT, non fusionnés. `master` inchangé.
- **NEXT exact / HUMAN GATE** : exécuter le FUE de jonction auth + devices + queue avec **acquisition unique des verrous**, check-in Kiosk et révocation concurrente, test anti-rejeu/idempotence QR sur une base Queue isolée, puis FUE de restauration sauvegarde/coupure sur LAB. Ne pas composer de transaction QR à partir du garde et de la méthode publique `perform` actuels (risque de deadlock), ni utiliser patient réel. Certification officielle CODE_CERTIFIED seulement après clôture du LOT08, NO_INSTALLABLE_GO. Notion consigne les dernières preuves. 

## LOT08 — 08.2-C / 08.3 / 08.2-D 08.4 PARALLEL DRAFT — 2026-11-10

- **Décision / contexte** : propriétaire « Go then » autorise développement parallèle isolé après la fusion validée de 08.2-B. MASTER prouvé à l'ouverture : `027a82aca4cc37308f6323e759283c4ca0e45fad`. PR #1239 CLOSED/MERGED sur ce SHA ; 08.1, 08.2-A, 08.2-B fusionnés. Anciennes sections plus bas disant « #1239 DRAFT / NO MERGE » : historique, non état actuel.
- **08.2-C, PR #1264 DRAFT** : branche `feat/v15-08-2-c-device-pairing-fue0-20261110`, HEAD `3189bc446990ea19e8301098d3bc5420b82596da`. Après FUE-0 in-memory, SQLite **isolé et explicitement initialisé pour LAB**, contrôle Admin `device.manage` vérifié sur la session locale vivante, tickets/bearers empreintes seulement, re-pair et révocation durables, tests restart, expiration, concurrence. [Run #42814174960](https://github.com/hraaaaf/Digital_crown/actions/runs/42814174960) **SUCCESS exact HEAD : 144 PASS / 3 SKIPPED + 4 subtests**, JUnit #13762474172. RED historique #42813994051 : assertion de test incorrecte pour bearer Admin malformé, corrigée sans assouplissement RBAC. **NON clos** : ACL Windows réelles, vrais appareils, usage du verrou de révocation pendant chaque mutation QR/Queue, reprise physique/cryptographie production.
- **08.3, PR #1265 DRAFT** : `feat/v15-08-3-atomic-commit-guard-fue0-20261110`, HEAD `b067bc8f7b657b798fe338c82d245c479e28af65`. Garde d'atomicité avant SQL dans moteur SQLite existant, sans duplication ; corruption événement => zéro écriture, panne simulée APRÈS `db.flush` AVANT commit => rollback intégral et reprise depuis nouvelle connexion, concurrence 2 check-ins => 1 seul gagnant. [Run #42814094809](https://github.com/hraaaaf/Digital_crown/actions/runs/42814094809) **SUCCESS exact HEAD : 17 ciblés PASS, full 144 PASS / 3 SKIPPED**, JUnit #13763407858. **NON clos** : crash du processus OS/killed, coupure électrique, restauration sauvegardes/RPO/RTO et concurrence inter-processus à certifier séparément.
- **08.2-D / 08.4, PR #1266 DRAFT** : branche `docs/v15-08-2d-08-4-qr-api-contract-20261110`, contrat uniquement `docs/v1.5/V15_08_2D_08_4_QR_API_PARALLEL_CONTRACT_20261110.md` ; QR Queue APPOINTMENT opaque, une seule consommation, 15 min par défaut 5–30, transition ARRIVED + WAITING transactionnelle, séparé de Station 03.2, Patient QR 03.3 et Station arrivée 03.4. REST/SSE/webhooks, 7 jours d'idempotence, aucune API ni QR runtime livrée.
- **Dépendances** : implémentation 08.2-D attend 08.2-C durable + 08.3 transactionnel. 08.2-E/08.5/08.6 attendent intégration et FUE. LOT09 raccord clinique des interfaces existantes ; LOT10 preuves appareils physiques. CODE_CERTIFIED officiel reporté jusqu'à clôture complète LOT08. Aucun merge de PR 1264–1266 ni activation, migration, déploiement, patient réel ou installateur. NO_INSTALLABLE_GO.
- **NEXT** : inspecter les deux derniers workflows transverses LOT07 encore actifs par PR (même si les FUE Queue exact-HEAD sont GREEN) ; compléter la frontière de transaction **device revocation + Queue commit** sans TOCTOU, la récupération après OS kill et les ACL Windows sur LAB séparé. 08.2-D QR runtime seulement après contrats stables. Aucun merge implicite ; NOTION est la source de preuve la plus fraîche.

## LOT08.2-B / B-7d — RED CONFLICTS RECONCILED / LAB FUE-I PASS — 2026-11-09

- **Décision autorisée** : utilisateur « Go then », tests frontend B-7d sur le merge simulé et, après preuves de sécurité, réconciliation contrôlée de la **branche PR DRAFT #1239 uniquement**. Ne jamais merger la PR vers master, installer, créer une release, utiliser de vrais dossiers patient ou approuver automatiquement le visuel.
- **SOURCE** : branche `feat/v15-08-2-b-rbac-isolation-20261109` HEAD avant lot `c6954e6ec0c775c245754840ad532e6ed147640e`, master actuel confirmé `d4d2d144393fc884e01ca8734c1efa9fb0e0f2e3` (master antérieur `edbc24ed...` avait avancé de six commits LOT05 sans chevauchement des cinq conflits). Exact **5 fichiers / 6 blocs** résolus dans worktree Git détaché sans modification de master, conservant tests de provenance/identité patient, tests blob/PDF authentifié, audit AST et garde Hub Windows, gouvernance FUE. Hash SHA256 des cinq résolutions identique entre simulations master anciennes et actuelles, 0 unmerged, git diff --cached --check PASS.
- **FUE frontend** : 5 suites chacune dans un processus indépendant avec **1 worker**, toutes **exit 0** : audit ClientFacingCopy 13/13, Documents M4-C 6/6, Hub 8/8, PrescriptionForm 7/7, PatientDraft 8/8 ; total **42/42 PASS**, zéro erreur worker. L'ancienne exécution combinée 42 assertions mais erreur onTaskUpdate/exit1 reste RED dans l'historique.
- **FUE backend** : Céphalo/Ortho **15/15 PASS / exit0** sur le merge précédent, contenus des cinq fichiers conflictuels inchangés après intégration master d4d2 ; aucune donnée patient réelle. Premier essai Queue Core sur l'arbre actuel **124 PASS / 3 FAIL / exit1** dû exclusivement au checkout sparse omettant le fichier Git suivi `installer/DigitalCrown.iss`. Après `git sparse-checkout add installer`, préflight **5/5 PASS / exit0** ; puis **régression complète Queue Core 127/127 PASS / exit0 / 158,86 s**, sur le même arbre fusionné. Les trois échecs initiaux restent conservés dans l'historique, mais le run complet final est maintenant réellement vert.
- **TypeScript final** : `tsc --noEmit -p tsconfig.app.json` **PASS / exit0** sur le master d4d2 fusionné, machine Windows 8 Go. Dossier de preuve [B-7d](docs/v1.5/V15_08_2_B_B7D_CONFLICT_RECONCILIATION_20261109.md) et manifeste 5 logs SHA-256 `docs/v1.5/evidence/lot08_2_b7d_master_conflict_sequential_20261109.json`, logs bruts hors dépôt.
- **GATES** : certification `CODE_CERTIFIED` master et `INSTALLABLE_CERTIFIED`, migration `/appointments`, tests Windows natifs installés/LOT10 physique **NOT_RUN / NOT_AUTHORIZED** ; B-6 `NO_INSTALLABLE_GO` demeure. [UI Human Visual Approval](https://github.com/hraaaaf/Digital_crown/actions/runs/42697010891) rouge attendu après changement HEAD et requiert de nouvelles preuves/screenshots et approbation **explicite** par propriétaire GitHub.
- **NEXT exact** : commit de réconciliation dans worktree isolé en respectant parent SHA exact, push uniquement vers branche DRAFT après vérification des références distantes, puis recontrôler PR/CI et documenter Notion. Aucune fusion vers master autorisée.



## LOT08.2-B / B-7c — 2026-11-09 — 388/388 FRONTEND FILES / 2035 TESTS WINDOWS SHARDED PASS · CI NOT VERIFIED

- **Décision GO utilisateur :** finir les lots 7–9 de Vitest Windows sous contrainte de 8 Go RAM, revalider les preuves machine et vérifier la CI GitHub du HEAD exact `66c2f3d4fb0efc6fa5d99a2d15211a5b02c4203f`. PR #1239 OPEN/DRAFT/NON MERGÉE, branch `feat/v15-08-2-b-rbac-isolation-20261109`, base master `324afd13487acf7ff29223f077451927b54b8178`.
- **RÉSULTAT OBSERVÉ (exhaustif sous plan de tests sharded)** : `frontend/src` contient **388 fichiers de tests**, répartis en **9 exécutions Vitest** de 48/48/48/48/48/48/48/48/4 fichiers, avec au maximum **2 workers**. **9/9 shards EXIT 0**, **388/388 fichiers PASS**, **2 035/2 035 tests PASS**, aucun FAIL dans les neuf groupes. Détail par shard : `271 + 264 + 215 + 263 + 274 + 237 + 268 + 224 + 19 = 2035`. Contrôle indépendant des neuf logs `ALL_VERIFIED=True FILES=388 TESTS=2035` / exit 0 ; par shard test/file count exact et SHA-256 des journaux enregistrés.
- **PREUVE CANONIQUE** : `docs/v1.5/evidence/lot08_2_b7c_windows_vitest_shards_20261109.json`, 9 empreintes SHA-256 de logs bruts non commités restant sur le PC de test `DigitalCrown-B7C-Shard-Evidence` ; rapport `docs/v1.5/V15_08_2_B_B7C_PRESCRIPTION_TIMEOUT_STABILITY_20261109.md`. Le code testé est le SHA `66c2f3d` avant commit documentaire. **Les exécutions Vitest globales non plafonnées antérieures restent RED**, ce PASS est une **validation exhaustive découpée**, pas un PASS d'un `npm test` monolithique.
- **Frontières** : tests ciblés B-7c plus anciens 34/34 PASS ; prescription plus forte (quatre presets, label, payload et ordre) et audit des libellés exhaustif par 48 sources, garde-brouillon patient intact. Aucune mutation de code clinique, patients, documents réels, installateur ou migration.
- **CI/GITHUB** : connecteur GitHub `fetch_commit_workflow_runs` limité à la première page des runs `pull_request` a retourné **0** ; un GET **public en lecture seule avec filtre exact `head_sha=66c2f3d`** a vérifié **1 run réel** : [UI Human Visual Approval #42686757746](https://github.com/hraaaaf/Digital_crown/actions/runs/42686757746), évènement `pull_request_target`, **FAILURE attendu** car `PR HEAD changed: approval revoked; new screenshots and explicit approval required`. Ce run ne prouve **aucune** CI Queue Core / Scope / CODE_CERT candidate au SHA testé ; elles restent **NON VÉRIFIÉES**. La PR est **mergeable_state=dirty** (conflits contre master) au contrôle public. Le CLI `gh` local est non authentifié, sans accès de dispatch CI. **Ne jamais contourner la gate visuelle humaine**. Politique `SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO` : tests natifs installés, `CODE_CERTIFIED` exact master, assets certifiés, LOT10 physique, vrai `/appointments` et humains **NOT_RUN/NOT_AUTHORIZED**.
- **BUILD + MÉNAGE** : `tsc --noEmit -p tsconfig.app.json` **PASS**, `npm run build:test` **PASS**, Vite PWA créé sous `dist-test`, manifeste `environment=test`, `commit=66c2f3d`, `mode=test`, **exit 0** ; jamais de build cabinet. La sortie de test `audit/out/frontend.json` et `frontend/dist-test` ont été vérifiées synthétiques puis supprimées ; seuls les logs de preuve externes au dépôt sont conservés.
- **NEXT EXACT** : committer rapport + manifeste dans PR DRAFT, vérifier nouveau HEAD et GitHub CI avec accès paginé, puis traiter les conflits `mergeable_state=dirty` et renouveler la preuve/approbation visuelle via décision séparée. Aucune fusion ou installation pour forcer un workflow.



## LOT08.2-B / B-7c — REAL PRESCRIPTION TEST TIMEOUT & EXHAUSTIVE AUDIT BATCHING — 2026-11-09

- **User GO:** continue the exact last RED: full frontend Vitest 2022 PASS / 1 FAIL (test-only PrescriptionForm quick-preset **5000ms timeout**), not a proven clinical prescription bug. PR #1239 DRAFT, starting SHA `82248e25c9eecc12c4b63052d40a9aee1c22a6f1`, no merge/install/deploy/clinical migration.
- **Oracle repair, NO clinical production code changes:** `frontend/src/features/admin/DocumentStudio/PrescriptionForm.g4Interactive.test.tsx` checks all four quick-preset names, order, payload drug name and exact 4 calls to `onApplyPreset`, with explicit 20s load budget. BEFORE the same isolated unchanged PrescriptionForm file passed **7/7**, actual test time **2.77s**; the RED was runner timeout only, not a callback assertion.
- **Second load failure discovered:** monolithic AST `ClientFacingCopyCandidateAudit.test.ts` timed out even at 20s during a four-suite focused run. Converted to exhaustive **48-file** source batches using identical source discovery filter, same per-file AST/technical-copy rules; new positive source count/unique/flatten coverage assertion, no exclusions and no weaker language scanning.
- **FUE-I Windows focused actual:** the four sensitive suites (copy audit, PrescriptionForm, patient draft-guard, M4-C documents) **34/34 PASS** across **4/4 files**, process exit 0; previous patient draft active-identity+empty editor test retained. Further TypeScript and full default frontend Vitest run currently in progress. `frontend/src/ClientFacingCopyCandidateAudit.test.ts`, `frontend/src/features/patients/PatientDraftRouteGuard.test.tsx` were previously local-uncommitted at `82248e2`.
- **Clinical safety boundaries:** no actual medication instructions altered, no prescribing algorithm clinically certified, no real patient data. `CODE_CERTIFIED`, `INSTALLABLE_CERTIFIED`, physical LOT10 and real `/appointments` migration **NOT_RUN/NOT_AUTHORIZED**; LOT08.2-B OPEN. Repro/report `docs/v1.5/V15_08_2_B_B7C_PRESCRIPTION_TIMEOUT_STABILITY_20261109.md`.
- **NEXT EXACT:** read full Vitest/TypeScript verdict; fix proven residual failures without dropping tests, compile/build if relevant, push safe verified changes only to DRAFT PR #1239, verify GitHub exact HEAD workflows and Notion. GitHub CLI local PC is not authenticated, so do not invent run IDs or CI state.



## LOT08.2-B / B-7 — RED / 3 FAILED CODE_CERT CANDIDATE ASSERTIONS — 2026-11-09

- **Décision :** GO « Red » : traiter les **trois échecs** du workflow GitHub candidat `Cabinet CODE_CERTIFIED candidate regression (no package)` [#42644548911](https://github.com/hraaaaf/Digital_crown/actions/runs/42644548911) au HEAD `c64d9e94077fb63bb6c37e3b80cf24d477dab3dc`. PR #1239 `feat/v15-08-2-b-rbac-isolation-20261109` OPEN/DRAFT/non mergée. Ne pas fusionner, déployer, créer d'installable ni migrer des patients.
- **CAUSE PROUVÉE logs :** frontend Vitest **2022 PASSED/1 FAILED** sur signature `handleView(doc.id)` qui ne correspond plus à l'appel réel sécurisé `handleView(doc.id, doc.name)`. Backend **5918 PASSED/2 FAILED/30 SKIPPED** : `test_cephalo_v1_l3_a4_document` simule un média sans `patient_id`, T0, provenance/date conformes et se heurte au **refus sécuritaire légitime** du lecteur ; `test_ortho_frontend_fail_closed_contract` exige un avertissement clinique littéral manquant dans le composant PDF Step4. Contrôle PostgreSQL/JWT candidat indépendant SUCCESS.
- **CHANGEMENTS MINIMAUX :** mise à jour de l'assertion frontend vers la vraie signature à deux arguments, renforcée par assertions du rattachement patient du blob ; correction de la fixture positive Céphalo avec T0 / patient 42 / upload / slot / version / date réels, **trois nouveaux cas négatifs** patient étranger, mauvais timepoint et image sans provenance pour vérifier l'absence de lecture des bytes ; ajout de l'avertissement clinique visible près des actions PDF dans Step4. Aucun garde de sécurité de production retiré ; le lecteur Céphalo et le module patient Documents restent inchangés.
- **Preuves locales initiales :** process isolé `ENVIRONMENT=test`, `sqlite:///:memory:` avec données fictives ; tests backend Céphalo+Ortho **14/14 PASS**, Vitest M4-C **6/6 PASS**. Premier **Vitest complet Windows 2019 PASS / 3 FAIL + 1 suite en erreur**, isolés en 2 fixtures Git absentes du sparse-checkout local, 1 assertion LF-only sous Windows CRLF et 1 test avec timeout 5 s. Après ajout des fixtures suivies Git **sans changement de code** et correction d'un seul test de portabilité CRLF en conservant l'assertion de garde exacte, les 4 suites ciblées **16/16 PASS**, y compris le timeout en isolation. Il ne s'agit pas d'un nouveau run complet vert. **TypeScript tsc PASS**, **build gardé npm run build:test PASS** vers `frontend/dist-test` avec manifest `mode=test`, sans installation. Nouveau Vitest Windows complet en cours dans checkout élargi ; CI Github sur SHA final à vérifier ; ne pas déclarer le candidat CODE_CERTIFIED tant que la CI complète n'est pas verte.
- **Dossier :** `docs/v1.5/V15_08_2_B_B7_CANDIDATE_RED_REPAIR_20261109.md`. Dernier **B-6** source-only maintient `SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO`, LOT08.2-B OPEN, tests natifs/physiques LOT10 NOT_RUN, aucune donnée patient réelle.
- **Next exact :** finir les régressions, pousser uniquement sur la même PR DRAFT, contrôler les runs de certification candidate au SHA exact, documenter Notion. CEPH experimental et Mobile Pocket restent des workflows séparés non clos sans preuve.



## LOT08.2-B / B-6 — DESKTOP INSTALLABLE ACCEPTANCE CONTRACT — 2026-11-09 — SOURCE PREFLIGHT PASS / NO GO

- **GO utilisateur :** « Go » pour définir et tester les conditions d'acceptation du véritable Desktop installable ; aucune autorisation de merge, de certification master, de build EXE, d'installation ni de migration clinique. PR #1239 DRAFT/OPEN, HEAD source avant ce sous-lot `b003528a744f78ad4a9375e7de0eb70762f38b34`.
- **Décision unique :** le LAB Queue Core et sa CI ne constituent pas `CODE_CERTIFIED` ni `INSTALLABLE_CERTIFIED`. Le vrai binaire installable exige les gates de `docs/CABINET_CERTIFIED_RELEASE_POLICY.md` : SHA exact master → CODE_CERTIFIED+Sigstore → assets scientifiques certifiés au même SHA → INSTALLABLE_CERTIFIED+7 manifestes → packaging natif fail-closed → FUE installable sur PC fictif → GO distinct de migration patients et LOT10 physique.
- **Livré :** matrice de décision exhaustive `docs/v1.5/V15_08_2_B_B6_DESKTOP_INSTALLABLE_ACCEPTANCE_20261109.md` avec Success/Proof/STOP et états PRESENT/NOT_RUN/NOT_AUTHORIZED. Nouveau préflight source **READ-ONLY** `scripts/v15_08_2_b_desktop_installable_preflight.py` : SHA 40 hex exact, dix garde-fous source inspectés, détection de couplage entre `WaitingRoomPage` et Queue Core LAB, rapport permanent `installable_ready=false` / `clinical_go=false`; aucun accès cabinet, installation ou package. `queue_core/tests/test_installable_source_preflight_08_2_b.py` injecte source altérée, mauvais SHA, refus de sortie dans repo, état NO GO.
- **Preuves source Windows Python 3.12 :** `SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO`, **10/10 contrôles statiques PRESENT** ; **5/5 tests ciblés de préflight PASS** ; suite globale Queue Core finale **127/127 PASS / 95,37 s**, compilation et diff-check PASS. Préflight désormais **strictement lecture seule** (stdout simple ou `--json`, aucune option de fichier de sortie). Les protections doivent encore être exercées sur un vrai artefact certifié avant acceptation native ; CI au nouveau SHA à relever après push.
- **Source canonique existante :** `docs/CABINET_CERTIFIED_RELEASE_POLICY.md`, `docs/quality/REALITY_PROOF_GATE.md`, `installer/DigitalCrown.iss`, `DigitalCrown.spec`, `run.py`, `docs/handovers/2026-11-07-restore03-installable-candidate-preflight.md`. La preuve B-5b sur le SHA `b003528` est Queue Core Linux **119 PASSED / 3 SKIPPED** et Scope Gate SUCCESS ; `Cabinet CODE_CERTIFIED candidate regression (no package)` était QUEUED au contrôle et **n'est pas une certification master**.
- **STOP / NEXT EXACT :** LOT08.2-B reste OPEN. Finaliser régression, exact-head PR/CI, mettre Notion à jour ; toute promotion vers master/installable et tout test sur clinique nécessitent un GO humain séparé. Ne pas créer de pourcentage non prouvé.



## LOT08.2-B / B-5b — RED CI DEPENDENCY ISOLATION — 2026-11-09 — WINDOWS PASS / LINUX CI PENDING

- **GO utilisateur :** « Red », traiter le blocage critique suivant de la PR #1239, sans fusion, installation, déploiement ou migration patient. HEAD avant fix `10ff5f55b4ec43709ad23e7f1b7a4e90f31283b9`. BRANCHE `feat/v15-08-2-b-rbac-isolation-20261109`, PR OPEN/DRAFT.
- **Cause constatée dans les logs GitHub :** [Queue Core #42634986803](https://github.com/hraaaaf/Digital_crown/actions/runs/42634986803) FAIL au SHA 10ff5f5 pendant **pytest collection, 0 tests exécutés**, `ModuleNotFoundError: email_validator`. La suite isolée Queue Core importait `backend.queue_core_desktop_lab`, ce qui importait d'abord `backend/__init__` et des schémas médicaux nécessitant `pydantic.EmailStr`. [Scope #42634986969](https://github.com/hraaaaf/Digital_crown/actions/runs/42634986969) SUCCESS. Ce n'était PAS un échec d'autorisation Queue Core.
- **Correction sécurité/architecture :** le module LAB existant, inchangé, est maintenant `queue_core/service/desktop_lab_bridge.py` ; `backend/queue_core_desktop_lab.py` est un shim de compatibilité vers cette implémentation, afin que l'authentique `backend.main` conserve sa composition. Tests Queue Core importent directement le module isolé ; nouveau test sur interpréteur vierge interdit l'import implicite de `backend`. Aucune dépendance clinique ajoutée, aucun skip de test ni affaiblissement de la CI ; aucun changement aux données, aux rendez-vous ni à la sécurité de production.
- **Proof Windows locale vérifiée :** `BACKEND_LOADED=False` import du module LAB depuis processus Python vierge ; suite ciblée Desktop 8/8 PASS ; suite globale `py -3.12 -m pytest -q queue_core/tests` **122/122 PASS / 82,28 s**, `compileall` et `git diff --check` exit 0. **Véritable `backend.main` ASGI synthetic** après shim : autorisation 403/401/200/CHECK_IN/logout/401, **exit 0**, sans démarrer `lifespan` clinique, et SQLite temporaire supprimée.
- **Document :** `docs/v1.5/V15_08_2_B_B5B_CI_ISOLATION_FIX_20261109.md`. CI au prochain SHA final à attester et Notion à synchroniser. **LOT08.2-B OPEN**, logiciel cabinet certifié/installer, essais physiques LOT10, données patients et migration `/appointments` NOT_RUN.
- **NEXT EXACT :** push contrôlé du correctif sur PR #1239 DRAFT, lire jobs/logs Linux et Scope Gate du nouveau SHA ; si échec changer de stratégie sans prétendre PASS, sinon actualiser Notion/PR. Aucune fusion ou déploiement non autorisé.



## LOT08.2-B / B-5a — REAL BACKEND.MAIN ASGI LAB FUE-I — 2026-11-09 — PASS / NO DEPLOY

- **Décision & périmètre :** GO « Green next » après B-5 Chromium LAB ; vérifier le véritable point d'entrée `backend.main:app` et ses middlewares via ASGI local synthétique. Aucun runtime clinique/lifespan, aucun installable ni migration patient ou de cabinet. Base git `3203eff850b081261ec7959cb81cc8f4a2bda782` PR #1239 DRAFT et non fusionnée.
- **Test autonome :** `queue_core/tests/desktop_main_lab_probe.py` : flag explicite `DIGITALCROWN_QUEUE_MAIN_FUE_RUN=1`, `ENVIRONMENT=test`, clinique `sqlite:///:memory:` et attestation runtime isolé, deux vraies SQLite temporaires B-2 + Queue Core avec comptes/visites fictifs, import réel `backend.main` **sans lancer clinical lifespan**, réseau absent ; test HTTP ASGI loopback réel sur la composition globale et les middlewares (synthetic `testclient` 403, 127.0.0.1 → 401 sans auth, 200 login/snapshot/check-in, 200 logout, 401 session révoquée). `backend.main` garde `WaitingRoomPage` clinique historique intacte. Commande : `$env:DIGITALCROWN_QUEUE_MAIN_FUE_RUN='1'; py -3.12 -m queue_core.tests.desktop_main_lab_probe` → **exit 0 / ACTUAL_BACKEND_MAIN_ROUTING_AND_RBAC_PASS_NO_CLINICAL_LIFESPAN**. Fermeture explicite moteurs SQLAlchemy pour suppression des fichiers Windows.
- **Écarts rencontrés et résolus :** `relay` absent seulement du sparse-checkout local, ajouté sans changement source ; testclient ASGI synthétique 403 attendu car seul loopback réel est autorisé ; SQLite test verrouillée pendant nettoyage initial, puis `engine.dispose` et rerun code 0. Warnings imports modèle Pydantic / ONNX absent dans sparse checkout non bloquants pour ce test.
- **Preuve :** `docs/v1.5/V15_08_2_B_MAIN_ENTRYPOINT_FUE_I_20261109.md`. B-5 précédent : FUE-G navigateur Chromium 19/19 PASS + captures 7, suite locale Windows 121/121 PASS, build:test isolé PASS. Le présent FUE-I **n'est pas** un test du cycle de vie de l'application clinique, du paquet installable, du contenu patient ou des machines cabinet. LOT08.2-B OPEN / LOT10 PHYSICAL NOT_RUN.
- **CI :** Scope Gate sur HEAD B-5 3203eff SUCCESS ; Queue Core #42632131539 encore QUEUED au relevé ; le prochain commit B-5a nécessite une vérification CI sur son SHA propre avant tout jugement. Aucun merge / déploiement / Vercel.
- **Next exact :** attester CI exact-SHA, documenter Notion + PR, puis isoler les critères d'acceptation d'un candidat Desktop installable avant tout test patient réel.



## LOT08.2-B / B-5 — DESKTOP LOCAL LAB FUE-G — 2026-11-09 — PREUVE BROWSER PASS / B OPEN

- **GO utilisateur :** raccorder B-4 HTTP/SSE au runtime Desktop local en laboratoire, FUE-G navigateur, sans fusion/déploiement/installation ni patient réel. PR #1239 DRAFT, HEAD avant B-5 `16bf642d2558380326e89fea3ac049308048de0f`, base master `324afd13487acf7ff29223f077451927b54b8178`.
- **Reality check :** Desktop réel `run.py → backend.main:app` + React ; `WaitingRoomPage.tsx` existante utilise les vrais `/appointments`. Aucune mutation de ce workflow ni de données cliniques. Montage `backend.queue_core_desktop_lab.attach_queue_core_lab` derrière flag + environnement `test` uniquement, deux fichiers SQLite synthétiques préexistants, marqueur explicite ; le montage dans `backend/main.py` est opt-in et exclut cabinet/production. Login opérateur B-2 tenant résolu serveur, rôles/grants seulement comme indices UI, RBAC toujours côté serveur.
- **Client LAB :** `frontend/src/features/queue-core/QueueCoreLabPane.tsx`, route React dév protégée `/queue-core-lab` plus entrée Vite de test isolée `/queue-core-fue.html`. Un navigateur réel utilise token Bearer volatile (pas URL/cookie/storage), fait check-in→call→chair→done, affiche les événements SSE, cache les actions non autorisées, et efface les visites immédiatement si le flux est clos/révoqué.
- **FUE-I :** montage Desktop 8/8 PASS, tests ciblés montage+HTTP/SSE 21/21 PASS, Python 3.12 Windows. **FUE-G navigateur :** Chromium + Python FastAPI et Vite sur processus loopback distincts, deux SQLite temporaires, 19/19 checks PASS, 7 captures 390/768/1280 et JSON hashes SHA256 ; aucune erreur navigateur inattendue ; vérification du 401 après révocation externe. Preuve : `docs/v1.5/V15_08_2_B_DESKTOP_LAB_FUE_G_20261109.md` et `docs/v1.5/evidence/lot08_2_b5_fue_g_20261109/`.
- **CI et gates :** re-tests complets Windows Python 3.12 **121/121 PASS (89,32 s)**, compilation Python PASS, TypeScript `tsc --noEmit -p tsconfig.app.json` PASS, build gardé `npm run build:test` PASS dans `frontend/dist-test` sans toucher au dist cabinet ; GitHub CI au SHA final à vérifier après push. FUE-G est **LAB navigateur synthétique**, PAS une session clinique native installée ; aucune preuve USB/Windows installer/TLS LAN, ni intégration aux rendez-vous cliniques ; LOT10 physique NOT_RUN. **LOT08.2-B OPEN, PR DRAFT, aucun merge/déploiement.**
- **Next exact :** relever résultats locaux et Actions exact SHA, POST Notion, puis définir gate distinct pour intégration dans candidat Desktop certifiable, sans exposer de vrais patients.



## LOT08.2-B / B-4 — HTTP/SSE LOCAL ASGI — 2026-11-09 — FUE-I PASS LAB, B OPEN / NO MERGE

- **GO user :** développer la vraie interface HTTP/SSE du Queue Core depuis le B-3 in-process, sans fusion, installation, déploiement ni patient réel. PR #1239 DRAFT, base master 324afd13487acf7ff29223f077451927b54b8178 ; HEAD avant B-4 a94343a12f6045db5595e108763fe6cfd7d3068d.
- **Implémenté :** queue_core/service/http_transport.py, factory FastAPI ASGI locale (aucun socket démarré), POST commandes, GET snapshot, GET replay paginé, GET SSE streaming (text/event-stream). B-2 session Bearer obligatoire depuis Authorization header, local loopback peer+Host, pas de credentials URL/cookie, Docs/OpenAPI/CORS fermés, refus 401/403, schéma HTTP fermé à l'injection de tenant/actor, SSE recontrôle droit B-2 avant ouverture et avant chaque frame / heartbeat, reprise Last-Event-ID tenant/queue, évents minimisés sans secret et IDs validés. Ajout queue_core/service/authorized_queue.py require_queue_read() à validation fraîche.
- **FUE-I transport local réel (sans réseau) :** queue_core/tests/test_http_sse_08_2_b.py, FastAPI TestClient + httpx.ASGITransport, 13 scénarios HTTP/SSE réels / négatifs avec deux vraies SQLite isolées et données synthétiques : commandes 0→2→3→5→7, IDOR, token, non-loopback, host, corps malformé, paginated replay, cursor, SSE révocation au milieu d'un lot d'événements et anti-injection de champs SSE. Suite Windows Python 3.12 après modifications : **113/113 PASS / 46,20 s** ; compileall et git diff --check exit 0.
- **CI GitHub vérifiée sur commit transport f75bc8dc6acab24720c89fadfafceb72741b6e76 :** workflow .github/workflows/v15-08-1-queue-domain-fue0.yml avec dépendances isolées FastAPI/httpx/anyio/pydantic/starlette ; run #42620845974 COMPLETED/SUCCESS, job #129172271703, logs Linux Python 3.11 : **110 PASSED / 3 SKIPPED / 31,19s** ; Scope Gate run #42620845954 SUCCESS. Les skips ne sont pas des passes. Le commit final de documentation/STATE appelle sa propre CI, dont le verdict doit être consigné dans Notion. Preuve : docs/v1.5/V15_08_2_B_HTTP_SSE_FUEI_20261109.md.
- **LIMITES :** aucun serveur écoutant, TLS, Windows packaging, client navigateur/UI ni expérience opérateur physique ; FUE-G non exécuté, LOT10 PHYSICAL NOT_RUN. Un octet déjà envoyé ne peut pas être retiré après révocation. Architecture non déployée/non activée en cabinet. LOT08.2-B OPEN, pas de merge ni production.
- **Next exact :** vérifier la CI Linux et Scope Gate au SHA poussé, enregistrer Notion, puis réconcilier l'interface vers le périmètre 08.3 et effectuer FUE-G/browser quand un vrai client est disponible. Pas de pourcentage inventé.



## LOT08.2-B — LOCAL COMMAND/REPLAY ADAPTER FUE-I — 2026-11-09 — CANDIDATE / NO MERGE

- **GO utilisateur :** après B-2 FUE-0, intégrer le contrôle humain aux vraies commandes/lectures événementielles du Queue Core, FUE proportionné ; aucune revue indépendante obligatoire par défaut, mais contrôles SEC/IDOR/intégrité systématiquement négatifs. Pas de GO fusion ou mise en production.
- **Source réelle vérifiée :** PR #1239 DRAFT sur base master 324afd13487acf7ff29223f077451927b54b8178 ; HEAD avant travaux a642bb38d26c5b6420456fc02867e2da8ea5d6b7. Domaine et tables Queue Core existants ; aucun HTTP/SSE runtime existant.
- **Implémentation :** queue_core/service/authorized_queue.py : adaptateur local in-process sur le vrai domaine Queue Core et la base SQLAlchemy séparée de la SQLite auth B-2 ; RECEPTION check-in, STAFF call/recall, CHAIR/DONE grants séparés, NO_SHOW/override explicites, verrou de transaction auth→queue, scope tenant/visite/ressource résolu depuis le serveur, événements minimisés, pagination/replay et queue snapshot réautorisés à chaque appel. Aucun listener, create_all, migration, données patient ni identité Device.
- **FUE-I local :** 11 tests sur 2 SQLite temporaires avec commandes/vrais événements, IDOR, annulation/révocation, cursor cross-tenant, concurrence command→revoke et pagination. FUE-I ciblé 11/11 PASS ; suite globale Windows Python 3.12 finale 100/100 PASS (33,65s), compileall et git diff --check PASS ; CI GitHub au SHA final à relever après push. Preuve : docs/v1.5/V15_08_2_B_LOCAL_SERVICE_FUEI_20261109.md.
- **Limite critique :** ce FUE-I concerne l'adaptateur local **sans transport HTTP/SSE**. Aucune preuve FUE-G/browser/SSE live ni physique (LOT10 NOT_RUN). Le prochain vrai endpoint/service devra revalider les autorisations par requête, souscription, replay et événement émis. B RESTE OPEN ; ne pas fusionner, déployer ou créer de comptes cabinet.
- **NEXT EXACT :** terminer re-test Windows + CI GitHub exact-SHA, consigner Notion, puis poursuivre l'intégration transport uniquement sur périmètre autorisé quand 08.3 expose un vrai service. Ne pas revendiquer de service HTTP déjà livré.



## LOT08.2-B — FUE-FIRST remplacement gate reviewer — 2026-11-09 — B-2 FUE-0 PASS / B OPEN

- **Décision utilisateur :** la revue indépendante systématique est substituée par le FUE approprié, conformément à SKILLS.md FUE-first ; les contrôles SEC/data/révocation restent obligatoires selon les risques. Pas de revue artificielle ni de sign-off humain inventé.
- **Base vérifiée :** PR #1239 DRAFT au SHA de départ `43581796b4c57223ddd734f8b2d35bc68ab2be72`; base master `324afd13487acf7ff29223f077451927b54b8178`.
- **FUE-0 exécuté sur Windows Python 3.12 :** nouveau `queue_core/tests/test_fue_08_2_b.py` : 3/3 PASS (SQLite réel isolé : reprise, revoke/A recovery, concurrence sérialisée, fail-closed rôle corrompu). Suite complète `py -3.12 -m pytest -q queue_core/tests` : **89 PASSED**, compileall et diff-check PASS.
- **Protocole et limites :** `docs/v1.5/V15_08_2_B_FUE0_20261109.md` ; données fictives, pas de clinique, FUE-I/G indisponible (routes/API/SSE pas encore implémentés). Tests physiques exclusif LOT10. Aucune fusion/déploiement accordé.
- **Next exact :** confirmer la CI au HEAD final de ce checkpoint FUE puis traiter l'intégration des contrôles d'autorisation aux vraies commandes/flux dans un sous-lot distinct ; le lot B reste OPEN. Aucune validation FUE-G ou produit affirmée.



## LOT08.2-B — B-2 persistance opérateurs candidate — 2026-11-09 — OPEN / NO MERGE

- **GO owner 2026-11-09 :** poursuivre B-2 exclusivement après B-1 au HEAD `e0363e055fd4b31b3903b105229445e7252e1078` de PR #1239 DRAFT. Aucun GO de merge, déploiement, installation ou activation clinique.
- **B-2 implémenté en LAB isolé :** `queue_core/security/operator_store.py`, extension additive au fichier SQLite local de 08.2-A (distinct de toute DB clinique), premier Admin bind tenant contrôlé par garde local, opérateurs nominatifs, scrypt, sessions opaques, rôle unique, attributions file/ressource, grants explicites, audit append-only, last-admin et bootstrap immuable par API + trigger SQL. `local_auth.recover_admin` invalide désormais les sessions A et B atomiquement.
- **Preuve directe Windows Python 3.12 :** `py -3.12 -m pytest -q queue_core/tests` → **86 PASSED / 0 FAILED** (fixtures synthétiques SQLite temporaires uniquement) ; `compileall` et `git diff --check` exit 0. Ne pas assimiler cette preuve à une validation physique ou sécurité complète ; le SHA final et CI GitHub sont à consigner après commit.
- **Contrat :** `docs/v1.5/V15_08_2_B_RBAC_ISOLATION_CONTRACT.md`, nouvelle section B-2 avec limites. `test_operator_store_08_2_b.py` fournit tests persistés, tenant/IDOR, droits, expiration, lockout, transactions, audit refus, rollback et récupération.
- **OPEN :** revue SEC ciblée sur SHA final et CI Linux/Windows applicable ; résolution serveur fiable des tenants/visites/ressources et couplage auth→commande/flux futurs non implémentés ; aucune route/API, service SSE ou installation. Scope mono-tenant local de B-2. Essais physiques exclusivement LOT10 NOT_RUN.
- **Next exact :** commit/push candidat sur PR #1239 DRAFT, inspecter CI exacte et revue SEC indépendante, corriger tout défaut critique et demander décision de fusion distincte une fois tous les gates logiciels requis satisfaits. Aucun merge automatique.



## LOT08.2-B — RBAC tenant-scopé / isolation — 2026-11-09 — B-1 EN COURS

- **08.2-A** : [PR #1238](https://github.com/hraaaaf/Digital_crown/pull/1238) MERGED sur master commit `324afd13487acf7ff29223f077451927b54b8178`; Windows CI 53/53 PASS au SHA source `1b4380735932896b8b7a38485b2af709182c796c`, physique `NOT_RUN / LOT10`. Un workflow transversal postmerge #42599749810 était IN_PROGRESS au premier relevé.
- **Décision propriétaire** : séquence 08.2-A → **08.2-B**, pas 08.3. G2 validé : Admin configuration/audit sans droits opérationnels ; accueil check-in/QR ; staff call/recall ; CHAIR/DONE distincts, NO_SHOW et queue.override OFF par défaut, permissions par tenant/file/visite/ressource.
- **B-1 candidat (PR DRAFT, non fusionné)** : policy pure `queue_core/security/rbac.py`, oracles synthétiques d'isolation/refus/révocation via resolver de session live, contrat `docs/v1.5/V15_08_2_B_RBAC_ISOLATION_CONTRACT.md`. La présence de code + tests ne constitue PAS une preuve d'auth multi-opérateurs persistante ni une certification des flux.
- **B reste OPEN** : persistance isolée des opérateurs nominaux, rattachements/permissions et authentification par compte, révocation immédiate de sessions, preuve last-admin et contrôle réellement appliqué sur chaque future commande/flux, revue SEC indépendante et CI au SHA avant GO de merge. C/D/E, 08.3, déploiement, cabinet et données patients hors périmètre.
- **Next exact** : CI Python/tests existants + nouveaux tests RBAC, examiner SEC et compléter durable store/transactions ; aucune validation physique avant LOT10.

## DÉCISION PROPRIÉTAIRE — 2026-11-09 — LOT08 logiciel/LAB ≠ LOT10 physique

**Cette décision prime sur les anciens checkpoints « NO-GO merge car tests physiques non exécutés » contenus plus bas.** La roadmap officielle [V1.5-10 — Tests physiques exclusivement](https://app.notion.com/p/3e677c66336281fcbe65f8889baf8c6a) réserve la validation matérielle/terrain au **LOT10** : 10.1 (installation postes), 10.2 (Queue Core réel), 10.7 (incidents/sécurité terrain), 10.8 (réception humaine). Le premier enrôlement physique Admin `issue→enroll→recover`, les ACL sur installation réelle, la récupération offline et le refus d'autres profils sont **PHYSICAL NOT_RUN / LOT10**. Ils ne sont **pas un préalable de clôture logicielle/merge du LOT08.2-A** ; l'utilisation clinique reste interdite jusqu'aux gates terrain applicables.

**Preuves 08.2-A :** [Windows Actions #42596486051](https://github.com/hraaaaf/Digital_crown/actions/runs/42596486051) SUCCESS sur SHA exécutable `1b4380735932896b8b7a38485b2af709182c796c`, **53/53 tests PASS**, création Win32 et vérification ACL réelles uniquement sous RUNNER_TEMP, refus CLI non interactive sans modification ProgramData, refus ACL non conforme ; [Ubuntu FUE-0 #42596493320](https://github.com/hraaaaf/Digital_crown/actions/runs/42596493320) SUCCESS. Une **décision de clôture du logiciel** doit considérer revue SEC, CI, risques et périmètre, sans exiger le terrain physique.

**PR #1238 :** reste DRAFT/non fusionnée **en attente d'une décision d'intégration distincte du propriétaire et des contrôles logiciels applicables, pas d'une preuve physique LOT10**. Pas de déploiement, d'installation cabinet ou de passage automatique à 08.2-B–E. **Next exact :** revoir les preuves et le diff logiciel A, proposer décision de merge ; si approuvée, merge + contrôles post-merge, puis poursuivre roadmap logicielle. Les précédentes mentions contradictoires documentent le gate erroné désormais supersédé.

## LOT08.2-A — Windows GitHub Actions ACL complémentaire — 2026-11-09 — CI PROUVÉ / PHYSIQUE OPEN

- **PR #1238 : OPEN/DRAFT/NOT MERGED**, [preuve Windows Actions #42596486051](https://github.com/hraaaaf/Digital_crown/actions/runs/42596486051) **SUCCESS** sur SHA exact testé `1b4380735932896b8b7a38485b2af709182c796c`, Windows hosted runner et Python 3.12. La suite `queue_core/tests` **53/53 PASS** ; non-interactive `status` refusé `INTERACTIVE_CONSOLE_REQUIRED` sans effet sur ProgramData ; **vraie création Win32 d'un dossier et fichier temporaires** sous RUNNER_TEMP avec validation owner/ACE réelle Get-Acl + refus ACL non conforme. Artifact JUnit non médical. Aucun accès cabinet ni donnée patient.
- **Linux FUE-0 existant** [#42596493320](https://github.com/hraaaaf/Digital_crown/actions/runs/42596493320) **SUCCESS** sur ce SHA ; correctif de l'oracle du test de refus sous non-Windows (attendre LOCAL_WINDOWS_CONSOLE_REQUIRED) inclus. Le code sécurité runtime est resté inchangé depuis le SHA source sécurité revu `44bc6fc639332796f064dbf18a59a4f8b5c3333f`.
- **Diagnostic des premiers FAIL :** Powershell 7 runner -> sous-processus Windows PowerShell 5.1 incapable d'auto-charger `Microsoft.PowerShell.Security` pour `Get-Acl`. La même vérification exécutée directement sous Windows PowerShell 5.1 (shell natif dans Actions) est PASS. Ce n'était pas une preuve de permissions correctes tant que la vraie vérification n'était pas PASS.
- **STOP MAINTENU :** runner hébergé ≠ console physique locale élevée. Aucun `issue→enroll→recover` réel à la console LAB, aucune vérification d'identité utilisateur non privilégié par second profil humain, aucune restauration hors ligne réelle sur poste LAB : **NOT_RUN**. Aucun merge, déploiement, installation cabinet, 08.2-B/C/D/E ni certification clinique autorisés. **Next exact :** Windows LAB physiquement isolé, Admin élevé local, recette première inscription + ACL + récupération offline, preuves expurgées, puis gate humain GO/NO-GO.
- **Fichier canonique :** ce checkpoint documentaire est ajouté après la CI ; le SHA testé `1b438073...` reste la preuve exécutable. Toute différence de SHA ultérieure doit être réconciliée par comparaison du delta, sans déclarer une nouvelle CI PASS si elle n'a pas tourné.

## LOT08.2-A — Local Windows identity/bootstrap — IN PROGRESS / DRAFT (2026-11-09)

- **2026-11-09 SEC review current source `44bc6fc639332796f064dbf18a59a4f8b5c3333f`**: independent read-only Codex delta review from `09f3d40e` reports **no actionable defect**. Prior full review found P2 stale expired session rows; corrected within serialized login transactions, including denied logins, with negative retention test. **53/53 direct Windows Python 3.12 PASS postcommit**, compileall exit 0, git clean. Directory/file SDDL accepted by Windows API without writes, remote CLI rejected with `INTERACTIVE_CONSOLE_REQUIRED` exit 2 and no real auth-store file created. [SEC review report](docs/v1.5/V15_08_2_A_SECURITY_REVIEW_20261109.md). **Physical elevated Windows console positive bootstrap/ACL NOT RUN; PR #1238 remains DRAFT / NO-GO merge or clinic install pending physical LAB proof**. No 08.2-B GO.

- **2026-11-09 independent Codex review on SHA 09f3d40e:** found P2 unbounded expired sessions retained in SQLite. Fixed under the login transaction by pruning `expires_epoch <= now` even on denied logins; added negative synthetic retention test. **53/53 direct Windows Python 3.12 PASS**, compileall and diff check PASS. New exact SHA and separate final review still required. Physical Windows local elevated console enrollment/ACL positive **NOT_RUN**; no clinical use, merge, 08.2-B or deploy.

- **2026-11-09 separate Codex review on e3513ac9:** no P1/P2 findings; one P3: read-only `status` unexpectedly created an auth directory before first enrollment. Fixed `windows_cli._database_path(initialize=False)` to inspect without creating, with a regression test. **52/52 direct Windows Python 3.12 PASS**, compileall and diff-check PASS. Fresh reviewer required on the *new* commit; physical elevated Windows-console positive enrollment/ACL still NOT_RUN, no real auth store created and no merge under this checkpoint.

- **SEC critical review #1, initial SHA 58e3b5e7:** independent targeted Codex SEC/OPS review identified P1 directory-owner ACL spoof and P2 dangling reparse bypass. Corrected with atomic Windows SDDL protected CreateDirectoryW/CreateFileW, trusted SID owner and both distinct required ACEs, non-following `lstat()` and `FILE_FLAG_OPEN_REPARSE_POINT`, with synthetic negative/static Win32/PowerShell tests. **51/51 direct Windows Python 3.12 PASS on preceding e3513ac9.** Subsequent 2026-11-09 review P3 correction now **52/52 PASS**. Real elevated physical console creation/ACL remains NOT_RUN. New SHA needs another independent security review before merge.

- **GOAL:** standalone Queue Core first Admin enrollment on a physically local elevated Windows console, no Internet, Firebase, patient records or clinical database access.
- **Owner GO:** « Play 8-2 A go ». This authorizes implementation of A only, not merge/release or 08.2-B–E.
- **BASE:** `edf26bb7ff70904b802069891f31ef3b4dc7691d` master (LOT08.1 CLOSED 29/29). Worktree `feat/v15-08-2-a-local-admin-bootstrap-20261108`, isolated branch.
- **DELIVERABLE CANDIDATE:** `queue_core/security/local_auth.py` (SQLite local auth + bootstrapping), `windows_console.py` OS privilege/console gate, `windows_cli.py` ProgramData ACL-controlled offline CLI, synthetic negative unit tests and `docs/v1.5/V15_08_2_A_LOCAL_ADMIN_BOOTSTRAP_CONTRACT.md`.
- **PRELIMINARY DIRECT WINDOWS EVIDENCE:** Python 3.12 `pytest -q queue_core/tests` **52/52 passed** (29 08.1 + 23 08.2-A incl. Windows ACL/symlink hardening and read-only status); compileall PASS. Real Remote Desktop Commander shell `python -m queue_core.security.windows_cli status` denied with `INTERACTIVE_CONSOLE_REQUIRED` exit 2; `ProgramData\DigitalCrownQueueCore\local_auth.sqlite` absent before/after. NO real admin account or recovery secret generated; tests use temp SQLite synthetic fixtures and injected guard.
- **SECURITY CONTRACT:** 256-bit random bootstrap (10min), single use/5-attempt cap; scrypt salted passwords, opaque SHA-256 session verifier and lockout, 8h sessions; separate 256-bit offline recovery secret, one-time rotation and all-session revocation. Restricted Windows physical console and ACL verification; no public route. No default admin.
- **UNVERIFIED / BLOCKED FOR REAL USE:** actual elevated physical Windows-console onboarding, DirectorySecurity Set-Acl success on target PC, backup/restore/installed service, session-cookie/network auth, multi-tenant RBAC, kiosk/QR, standalone runtime and legal G3. Risk-critical source needs independent SEC/OPS review on exact SHA before any merge, with negative tests and correction loops. No automation GitHub Actions requested.
- **NEXT:** commit & push DRAFT PR, direct Windows proof exact SHA, separate reviewer, POST Notion. Do NOT merge, install or begin 08.2-B without distinct GO.

## LOT08.1 — Queue Core domain contracts — CLOSED / POST-MERGE VERIFIED (2026-11-08)

- **GOAL:** isolated standalone Queue Core domain state machine, dynamic ranking, auditable event plans, dedicated SQLAlchemy schema and synthetic FUE-0. **Delivered:** G1 transitions/rank oracles, manual NO_SHOW and queue.override, tenant/resource constraints, active chair occupancy, provenance and SQL integrity checks. No clinical DB coupling, migration, patient data or runtime deployment.
- **RESULT:** [PR #1234](https://github.com/hraaaaf/Digital_crown/pull/1234) **MERGED**; final contributor SHA `1df36d79a694f713cb19b112ae26831501cf1678`; squash master SHA `a5c47f5efcc7b9843a9fea13799bae073ca541e7` (based on parent master `16f531f04eb7daff3bf5d75017717e12927f47ab`). Owner GO "Green" captured.
- **PROOF POST-MERGE Windows:** authorized device DESKTOP-3MAJEEH, isolated worktree checked out on the exact master merge SHA; Python 3.12 `pytest -q queue_core/tests` **29/29 PASS**, `compileall -q queue_core` **PASS**, clean git tree. No GitHub Actions tests deliberately launched; older green runs belong to earlier contributor SHAs and are not evidence for this one.
- **INDEPENDENT CODE REVIEW:** fresh Codex CLI read-only agent on final contributor SHA against updated `origin/master`: no definite actionable defects reported. Its default Python 3.14 lacked pytest; only separate Windows 3.12 tests substantiate FUE. Earlier distinct reviews identified P1/P2 defects corrected and re-tested. This is **AI code review, not medical or human signoff**.
- **CLOSEOUT SCORES (08.1 scope ONLY):** EXECUTION 9.0/10, FUE_EVIDENCE 9.0/10, RETAINED 9.0/10 (minimum). FUE-0 applicable and demonstrated, no UI exists in 08.1; FUE-I/G and installed runtime remain later sublots. Final independent review + postmerge tests serve as scoped Perfection Pass.
- **LIMITS:** `call_visit` cannot prove candidate completeness; future 08.3 MUST load authoritative candidates under DB transaction lock and atomically commit resource state, audit and versions. No durable append-only, encryption, RBAC, kiosk/QR, API/SSE, webhooks, UI, backups/restore or real patient enablement is claimed.
- **HANDOVER:** `docs/v1.5/V15_08_1_QUEUE_CORE_CLOSEOUT_20261108.md`; contract `docs/v1.5/V15_08_1_QUEUE_CORE_DOMAIN_CONTRACT.md`; historical detailed review trail in `techdoubt.md` and [canonical Notion LOT08](https://app.notion.com/p/3ec77c66336281d59cdcffe610561f86).
- **NEXT EXACT:** 08.2 local identity/RBAC/device/QR requires separate GO and fresh preflight; no 08.2 start, merge beyond closeout documentation, clinic release or Vercel deployment under this approval.

# LOT07 V1.5 Desktop Experience & MultiView — 2026-11-08 — INTEGRATED DELIVERY CLOSED (LIMITED SCOPE)

- **Scope closed:** R8.3 + POLISH-01 + POLISH-02 (historical merge and postmerge CI success 2026-10-31), plus Windows B10 true NVDA certification workflow fix PR #1228, source head `68279047d9d73a501f18a1e5c7fb235f241deae7` merged at `1131f117254894d208490b2b6916fd2a4799d18b`.
- **Proof B10 source:** Windows actual NVDA, native zoom and synthetic authenticated FastAPI/React [run #42481818872](https://github.com/hraaaaf/Digital_crown/actions/runs/42481818872) SUCCESS (18 screenshots, 104 checks), owner Human Visual Approval [#42504061075](https://github.com/hraaaaf/Digital_crown/actions/runs/42504061075) SUCCESS.
- **Proof postmerge:** [Cabinet Upgrade PostgreSQL Certification #42504229531](https://github.com/hraaaaf/Digital_crown/actions/runs/42504229531), **2/2 SUCCESS** on the B10 merge commit. Merge diff is exactly one CI workflow and one synthetic browser test script, no patient/clinical runtime changes.
- **Historical DRAFT disposition:** #1131 (R5) CLOSED/NOT MERGED, core R5 API/preferences modules present on master; #1109 (R3) CLOSED/NOT MERGED, historical 3-pane DEV pilot NOT SHIPPED. The nine declared layout starting points on master are **not nine independently certified clinical UIs**. Numerous historical DRAFTs remain outside this verified closure and are not silently certified. No clinical or patient data imported.
- **Future scope:** R3 prototype and missing 3-pane specialist views are **unshipped/deferred**, preserved in [Notion backlog](https://app.notion.com/p/41277c66336281cc9654e5e69fe4e2d4), with branch/PR history intact; if deemed REQUIRED by owner, reopen LOT07 scope before treating it as completed. No blanket clearance for unimplemented clinical interfaces.
- **Roadmap:** [LOT07 canonical closeout](https://app.notion.com/p/40277c66336281b6b7ffeeecae6baff9) and [V1.5 roadmap](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb). LOT08 G6 is cleared only for this delivered, bounded LOT07 scope. Resume LOT08 preflight against current master, and still lock G1-G5 before 08.1. 35 SP LOT08 re-estimate remains tentative, not approved baseline.
- **No release:** no Vercel, no cabinet PROD deployment, no physical multi-monitor / OS DPI200 field certification; physical tests at LOT10.

**NEXT EXACT:** Re-check current master SHA/CI, confirm relevant LOT07 closure and any REQUIRED scope exception; re-run LOT08 PRE / domain/tenant/visits before any LOT08 implementation. No implicit permission for real patient data, migration, merge of future features or production.

---


> Fichier de reprise canonique. Historique pré-audit : `docs/archive/STATE_2026-07-21.md`.

# Etat canonique scientifique — 2026-10-07

## LOT08 — Facad Ricketts 32F compatibility disposition — MERGED / POST-MERGE CLOSEOUT PENDING

- Repository: `hraaaaf/Digital_crown`
- PR: `#775` — MERGED / CLOSED
- Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`
- exact evidence HEAD before docs closeout: `575fc9e2ad21133763bdacbe512e7591a39b9f59`
- Facad source: official 3.14.1.1111 `Ricketts (32 F).cph`
- pinned profile SHA-256: `d0b442b39ac7db3dc9c46d807cb3c20bd937c69783b096b484872017f9376518`
- originally unmapped compatibility rows: **26**
- explicitly dispositioned compatibility rows: **26/26**
- remaining `unmapped`: **0**
- important boundary: **26/26 dispositioned does not mean 26 runtime aliases**. Vendor variants, landmark-authority differences, signed/presentation parity gates and non-authoritative Facad norms remain fail-closed.
- final targeted workflow: `Facad Ricketts 32F final seven contract #2` — **SUCCESS** on `575fc9e...`
- explicit adversarial review A (science/provenance): **15/15 PASS**, 0 BLOCKER / 0 MAJOR
- explicit adversarial review B (CI/reproducibility): **14/14 PASS**, 0 BLOCKER / 0 MAJOR
- additional confirmation pass: **10/10 PASS**
- final Perfection Pass: **16/16 PASS**
- final scores on evidence HEAD: EXECUTION **9.4/10**, ADVERSARIAL **9.4/10**, RETAINED **9.4/10**
- no frontend product delta; no clinical runtime activation in the final compatibility-disposition clusters
- Vercel: **NOT AUTHORIZED / NOT USED**
- merge commit: `c7209e9d35f0a85a12ee1725589bca2863aa6607` — **MERGED**

Canonical closeout source:
- `docs/handovers/2026-10-07-ricketts32-compatibility-closeout.md`

**Next exact:** merge the docs-only post-merge reconciliation PR after its exact-head documentary checks are green; then perform a read-only master coherence check and mark the LOT08 Ricketts 32F compatibility closeout fully closed.

# Etat canonique manuel - 2026-10-01

## V1.5-01 — Cabinet topology & workstation roles — CLOSED

- PR topology/workstation harness: #734 — MERGED
- merge commit #734: `a37367dcc3283ef2cb89fd79f736b387171ed89d`
- follow-up deterministic Honoraires harness: PR #738 — MERGED
- exact candidate head #738: `5de868634a2335bce13a306b70124a58d33f99d9`
- final merge commit: `b7c6d25b99e1de2b5a8e937f0909ba02b040f99e`
- T2 PR certification #5948 / run `36894203496`: **SUCCESS** end-to-end
- PR CI #7129 / run `36894203439`: **SUCCESS**
- post-merge master CI #7132 / run `36912825476`: **SUCCESS**
- post-merge Cabinet Upgrade PostgreSQL #1091 / run `36912825240`: **SUCCESS**
- deterministic Honoraires period: fixed September 2026 fixture + explicit Accounting UI period selection; no UTC/local month rollover dependency
- WorkstationModeGate/auth: unchanged by the hardening follow-up
- production runtime: unchanged by PR #738
- double-check internal review: **9.7/10**
- triple-check adversarial internal review: **9.6/10**
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

**Next exact:** open **V1.5-02 — Patient Identity & Photo**.

# Etat canonique manuel - 2026-09-30

## V1.5-00 — Hub & Dispatcher — CLOSED

- PR closeout: #724 — MERGED
- merge commit: `2f0fdeb4583e633e479627a275d7da2d6bc1375e`
- exact candidate head: `f406ae767f2585e468a15cbc65ce5d106573e9f1`
- targeted Hub/Gate/Station/Admin tests: **17/17 PASS**
- Hub Visual Proof run `36788607154`: **SUCCESS**
- Human Visual Approval run `36790450196`: **SUCCESS**
- double-check exact-head: **9.3/10**
- triple-check adversarial exact-head: **9.0/10**
- post-merge code identity: the four touched Hub/Gate runtime+test blobs are byte-identical between candidate HEAD and merge commit
- V1.5-00 residual gap closed: Control Center remains fail-soft as a local recovery surface while clinical routes remain fail-closed; Station remains restrictive
- CI doctrine: only directly impacted tests/builds/workflows are proof-relevant; broad unrelated frontend/browser matrices are not rerun or treated as blockers unless a transverse dependency or invariant requires it
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

**Next exact after closeout docs merge:** open **V1.5-01 — Cabinet topology & workstation roles**.

# Etat canonique manuel - 2026-09-29

## V1 — CLOSED / V1_OPERATIONAL

- Repository: `hraaaaf/Digital_crown`
- V1-08 initial freeze: **CLOSED** - `3c86e72bf0e132e6f79bc336d4ff9eb121d08fab`
- V1-09 installability: **CLOSED / INSTALLABLE_CERTIFIED**
- V1-10 real cabinet activation: **CLOSED / VERIFIED**
- Final certified/installed V1 SHA: `bce60b26059054ba43cf8ec13cd210098e648ea4`
- Installed release: `dc-cabinet-bce60b260590-run36628947897`
- `INSTALLABLE_CERTIFIED`: **OUI**
- `V1_OPERATIONAL`: **OUI**
- Evidence-carrying master before docs closeout: `6966ebf2656f78dd6674d435bc806bd659248d0f`
- Master CI `36638379136`: **SUCCESS**
- PostgreSQL certification `36638379156`: **SUCCESS**
- Live cabinet: health/db/storage HTTP 200; normal launcher restart OK
- Preservation: 434/434 document archives and 2915 media files; integrity PASS
- Rollback: fresh encrypted DB/media backup retained; isolated historical rollback rehearsal documented
- Limitation: V1-10 does not claim comparative visual UX certification
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

## Continuite

V1 is **CLOSED** and operational on the real cabinet. No V1 execution lot remains. After this final canonical documentation closeout is merged and re-read on `master`, execution authority transfers to the canonical POST-V1 / V1.5 roadmap. Next exact: **V1.5-00 — Hub & Dispatcher**.

# Historique canonique — 2026-08-14

## Baseline vérifiée

- Repository : `hraaaaf/Digital_crown`
- `master` après merge P0-6 : `412ab81cc5c47b7220865881f83836b539458a69`
- PR P0-6 : `#12` — MERGED
- Head candidat P0-6 certifié : `8dfe6bcfd866f62a1b41aca08554246411ad67e4`
- CI P0-6 : run `31810762297` — SUCCESS
- Backend tests/durcissement : **SUCCESS**
- Frontend tests/build : **SUCCESS**
- Garde production négative : **SUCCESS**

## Doctrine produit confirmée

- Application **on-premise / local-first**.
- Firebase : identité/licence, jamais source de vérité des dossiers patients.
- Architecture courante : modèles locaux + moteurs déterministes ; aucun LLM requis.
- Donnée patient requise mais absente = inconnue/non-évaluable ; jamais inventée.
- `tests green != validation scientifique`.
- Dans ce projet, `review` signifie par défaut **double-check complet par l’agent**, sauf demande explicite d’un reviewer externe.

## P0 — Safety & Integrity — CLOSED ✅

### P0-1 — PRESCRIPTION-MISSING-DATA-FAIL-CLOSED — CLOSED ✅

Objectif : empêcher toute valeur patient synthétique/estimée de déclencher un calcul patient-spécifique lorsqu’une donnée requise manque.

Implémentation intégrée :
- garde backend explicite `evaluable/non_evaluable` ;
- âge absent reste `None` ;
- poids absent n’est jamais synthétisé ;
- antécédents absents restent explicitement incomplets ;
- enfant sans contexte sûr ne passe pas dans le chemin pédiatrique legacy ;
- plan non évaluable = zéro ligne automatique ;
- `PrescriptionGuideModal` exige un poids explicite pour l’automatisme pédiatrique ;
- `estimateWeightFromAge()` est neutralisé ;
- top-level `assessment.age` est masqué lorsque le contexte n’est pas évaluable ;
- tests backend/frontend missing-data ajoutés.

Double-check final avant merge :
- restauration de tests `clinical_rules_engine` + `habits_engine` supprimés accidentellement ;
- test honoraires rendu déterministe, sans assertion permissive `409 ou 422` ;
- diff final : 16 fichiers, aucun fichier parasite ;
- couverture backend finale : **2459 passed, 7 skipped, 0 failed**.

Limite explicite :
- ce lot **ne valide pas scientifiquement** les constantes thérapeutiques/doses historiques du moteur legacy ;
- ces constantes restent une dette scientifique distincte.

Dette CI non bloquante :
- la CI force `httpx==0.27.2` pour compatibilité Starlette/TestClient ;
- cela entre en conflit déclaré avec `firebase-admin 7.5.0` et `ultralytics-platform 0.1.4`, qui demandent `httpx>=0.28` ;
- correction durable à traiter séparément : upgrade FastAPI/Starlette ou isolation des dépendances de test.

### P0-2 — CMO-NON-PRESCRIPTIVE-BOUNDARY — CLOSED ✅

Objectif : empêcher la synthèse CMO de transformer des mentions textuelles documentaires en diagnostic, pronostic ou décision thérapeutique autonome.

Implémentation intégrée :
- synthèse CMO convertie en signaux documentaires uniquement ;
- conservation des clés de réponse historiques nécessaires à la compatibilité ;
- ajout explicite de `evidence`, `uncertainty`, `practitioner_validation_required=True` et `automation_scope="signal_only"` ;
- pronostic autonome neutralisé en `Non déterminé automatiquement` ;
- aucune décision automatique d'initier, reporter ou modifier un traitement orthodontique ;
- mémoire Ghost CMO reclassée en `SIGNAL_CLINIQUE` ;
- tests ciblés couvrant les signaux textuels et le cas de texte négatif traité comme mention à valider, jamais comme diagnostic.

Certification :
- PR `#6` — MERGED ;
- head candidat certifié : `84c14bb54068d21a9d7c668b5d041fdac7d93e01` ;
- CI : run `31758201657` — SUCCESS ;
- backend : **2462 passed, 7 skipped, 4 warnings, 0 failed** ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `6def2a2501cd687f5fa9be03741206b77b02643f`.

Limite explicite :
- la détection reste lexicale et peut relever une mention négative ou hors contexte ; elle est exposée comme **signal incertain à valider**, jamais comme conclusion clinique.

### P0-3 — SQLCIPHER-FAIL-CLOSED — CLOSED ✅

Objectif : empêcher un cabinet on-premise configuré sur SQLite disque de démarrer en clair si SQLCipher est indisponible ou si la migration de chiffrement échoue.

Implémentation intégrée :
- `ENVIRONMENT=cabinet` + SQLite disque impose désormais SQLCipher ;
- driver `sqlcipher3` absent = `RuntimeError` bloquant avant ouverture d'une SQLite non chiffrée ;
- migration plaintext → SQLCipher échouée = restauration du fichier d'origine puis démarrage refusé ;
- `development` et SQLite `:memory:` restent compatibles avec la CI/tests ;
- tests subprocess forcent l'absence de `sqlcipher3`, couvrent le refus de démarrage, la restauration du fichier plaintext et la non-régression development.

Certification :
- PR `#8` — MERGED ;
- head candidat certifié : `bf01fc9b66848c64ba159924ceb900da90d886fe` ;
- CI : run `31785414095` — SUCCESS ;
- backend : **2465 passed, 7 skipped, 4 warnings, 0 failed** ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `c4adedb6528d586e3a8ec8fa5c52e33069cfb9f3`.

### P0-4 — PARTIAL-PAYMENT-NO-INFERENCE — CLOSED ✅

Objectif : empêcher `documents/generate` de créer un véritable `Payment` partiel à partir d'un montant inventé lorsque le contrat ne transporte aucun montant encaissé explicite.

Implémentation intégrée :
- `DocumentRequest` refuse `payment_status=PARTIEL` sans montant encaissé explicite ;
- le flux dédié `/accounting/payments` reste le chemin autorisé pour un paiement partiel car `PaymentCreate.amount` y est obligatoire ;
- `EN_ATTENTE` et `PAYE` restent valides ;
- tests dédiés couvrent le refus fail-closed et l'absence d'écriture partielle inférée ;
- le test financier legacy a été réaligné sur `PAYE` afin de ne plus codifier l'ancien comportement dangereux.

Certification :
- PR `#9` — MERGED ;
- head candidat certifié : `7e5066d1dd53abfde33ad5e8043cd1c5d14c4d37` ;
- CI : run `31805059079` — SUCCESS ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `a99025d67a5470219369c633570a617e19f6f557`.

Limite UX connue :
- le bouton `PARTIEL` du Document Studio reste fail-closed jusqu'à ajout d'un vrai champ montant encaissé ; aucune valeur financière ne doit être devinée entre-temps.

### P0-5 — PRESCRIPTION-SAFETY-TENANT-GUARD — CLOSED ✅

Objectif : empêcher `POST /api/prescriptions/safety/check` de lire ou évaluer un patient hors tenant avant l'appel au service clinique.

Implémentation intégrée :
- `assert_patient_access(patient_id, current_user, db)` s'exécute avant `prescription_service.check_safety(...)` ;
- un patient d'un autre tenant produit `403 Accès refusé` ;
- le service de sécurité n'est jamais appelé pour ce patient ;
- test cross-tenant dédié ajouté.

Certification :
- PR `#11` — MERGED ;
- head candidat certifié : `d579750ce5897f86e902cf70b4e5003d188f1762` ;
- CI : run `31807332356` — SUCCESS ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `67dc6620f5667ad4060592ef5662379fc720b6f9`.

### P0-6 — PREVIEW-MUST-BE-READ-ONLY — CLOSED ✅

Objectif : garantir qu'une preview documentaire ne persiste aucun état comptable ou archive en base.

Implémentation intégrée :
- les previews d'échéancier à données directes utilisent `flush()` puis `rollback()` au lieu de commits durables ;
- `DocumentFactory.create_installment_plan(..., archive=False)` désactive la création de `DocumentArchive` en preview ;
- le chemin preview avec `plan_id` existant désactive lui aussi l'archivage ;
- le log d'audit `GENERATE` n'est pas persisté en preview ;
- `DocumentRequest` accepte explicitement `echeancier`, alignant le contrat avec le routeur ;
- test dédié vérifie que `InstallmentPlan`, `Installment` et `AuditLog` restent inchangés et que la factory reçoit `archive=False`.

Certification :
- PR `#12` — MERGED ;
- head candidat certifié : `8dfe6bcfd866f62a1b41aca08554246411ad67e4` ;
- CI : run `31810762297` — SUCCESS ;
- backend tests/durcissement, frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `412ab81cc5c47b7220865881f83836b539458a69`.

## P1 — Hardening — ACTIVE

### P1-1 — NATIVE-SECURE-STORAGE — CLOSED ✅ (N/A runtime courant)

Constat vérifié : le client actuel est une PWA React/Vite et le dépôt ne contient aucun runtime natif Capacitor/Tauri/Electron ni dépendance Keychain/Keystore/SecureStore à câbler.

Décision :
- ne pas introduire un wrapper natif artificiel uniquement pour satisfaire la roadmap ;
- le runtime web courant ne doit pas persister de bearer secret longue durée dans `localStorage`, `sessionStorage` ou IndexedDB ;
- tout futur client natif devra stocker les credentials longue durée exclusivement dans le Keychain/Keystore du système.

### P1-2 — MOBILE-CREDENTIAL-LIFETIME-REVOCATION — ACTIVE

Objectif : réduire l'exposition des credentials mobiles longue durée et vérifier une révocation réellement fail-closed.

Constats initiaux :
- le flux mobile/ZKA émet actuellement un bearer JWT avec une durée de vie de 365 jours ;
- une infrastructure `jti`/blacklist existe déjà et doit être conservée puis testée, pas réinventée ;
- le flux de claim one-shot doit être vérifié pour ne pas consommer définitivement le token avant validation complète du handshake.

### P1-3 — CABINET-SETTINGS-STRICT-WHITELIST

Whitelist Pydantic stricte pour les paramètres cabinet ; pas de mass assignment générique.

### P1-4 — PATIENT-SCOPED-TENANT-AUDIT

Audit tenant exhaustif des routes patient-scopées.

### P1-5 — UPLOAD-MIME-MAGIC-BYTES

MIME + magic bytes systématiques sur uploads sensibles.

### P1-6 — FRONTEND-HASACCESS-CENTRALIZATION

Centraliser `hasAccess()` frontend.

### P1-7 — LEGACY-ENGINE-QUARANTINE

Quarantainer/supprimer les anciens moteurs non utilisés.

## P2 — Certification

- CI sur le head réellement candidat.
- Backend + frontend + build.
- Smoke live/rehearsal ciblé selon le risque.
- Audit visuel 390 / 768 / 1280 pour les lots UI concernés.
- Accessibilité clavier/ARIA sur contrôles custom.
- Validation scientifique céphalométrique source par source avant toute revendication autoritative.

## Skills scientifiques applicables

- `.claude/skills/audit-prescription-flow/SKILL.md`
- `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md`
- `.claude/skills/audit-panoramic-report-pipeline/SKILL.md`
- `.claude/skills/validate-cephalo-pipeline/SKILL.md`
- `.claude/rules/scientific-engineering.md`

## Lot actif

### LOT P1-2 — MOBILE CREDENTIAL LIFETIME + REVOCATION — ACTIVE

---

## Document Studio — chantier actif — 2026-08-15

Roadmap canonique : `DOCUMENT_STUDIO_ROADMAP.md`.

### R1 — P0 Cohérence médicament / Maroc-first — CLOSED ✅
- PR `#17` — MERGED.
- Head certifié : `8063b11b061ea6d1912e1b4e1a0ab8ef1fcb649a`.
- CI : run `31852032393` — SUCCESS.
- Merge : `e32ab311f72980e0797b93a306c3616a4ff66042`.

### R2 — P0 Persistance protocoles/habitudes — CLOSED ✅
- PR `#19` — MERGED.
- Head certifié : `ba66457e5f65917f71670e151826062442525200`.
- CI : run `31852827218` — SUCCESS.
- Merge : `432a95eca05d1d7b9781d2d8e81077f0dcb589f2`.

### R3 — P0 Safety orchestration — CLOSED ✅
- PR `#20` — MERGED.
- Head certifié : `becadcafb4ba0e6a5f4fda10a0053bb92c96fe1e`.
- CI : run `31853962025` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `75e4693dc983ba1708914d16432504bea8f0cd8c`.
- Le Studio n'affiche plus d'état safety vérifié avant succès réel du backend ; états explicites `unchecked/checking/verified/error`.
- Dette R3 non bloquante : appel safety read-only parallèle encore présent dans `DocumentHub`, à dédupliquer lors du prochain lot pertinent.
- Aucune certification clinique/scientifique humaine revendiquée.

### R4 — P0 Dirty-state & actions — CLOSED ✅
- PR `#21` — MERGED.
- Head certifié : `cdaf28874bc9155d115108bba7548470300c5ca1`.
- CI : run `31855874418` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `6a4debe01cf0e0ea78e49ed787cae5e26c4976b8`.
- Dirty-state dérivé du fingerprint ordonnance complet ; garde onglet/navigateur ; reset après archivage ; actualisation contexte explicite.
- Le fallback source `forme: d.forme || 'Sachets'` existe encore dans le legacy, mais son effet caché est neutralisé à la frontière transport et la forme manquante est explicitée dans l’UI.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R5 — P1 Fast Prescription UX — CLOSED ✅
- PR `#22` — MERGED.
- Head certifié : `6de453962668e66be9e26978ec07fc9082afacb7`.
- CI : run `31878337816` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `8957635e1bd50d8f44fbcef38c529b3c27f8fb32`.
- Quick-picks praticien issus des habitudes réelles : récents + fréquents. Aucun favori étoilé explicite inventé.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R6 — P1 Protocoles + Référentiel — CLOSED ✅
- PR `#23` — MERGED.
- Head certifié : `10751078601c3aa5be728bc263e25a58e856c676`.
- CI : run `31879112143` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `6f2b8a22f9cdca25cafe228f266ed46deee8281b`.
- Référentiel search-first, ajout manuel replié, contexte âge/poids visible, `Mes protocoles` réversible après masquage.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R7 — P1 Contexte + Preview premium — CLOSED ✅
- PR finale `#26` — MERGED.
- Head certifié : `9a39ecc4d415e59c5457a58638a48ba0c22f81fd`.
- CI : run `31879649826` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `2596da527fdd1bee5c6746f645e995f682ca3189`.
- PR intermédiaires `#24` et `#25` fermées sans merge car remplacées par le candidat consolidé sur baseline post-R6.
- Contexte patient et preview utilisent une terminologie déterministe ; preview responsive ; test backend prouve qu’une ordonnance `preview=true&archive=true` ne crée ni archive, ni audit, ni paiement, ni acte.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### P1 Ordonnance — ENGINEERING CLOSED ✅
- R1→R7 fermés et fusionnés.
- Roadmap canonique synchronisée.
- Interaction runtime et recertification UX/clinique restent des gates séparés et ne sont pas revendiqués.

### P2 Devis + Honoraires — ACTIVE 🟡
- Audit canonique : `docs/audits/DOCUMENT_STUDIO_P2_DEVIS_HONORAIRES_AUDIT.md`.

#### P2-A — Prix catalogue local conservé — CLOSED ✅
- PR `#27` — MERGED.
- Head certifié : `7289d0bf64c8139838470923622f8c0b588206e1`.
- CI : run `31882328096` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `a8ce1f8143fd58f20aee5cb4ebb9b8827128c4cc`.
- Le wrapper répare uniquement les suggestions locales dont le prix catalogue existe ; aucun prix absent n’est inventé.

#### P2-B — PARTIEL fail-closed cohérent UI/backend — CLOSED ✅
- PR `#29` — MERGED.
- Head certifié : `d60a99c290e0e27c84d73fb95d947fa111461f7a`.
- CI finale : run `31884437013` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `6543c3dad146bdbe055117fe0302b3fbe9cbda07`.
- Premier head `1005f2281868f435b8fb2f56066bc920b3151df5` : frontend/build + garde production verts, backend rouge uniquement parce qu’un `ValueError` Pydantic restait non sérialisable dans le contexte du handler JSON ; corrigé avec `PydanticCustomError`.
- `PARTIEL` ne peut plus devenir l’état du document dans ce flux ; aucun montant partiel n’est inféré.
- `PaymentCreate.amount` est strictement positif et les méthodes connues sont normalisées explicitement.

#### P2-E — Échéances/réconciliation financière exacte — ACTIVE 🟡
- Défaut confirmé : Honoraires global peut créer un plan dont la somme des échéances diffère du total facturé.
- Préparation P2-E : réconciliation exacte au centime frontend/backend + tests ; PR draft `#30` 3/3 verte sur ancienne baseline.
- #30 ne doit pas être mergée : reconstruction obligatoire sur baseline post-P2-B.

#### P2-F — Allocation PAYE exacte par Acte — PREPARED
- Défaut confirmé : Honoraires PAYE crée des Acte marqués PAYE mais un Payment global sans `acte_id`, ce qui peut diverger de la vue `actes-billing`.
- Helper/test d’allocation exacte préparés sur PR draft `#31`; intégration route à faire après P2-E.

#### Préparation UX suivante
- P2-C : quick actions tactiles + phases déterministes sans durée clinique estimée, PR draft `#32`.
- P2-D : handler legacy de déduplication odontogramme confirmé orphelin ; policy `dent::traitement`, PR draft `#33`.

#### Pré-audits isolés pendant les CI
- P3 : `work-20260815-p3-static-audit` — non fusionné.
- P4 : `work-20260815-p4-static-audit` — non fusionné.
- P5 : `work-20260815-p5-static-audit` — non fusionné.
- P6 : `work-20260815-p6-static-audit` — non fusionné.

#### P5-P0 clinique découvert — NON CORRIGÉ 🔴
- `HouseWizard` est atteignable via `Mode Expert`.
- `DiagnosticEngine` produit diagnostic/protocole/plan de traitement et substitue actuellement automatiquement des classes thérapeutiques à partir d’une détection textuelle d’allergie.
- Exemple source vérifié : pénicilline → remplacement `AMOXICILLINE` par `CLINDAMYCINE/MACROLIDE`; AINS → remplacement par `CORTICOSTÉROÏDES`.
- `Appliquer` transforme le résultat en insight `DETERMINISTIC` et positionne le score d’intelligence à 100 ; il ne persiste pas directement le treatment plan dans la DB au point inspecté.
- Branche de sécurité `work-20260815-p5p0-no-auto-substitution` : test de frontière ajouté, correctif applicatif non encore fusionné.
- Priorité : aucune substitution thérapeutique automatique ; exposer une alerte à validation praticien.

Aucune certification financière production, UX runtime ou clinique/scientifique humaine n’est revendiquée pour les lots actifs/pré-audits.
