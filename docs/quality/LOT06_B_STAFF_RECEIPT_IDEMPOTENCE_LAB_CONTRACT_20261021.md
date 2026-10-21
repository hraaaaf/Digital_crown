# V1.5-06 / LOT06-B — Contrat LAB de confirmation staff et reçu idempotent

**STATUT : SYNTHÉTIQUE / CODE DE TEST UNIQUEMENT / NO-GO clinique.**
**Source de départ :** PR #998, `b8b818d932153fafc679ff4b67ecf081e8febc5e`. Le LAB ne monte aucune route HTTP, n'importe aucun `ClinicalAsset` et ne modifie ni `backend`, ni les données Patient/RDV du cabinet, ni l'installateur/SCM.

## Modèle et invariants mesurables

1. **Source synthétique :** bytes 2×2 PNG obtenus dans le test via `HotFolder.read_verified` ; la méthode `fixture_capture` calcule et stocke son SHA-256 local. Cela **ne prouve pas** l'identité réelle d'un appareil ni un transfert de bytes vers le serveur.
2. **Staff / workstation / Patient / RDV :** autorité **mockée** sous une même DB de fixture. `fixture_staff` fabrique une session locale ; elle n'est ni un vrai JWT ni un login Cabinet. Toute approbation requiert `explicit_staff_action is True`, une session staff autorisée, une station active, un Patient actif et un RDV actif du même cabinet relié à ce Patient, plus capture+SHA+station inchangés. Toute discordance échoue fermée.
3. **Commit :** une approbation lab est enregistrée avant toute tentative de reçu. Le `commit` revérifie, **dans une transaction SQLite `BEGIN IMMEDIATE`**, staff, tenant, station, Patient, RDV, capture et digest. Il insère reçu **et événement d'audit dans la même transaction**. `UNIQUE(tenant,capture_id)` et le verrou SQLite garantissent un seul reçu local par acquisition dans ce modèle.
4. **Idempotence/récupération logique :** répéter le *même approval_id* restitue le même `LAB-...` sans nouvel événement de commit (y compris après réouverture DB et dans plusieurs threads). Nouvelle approbation ou liaison conflictuelle pour un capture déjà reçu : erreur, sans remplacer le reçu. Panne injectée après INSERT de reçu ou après audit avant COMMIT : rollback de toutes les écritures de transaction ; essai suivant permis.
5. **Fail closed :** réservé à `ENVIRONMENT=test`, `DIGITALCROWN_ISOLATED_RUNTIME=true` et `DC_V15_06_ACK_CONTRACT_LAB=1`, sous racine `tempfile` explicitement marquée. Aucun appel HTTP, transport, autorisation clinique, `server_confirmed=True` ou modification de `HotFolder.items()` ; le spool demeure `PENDING_CONFIRMATION` même si la fixture crée un reçu `LAB_RECEIPT_COMMITTED`.

## Portée de la preuve et erreurs à ne pas commettre

- Ce LAB prouve **l'atomicité des deux tables locales `receipts` et `audit` d'une DB SQLite fictive**, pas l'atomicité entre SQL clinique + Media Core + blob chiffré + spool/poste ; pas un accusé réseau ni un reçu clinique véritable.
- Les méthodes `fixture_*` constituent **l'autorité simulée entièrement contrôlée par le test**. Un acteur qui peut écrire la SQLite de fixture peut modifier les identités/approbations ; la séparation des rôles, la résistance au même SID, l'hébergement SCM et la sécurité des clés ne sont pas prouvés.
- Le `explicit_staff_action` est un **drapeau du banc**, pas une attestation UI d'un opérateur ; aucun BEFORE/AFTER humain, test d'un vrai écran ou empreinte numérique d'approbation. Rien ne déclenche l'ancienne API `/api/patients/{patient_id}/assets/import`.
- Les rejets, le concurrent local et la coupure transactionnelle sont des exercices **software-only** ; ni coupure électrique, ni perte d'un commit fsync, ni restauration DB+blobs, ni test Windows SCM W01–W12.
- Contourner ces limitations en connectant directement le module LAB au backend productif serait un **BLOCKER de sécurité**.

## Next exact, sans élargissement implicite

Formaliser d'abord un **vrai contrat de session de capture** autorisé par un principal appareil/enrôlement vérifié, une **confirmation humaine staff** attestée par login/permissions serveur, un flux Media Core chiffré lié à `source_capture_id + sha256 + cabinet + workstation + patient + RDV + request_id`, puis réservation/idempotence durable avec transaction et boîte de sortie pour l'ACK (pas de double import après perte de réponse). Revalider toutes les autorités à l'instant de l'écriture, gérer annulation/révocation, erreurs/récupération et restauration cross-store. Cette étape produit est **OPEN** et exigera son propre GO de conception et des tests au HEAD final. Le HOLD Codex/SCM demeure. La PR fille de #998 reste DRAFT, jamais un permis d'activer ou déployer.
