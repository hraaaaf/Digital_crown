# STATE — DigitalCrown

> Fichier de reprise canonique. Historique pré-audit : `docs/archive/STATE_2026-07-21.md`.

# État canonique manuel — 2026-08-14

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
