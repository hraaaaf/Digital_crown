# DIGITAL CROWN — CEPH-BILAN-A4-SIGNATURE-01 — contrat PRE (12 novembre 2026)

**Décision unique — GO de préparation, PAS de GO clinique :** autoriser un **compte rendu céphalométrique descriptif A4** revu et attesté par le praticien, indépendant de R11–R14 (diagnostic, objectifs, options, stratégie). Ne pas lever `clinical_validation_available=false` et ne jamais transformer automatiquement une mesure en diagnostic.

**Statut de ce fichier :** SPECIFICATION / PRE, pas une implémentation ni une certification. Une nouvelle PR applicative et des preuves exact-HEAD seront nécessaires avant toute activation. La publication, migration critique, fusion, et introduction de patients réels exigent leurs gates séparés.

## 1. Contexte démontré au HEAD de départ

- Origine de cette branche documentaire : PR [#1316](https://github.com/hraaaaf/Digital_crown/pull/1316), HEAD `280779b75a88795dbe92b8b94fc284c74722028d`. Calibration fonctionnelle synthétique avec vrai HTTP/SQLite/GUI : [Actions #43201754713](https://github.com/hraaaaf/Digital_crown/actions/runs/43201754713), SUCCESS, 17 tests auto + 14 tests calibration manuelle/HTTP, artefact #13934909674. Cela ne prouve ni précision sur images réelles ni validité clinique.
- `backend/services/cephalo_r15_clinical_studio.py` maintient `clinical_validation_available=false` parce que le R14 autoritaire n'est pas prêt. Le bilan descriptif ne doit pas contourner ce garde.
- `backend/services/cephalo_pdf_projection.py` exige la chaîne typée et la révision ; `backend/services/generators/cephalo_four_part_report.py` rend explicitement « BROUILLON — NON SIGNÉ » et peut présenter des diagnostics/plans sourcés : **ce renderer multi-parties ne doit pas être renommé « signé » par simple changement de texte**.
- `backend/routers/patients.py` : `POST /api/patients/{patient_id}/pdf` accepte un brouillon `archive=false`, refuse un **nouvel** archivage officiel `archive=true` sans signature du PDF exact, tout en préservant le replay d'anciens rapports intègres.
- `backend/services/cephalo_document_lock.py` possède déjà un verrou de l'étude, une vérification d'identité/révision, un replay idempotent et la relecture des octets d'archive sous SHA-256. `models.DocumentArchive` fournit `patient_id`, `analysis_id`, `uploaded_by_id`, `file_hash`, `file_size`, `clinical_data`, statut et version. Réutiliser les invariants éprouvés, sans supposer que ces champs constituent déjà une signature.
- `frontend/src/features/ortho/components/Step4Documents.tsx` offre « Brouillon PDF » et désactive volontairement l'archivage officiel.

## 2. Périmètre / hors périmètre

**IN :** rapport strictement descriptif de l'étude sélectionnée, mesures et unités issues de la lecture backend typée, échelle auto vérifiée ou manuelle admissible, points/mesures corrigés par le praticien avec provenance, notes descriptives clairement attribuées à leur auteur ; revue explicite de la version exacte ; attestation interne du praticien ; archivage immuable et lecture ultérieure contrôlée.

**OUT :** validation R14, diagnostic automatique, classification normative non validée, sélection d'option thérapeutique, prescription ou plan de traitement, activation des six protocoles Ricketts en HOLD, sortie de données patient du poste, LLM runtime, signature qualifiée légalement reconnue **sans étude juridique et mécanisme distinct**. Les anciens rapports officiels restent accessibles suivant leurs gardes, sans être implicitement « re-signés ».

## 3. Invariants de sécurité (fail closed)

1. Le serveur seul calcule l'identité `cabinet/tenant + patient_id + analysis_id + revision scientifique + source image + calibration/evidence graph`; aucune identité, rôle, statut signé ou révision finale ne vient d'un champ contrôlé par le client.
2. Un utilisateur autorisé à lire un dossier n'est pas automatiquement habilité à signer. Exiger l'identité du praticien authentifié, rôle/permission explicite, session et poste autorisé ; interdire la signature par mandataire, superadmin générique ou tenant voisin sans règle prouvée.
3. La calibration **admissible et persistée** est obligatoire pour afficher des distances linéaires en mm. Échelle absente, altérée, ratio aberrant, provenance invalide ou graphe typé incohérent => pas de signature ; les mesures angulaires ne deviennent pas diagnostic.
4. Les notes signables sont descriptives et persistées à une révision/version indépendante. Exclure du contenu final toute clé libre `ai_diagnostic`, `clinical_data` legacy non attestée, et objets R11–R14 non validés. Un texte saisi par le praticien est attribué au praticien, jamais « déduit » par l'IA.
5. Préparer **les octets finaux exacts** du PDF (mise en page A4, métadonnées stables), calculer SHA-256 côté backend et présenter au praticien la même version. L'attestation lie l'empreinte de CES octets, la révision, les sources, le dossier, l'identité et l'horodatage backend. **Ne pas altérer le PDF après attestation** ; si la mise en page change, recommencer la revue et générer une autre empreinte.
6. Une attestation applicative + SHA-256 prouve la liaison au contenu dans la base locale ; elle ne doit PAS être vendue comme signature électronique qualifiée ni comme signature PDF PAdES tant qu'aucune signature cryptographique vérifiable par un tiers n'est réellement implémentée et testée. Afficher « bilan descriptif attesté par le praticien » plutôt que « signature qualifiée ».
7. À la validation, relire sous verrou/CAS l'identité patient, l'empreinte de la source, les révisions graphe, calibration et notes. Si un point, une calibration, un texte, un autorisé ou une source a changé depuis la prévisualisation, HTTP 409 sans archive et sans signature.
8. Un clic répété avec **la même identité + révision + empreinte** restitue exactement la même archive ; une collision, une autre empreinte à révision égale ou deux signataires concurrents => 409 sans duplication. L'ancienne archive reste vérifiable et datée, pas réécrite ; toute révision ultérieure est un nouvel acte et ne modifie pas l'ancien document.
9. Conserver et étendre le protocole transaction/fichier/journal de récupération existant : PDF temporaire, empreinte, persistance journal + DB, publication atomique si possible, rollback et nettoyage vérifiables en cas d'erreur. Ne jamais exposer de chemin libre, de fichier patient au navigateur non authentifié, ni de lecture différée TOCTOU après la vérification SHA.
10. Préserver les refus de la route générique `documents/archive` pour `RAPPORT_CEPHALO` ; seule une route clinique dédiée pourra créer un document officiel après preuve. Ne pas substituer `archive=true` à une signature.

## 4. Parcours proposé (deux actes explicites)

- **A / Préparer** : étude et révision explicites ; relecture chaîne et mesures descriptives ; capture des notes validées et de l'identité source ; génération du PDF A4 candidat sans statut d'archive ; empreinte calculée ; aperçu exact affiché avec les avertissements et les champs indispensables. L'UI indique « Non signé » tant que l'attestation n'existe pas.
- **B / Attester et archiver** : bouton distinct activable seulement si tous les contrôles descriptifs passent ; action consciente du praticien sur le PDF exact ; relecture serveur des révisions et du hash ; création d'un reçu signé interne séparé de R14, lié à un document permanent et audité ; lecture après archivage en reprenant les octets SHA-vérifiés. Le statut de signature dépend du reçu serveur, **jamais** d'un badge frontend ou du texte du PDF.
- **C / Relecture** : vérifier identité/permission + reçu + empreinte + chemin autorisé avant de servir les octets. Toute altération => erreur explicite, aucun affichage « officiel ». Les modifications ultérieures du cas ouvrent une nouvelle version, elles n'effacent pas l'historique de l'acte précédent.

## 5. Modèle de preuve à étudier avant écriture médicale

`descriptive_document_attestation_v1` (contrat candidat, PAS un schéma existant) : `tenant_id`, `patient_id`, `analysis_id`, `scientific_revision`, `evidence_graph_hash`, `calibration_provenance_hash`, `clinician_notes_revision/hash`, `signer_user_id` (auth backend), `signed_at_utc`, `pdf_sha256`, `pdf_length`, `archive_id`, `attestation_id`, `attestation_kind=INTERNAL_DESCRIPTIVE`, `supersedes` (optionnel), `audit_event_id`. Une modification de schéma ou migration clinique n'est **pas** autorisée par ce contrat documentaire ; vérifier d'abord si une conservation sûre est possible dans les structures actuelles.

## 6. Tests obligatoires sur données 100 % synthétiques

**Cas acceptés :** preuve de calibration auto admissible et manuelle avec source typée ; mesures en mm recalculées avec origine claire ; PDF A4 exact, non-signé avant attestation, attestation post-confirmation, lecture SHA identique ; deux viewports cabinet (1280×900 et 1600×1000), puis 390×844 pour l'action ; archive après redémarrage et restauration de sauvegarde isolée ; double clic identique => même ID/empreinte, zéro double ligne.

**Refus :** étude non calibrée, evidence graph absent/legacy, ratio non admissible, source patient non concordante, autre tenant, acteur non dentiste, session expirée/non enrôlée, notes modifiées, révision N→N+1 entre aperçu/signature, recalibration concurrente, falsification de PDF ou réception, hash incohérent, signature sur document d'autrui, deux demandes de signatures avec hash différents, filesystem read-only/écriture incomplète, recovery journal en conflit, lecture du mauvais blob, tentative d'injecter diagnostic ou plan.

**Observabilité :** aucune donnée patient réelle dans logs/PR/artifacts, secrets non exposés, séquence événements source → aperçu → confirmation → archive → relecture horodatée, échec 4xx/409 explicite sans écriture partielle. Vérification indépendante SQLite du reçu et du fichier + seconde revue sur les risques signature/archivage avant toute activation.

## 7. Plan d'exécution et gates

- **S0 — PRÉPARATION (ce document) :** décider le périmètre documentaire, inventorier le code et écrire contrat/test plan ; aucun code runtime ni migration.
- **S1 — Test-first en PR applicative DRAFT isolée :** définir API et objets d'attestation, tests négatifs de droits/provenance/concurrence et preuve PDF SHA. Démarrer rouge sur les assertions manquantes sans manipuler de vrais patients.
- **S2 — Backend local-first :** implémenter receipt et transaction d'archive vérifiée avec sauvegarde/restauration. Si un schéma nouveau est nécessaire, **HUMAN GATE migration** avant application.
- **S3 — UI Step 4 :** BEFORE/AFTER à états identiques, afficher explicitement résumé, origine, relecture du PDF exact, signature/archivage et refus ; aucune manipulation R11–R14.
- **S4 — PREUVE :** CI exact HEAD, vrais appels HTTP authentifiés, base SQLite/SQLCipher isolée, cas de conflit et redémarrage, artifact PDF synthétique SHA, comparaison visuelle, évaluation des droits ; validation praticien distincte, pas de release clinique implicite.
- **S5 — INTEGRATION (non autorisée dans ce lot préparatoire) :** revue indépendante de sécurité + autorisation explicite du praticien avant merge/installation. Aucun Vercel.

## 8. Critères de clôture

Le lot **CEPH-BILAN-A4-SIGNATURE-01** ne sera « VERIFIED » que lorsque (1) un praticien autorisé peut revoir les octets exacts d'un A4 descriptif, (2) un reçu immuable prouve l'attestation interne de ces octets et des révisions dans une DB locale, (3) l'archive est relue avec preuve SHA et droits effectifs, (4) refus/race/recovery ont été testés, (5) le pipeline diagnostic/traitement demeure bloqué et (6) les preuves GitHub + UI + backup sont attachées au HEAD final. **La présence du présent document ne valide aucun de ces critères.**

**Next exact :** audit des contrats persistants de signatures/archivage existants et définition des tests S1 ; arrêt si migration/stratégie légale ou données patient deviennent indispensables. **Fichier canonique de ce nouveau lot : ce document.**

## 9. S1 — découverte et choix de réutilisation P3 (12 novembre 2026)

**Constat corrigé par lecture du code :** Digital Crown possède **déjà** un socle applicatif P3 pour les documents génériques :
- `backend/services/document_signature_p3.py` : `sign_document`, `verify_document_integrity`, `verification_state_for_document` ; auteur actif contrôlé, signer = auteur, SHA-256 et taille des octets archivés, horodatage et idempotence simple ; **pas une signature cryptographique qualifiée**.
- `backend/routers/document_provenance_p3.py` : `POST /api/documents/{document_id}/sign`, autorisation patient + type de document + utilisateur ; façade de provenance pour `POST /api/patients/{patient_id}/pdf`.
- `backend/models_document_provenance_p3.py` : colonnes existantes `author_practitioner_id`, `signed_by_practitioner_id`, `signed_at`, migration P3 déjà définie et attestations génériques existantes ; **aucune nouvelle migration ne doit être lancée dans S1**.
- `backend/tests/test_document_signature_p3.py` : tests génériques déjà présents pour les signatures ordinaires, refus et octets altérés.

**Différence critique :** P3 signe un **DocumentArchive existant** mais ne vérifie pas, dans `sign_document`, un reçu de relecture du PDF céphalo exact, les révisions du graphe/notes/calibration, ni l'exclusion des champs thérapeutiques libres. Le verrou Céphalo sur la **création** d'une nouvelle archive A4 non signée demeure en place. Le test S1 couvre le risque d'une ancienne archive Céphalo ou d'un futur mauvais câblage du flux P3 ; ne pas prétendre qu'un nouvel archivage officiel est aujourd'hui possible.

**S1 test-first :** `backend/tests/test_ceph_a4_descriptive_attestation_s1.py` contient quatre tests positifs de non-régression des mécanismes existants (archivage tenu, signature P3 d'ordonnance, tampering, auteur autre) et cinq exigences de sécurité céphalo **XFAIL(strict)** (absence de reçu, révision périmée, SHA de prévisualisation différent, texte diagnostic/traitement injecté, vérification publique affirmant à tort « signé »). Ils constituent des **critères RED non résolus**, pas une signature céphalo testée. Toute éventuelle tentative d'intégration S2 doit transformer ces cinq contrats en PASS sous contrôle métier, sans `skip` ni `xfail`.

**Choix technique :** étendre **avec un garde céphalo explicite** la chaîne P3 existante, en réutilisant sa vérification de l'intégrité et de l'identité auteur ; ne pas créer un second moteur P3 parallèle, ni assimiler l'acte documentaire au R14. Les primitives à associer à la relecture verrouillée de `CephaloAnalysis` et au digest de contenu/notes doivent être évaluées **avant** toute écriture S2. Préférer un rejet strict pour tout `RAPPORT_CEPHALO` sans reçu exact accepté. Une migration reste une décision humaine séparée.

**GATE S1 :** un pipeline vert contenant `XFAIL` prouve la **traçabilité des trous contractuels**, **PAS** la réussite de la signature ; un `XPASS(strict)` non analysé est un défaut de cohérence du protocole, pas une certification automatique.

## 10. Décision V1 révisée — Aperçu / Imprimer OU Archiver (12 novembre 2026)

**Décision propriétaire :** pas de signature manuscrite, de PAdES ni de signature qualifiée obligatoires dans la V1. La cible de workflow est désormais **Analyse → Correction → Validation explicite du praticien → Aperçu du bilan A4 → Imprimer OU Archiver**, avec le nom et le cachet du praticien autorisé. **Imprimer ne crée aucune archive**. Archiver est un acte distinct et doit conserver les octets exacts du PDF approuvé, son empreinte SHA-256, la révision scientifique, l'auteur, les droits et l'historique.

**Incrément S2A réalisé sur branche isolée (non clinique, non mergé) :**
- Le `handlePrint` de `frontend/src/features/ortho/stores/useOrthoStore.ts` envoyait auparavant `archive:true` : cette confusion impression/archivage est corrigée pour utiliser exclusivement `archive:false`, avec contrôle de l'étude et révision exactes. Le PDF s'ouvre dans une fenêtre locale avec un bouton explicite « Imprimer le PDF ». Aucune écriture `DocumentArchive` ne découle du clic imprimer.
- `Step4Documents.tsx` rend les actions **Prévisualiser / Imprimer / Brouillon PDF / Archivage suspendu** explicites. Le bouton d'archive officiel reste désactivé : le serveur ne possède pas encore la validation descriptive attestée du praticien. Ne pas faire passer ce verrou pour une fonctionnalité complète.
- Le texte de l'UI précise qu'une **approbation traçable** suffira dans le futur flux V1, et qu'aucune signature électronique avancée n'est exigée. Les tests et captures qui s'appuyaient sur le libellé historique sont mis en cohérence sans enlever le refus d'archive.
- Les nouveaux tests `backend/tests/test_ceph_a4_preview_print_archive_v1_contract.py` gardent les invariants print=archive:false, cohérence patient/étude, refus archive tant que validation absente, R14 inchangé.

**Gates encore ouverts :** la validation praticien backend, la production d'un bilan final non-brouillon et l'archivage transactionnel immuable avec preuve PDF sont **NON IMPLÉMENTÉS** dans S2A ; ne jamais les simuler côté frontend. Les cinq XFAIL S1 liés à la signature applicative doivent être revisités selon la nouvelle décision V1, et non activés en aveugle. Réutiliser les champs/transactions P3 lorsque leur sécurité est prouvée, mais ne pas rendre une signature avancée obligatoire.

**Next exact :** vérifier exact-HEAD TypeScript, tests existants et nouveau contrat d'impression ; ensuite définir et implémenter **S2B validation praticien + archivage officiel** comme lot distinct, sous revue de sécurité, sans migration ni activation médicale implicite.

## 11. S2B implémentation candidat V1 — PDF descriptif, approbation et archive locale (12 novembre 2026)

**État :** code candidat dans une PR DRAFT non fusionnée ; ne pas déclarer de succès clinique ni d'archive utilisable avant les tests E2E exact HEAD, revue indépendante, et gate d'intégration.

**Décision explicite maintenue :** le praticien ne doit ni dessiner une signature ni disposer d'un certificat qualifié. Un clic volontaire de validation sur le **PDF exact** après relecture suffit au parcours V1, à condition de conserver la preuve d'identité, la version scientifique, les octets et l'historique. La validation d'un bilan **descriptif** ne débloque jamais le diagnostic/traitement R11–R14.

**Nouvelle API séparée de la route historique bloquée :**
- `POST /api/patients/{patient_id}/cephalo-a4/prepare` avec `analysis_id` et `expected_revision` : authentification `cephalo` + rôle DENTISTE habilité, chaîne typed graph vérifiée, calibration persistée, 38 repères présents, cohérence ; génération d'un A4 descriptif avec nom professionnel + cachet textuel du cabinet configuré. Retour au navigateur en base64 d'un candidat PDF, SHA-256 et reçu HMAC lié à praticien/cabinet/patient/étude/révision/empreinte scientifique et aux octets du PDF, TTL 10 min. Le PDF temporaire généré par le backend est supprimé et aucune ligne DocumentArchive n'est écrite à ce stade.
- `POST /api/patients/{patient_id}/cephalo-a4/archive` exige le même PDF intégral, le reçu HMAC, `approved=true` de façon explicite et le bon utilisateur ; acquiert le verrou SQL par étude, revalide l'étude et son empreinte, refuse toute divergence, archive exactement les octets relus via `ArchiveService`/journal de récupération existant, enregistre `approved_by_practitioner_id`, `approved_at_utc`, `scientific_source_sha256`, `approved_pdf_sha256`, `clinical_diagnosis_validated=false` dans le JSON local déjà disponible, plus auteur P3 et événement d'audit dans la même transaction. Idempotence/replay par identité du PDF et utilisateur. Ce n'est PAS un certificat de signature qualifiée et les champs P3 `signed_*` restent inutilisés.
- `backend/services/generators/cephalo_four_part_report.py` possède désormais un chemin séparé **CEPH_A4_DESCRIPTIVE_APPROVAL_V1** qui supprime entièrement les sections III Diagnostic et IV Traitement ; aucune note IA/historique non approuvée n'est reprise. L'en-tête et le pied de page du cabinet restent les mêmes que pour les autres documents. Un cachet non configuré est indiqué explicitement et non inventé.

**UI Step4 :** chemin clinique complet et bouton legacy « Archivage suspendu » restent bloqués. Un parcours dédié « Préparer l'aperçu A4 à valider » présente le PDF dans une fenêtre de relecture, son identité de version, son empreinte SHA et le cabinet ; un checkbox praticien active « Valider et archiver ce bilan A4 ». L'impression existante est toujours `archive:false`. Le frontend annule tout aperçu en cas de changement patient/étude et refuse les modifications locales avant transmission.

**Preuves exigées (synthétiques uniquement) :** tests unitaires HMAC/falsification/droits/expiration/croisement, HTTP authentifié de préparation/validation et lignes SQLite, contrôle SHA + PDF A4 (ne contient pas diagnostic/plan), refus sans checkbox, tampering, révision scientifique périmée, doublon idempotent, validation refusée par rôle non-dentiste, rejet des archives historiques corrompues, relecture et recovery. Vérifier les trois classes indépendantes CI et le nettoyage des fichiers temporaires, aucune donnée patient réelle.

**Avant closeout :** confirmer disponibilité réelle du nom et du cachet de cabinet (le cachet V1 actuel est **textuel à partir de la configuration**, pas un tampon graphique scanné), revue indépendante du verrou concurrency/token/récupération, sauvegarde et restauration du document, capture BEFORE/AFTER mêmes viewports. Sans ces preuves, S2B reste PRE et aucune activation clinique n'est autorisée. La précédente PR #1321 S2A (Aperçu/Imprimer) était GREEN, mais cela ne constitue pas une certification S2B.

## 12. J5 — revue indépendante S2B (13 novembre 2026)

**GO humain reçu :** revue S2B à risque élevé de concurrence/recovery, sans activation clinique, merge, migration ou déploiement. Cette revue ne constitue pas un test physique (réservé au lot 10).

**Périmètre et stratégie de preuve :**
- **Deux connexions SQLite réelles**, dont la première détient le verrou SQL de l'étude avant l'archivage : le second praticien/onglet doit attendre ; des octets identiques sont rejoués sans seconde archive/audit, des octets différents pour la même révision sont refusés HTTP 409. Vérification finale d'une seule ligne `DocumentArchive`, d'un seul audit, du SHA du PDF et de l'absence de journal/fichier orphelin. Test `backend/tests/test_ceph_a4_s2b_j5_independent_review.py` — séquence SQL réelle, contrat de science testé indépendamment en JWT E2E existant.
- **Crash / reprise du PDF exact S2B :** préparation de journal + octets originaux sans COMMIT, tentative de reprise sur des octets révisés refusée sans suppression, reprise du même reçu exact, vérification archive SQL + PDF + absence d'orphelin. Le test générique SIGKILL/SQLCipher reste nécessaire pour prouver la coupure de processus, car la simulation J5 locale ne tue pas un processus.
- **A4 BEFORE / AFTER à même géométrie** : brouillon clinique historique et candidat descriptif synthétiques issus de la même étude, projection rasterisée A4 au même zoom, suppression contrôlée des sections Diagnostic/Plan et du mot Brouillon pour la version descriptive, identité médecin/cachet de configuration conservés, archivage de l'octet exact après aperçu. Artefacts PNG synthétiques non médicaux, sans valeur de validation clinique ni présentation de patient réel ; preuve raster et empreintes enregistrées par CI.
- **Tests applicables :** réussite de la compilation TypeScript, de la logique du composant React, des refus HTTP, de la régression calibrations et du contrôle archive historique. Les cinq XFAIL S1 antérieurs doivent rester explicitement classés comme exigences historiques de signature avancée, et **ne pas être représentés comme une certification S2B**.

**État :** PR J5 en branche isolée, tests à exécuter sur HEAD exact. Aucun SUCCESS inventé. Si course, hash ou crash révélait une anomalie, corriger avant clôture. La signature électronique qualifiée et le tampon graphique scanné ne sont pas des conditions de V1 ; les champs cachet actuels sont ceux de la configuration du cabinet.

### 12.1 Revue adversariale complémentaire — identité visible et périmètre de validation (13 novembre 2026)

**Défaut avéré par revue de code :** l'ancien reçu S2B était lié au graphe scientifique et aux octets PDF, mais **pas à l'état courant des données affichées dans le PDF** (nom/date de naissance/sexe du patient, nom du praticien et cachet textuel du cabinet). Une modification de ces champs après l'aperçu pouvait conserver la même révision scientifique et être archivée comme une identité périmée. L'approbation est par nature liée à *l'exact PDF vu* ; il faut aussi refuser les circonstances où les données affichées sont devenues obsolètes.

**Correction J5 candidate :**
- `rendered_identity_fingerprint` SHA-256 canonique couvre identifiant du patient, nom, prénom, date de naissance, sexe, ID et nom affiché du praticien, ID propriétaire et nom/cachet du cabinet. Il est inclus dans le reçu HMAC validé côté serveur.
- Préparation : calcule l'identité au rendu, puis relit après génération du PDF et refuse toute mutation avant l'émission du reçu. Archivage : sous verrou SQL d'étude, relit patient/cabinet, protège ces deux lignes sur PostgreSQL avec FOR UPDATE, rafraîchit le praticien authentifié et rejette 409 si le SHA de l'identité diffère. SQLite conserve son verrou d'écriture actuel.
- Le JSON local `DocumentArchive.clinical_data` enregistre aussi `rendered_identity_sha256` à côté de `scientific_source_sha256` et `approved_pdf_sha256` ; aucun ajout de colonne ni migration.
- Les tests synthétiques couvrent désormais la mutation du nom, de la naissance, du cachet et du nom du praticien entre aperçu et approbation ; ils ne doivent créer ni ligne ni PDF officiel. Les tests HMAC couvrent une substitution de ce fingerprint.

**Changement de périmètre J5 :** le lot était annoncé initialement « tests uniquement ». La revue a révélé un défaut réel d'intégrité ; correction serveur limitée aux deux routes S2B et au service de validation, et ajustement des tests existants, toujours sans toucher au moteur clinique, R11–R14 ou UI runtime. La première CI J5 GREEN au SHA `031670081a5fab33d028756ffec1e32e82541b9d` **ne valide pas** ce correctif ultérieur : exiger une nouvelle CI exact SHA et preuves avant clôture.

**Preuve du jalon initial (sans ce correctif) :** [E2E #43445110928](https://github.com/hraaaaf/Digital_crown/actions/runs/43445110928) COMPLETED/SUCCESS, 3 tests de concurrence/recovery + 1 comparaison A4 synthétique PASS, 29 tests React PASS, GUI/SQLite PASS. Artefact visuel [#14046544433](https://github.com/hraaaaf/Digital_crown/actions/runs/43445110928/artifacts/14046544433), SHA `6bea0849f6376741fa7d78b98f0602045e2f8200957e11becf030dc707b7db9f`. **Next :** confirmer tous les tests après correction d'identité sur le HEAD exact, puis revue de sécurité indépendante humaine si requise par le gate.

### 12.2 Vérification humaine des captures BEFORE/AFTER — défaut d'en-tête découvert

L'artefact synthétique J5 [#14046544433](https://github.com/hraaaaf/Digital_crown/actions/runs/43445110928/artifacts/14046544433) a été téléchargé, décompressé et les deux images de la page A4 examinées visuellement à même échelle. Le rendu AFTER éliminait les sections Diagnostic et Plan ; cependant, il contenait encore les textes *fictifs* de la template générique **« Dr. Nom Prénom », « د. الإسم الكامل », « Votre adresse de cabinet », « Contact »** alors que le corps du document identifiait un autre médecin (« Dr. Test »). Ce résultat de test aurait été dangereux sur un bilan officiel ; la première CI verte ne prouvait donc pas une qualité de rendu exploitable.

**Correction candidate J5 :**
- Le renderer A4 descriptif fixe la première ligne de l'en-tête FR au **praticien authentifié** déjà lié au PDF, conserve les lignes secondaires professionnelles configurées, et ne fabrique **aucun nom arabe** si la traduction authentique n'a pas été configurée ; la template d'origine pour les brouillons historiques demeure inchangée.
- `require_real_cabinet_letterhead` refuse dès la préparation du bilan A4 descriptif toute configuration sans nom de cabinet, **adresse professionnelle effective** ou **moyen de contact effectif**. Les champs des utilisateurs associés ne servent qu'en fallback réel ; aucun mot de démonstration ne peut se transformer en en-tête officiel.
- Le hash du contexte de rendu lié au reçu HMAC couvre désormais aussi l'adresse, les numéros et contacts du cabinet, les lignes d'en-tête et le template/logo déclaré ; toute modification entre la revue et l'archivage invalide la preuve. Le PDF imprimé contient une mention neutre : *« Le PDF isolé n'atteste pas à lui seul sa validation »*, la preuve étant l'archive authentifiée.
- Les tests synthétiques sont configurés avec adresse/contact fictifs mais clairement TEST ONLY, en laissant les lignes d'en-tête initialement vides pour prouver que l'AFTER n'utilise plus « Dr. Nom Prénom ». Nouvelle vérification explicite des textes, refus si adresse/contact absents et mutation de l'adresse/téléphone après l'aperçu. **Repassage CI exact HEAD exigé**.

**Statut :** corrections en branche test #1326, ni mergées ni déployées. Aucun résultat clinique ou score visuel déclaré avant un nouvel artefact AFTER examiné visuellement et les contrôles exact HEAD GREEN.
