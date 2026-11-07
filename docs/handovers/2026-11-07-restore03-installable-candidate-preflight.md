# Digital Crown — RESTORE-03 → Desktop certifiable — preflight / handover

**Date :** 2026-11-07  
**Statut :** DRAFT / PREPARATION ONLY — NOT INSTALLABLE — NO CLINICAL GO  
**Décision :** préparer la candidature et les preuves sans fusion, certification, création d'EXE, installation, activation, mutation de cabinet ni contournement des gates.

## Goal / Success / Proof

- **GOAL :** fournir une reprise reproductible et des gates explicites pour passer des FUE de laboratoire RESTORE-03 à un *futur* artefact Windows `INSTALLABLE_CERTIFIED`, puis à la restauration vérifiée A→B sur matériel isolé et au contrôle RESTORE-04 NAS/SMB réel.
- **SUCCESS de ce sous-lot documentaire :** les preuves existantes sont indexées au SHA, les étapes exécutables et leurs STOP sont définies, toutes les cases non prouvées restent ouvertes.
- **PROOF :** GitHub PR/commit, runs et artifacts ci-dessous ; fichier présent dans la PR DRAFT. Ce document ne certifie aucun code, build ni appareil.

## Contexte immuable AVANT ce document

| Élément | Source / verdict vérifié |
|---|---|
| PR | [#1221](https://github.com/hraaaaf/Digital_crown/pull/1221), DRAFT / OPEN / UNMERGED |
| Dernier HEAD FUE intégralement observé | `4168e4bfc66af91c34bee925abe4e2b607712434` |
| CI au HEAD ci-dessus | 38 workflows : **37 SUCCESS**, **1 SKIPPED** (M6-I Biometric Passkey Certification), **0 failure**, **0 actif** |
| P4 normal Windows A→B | [run #42419219432](https://github.com/hraaaaf/Digital_crown/actions/runs/42419219432), deux jobs SUCCESS ; preuve B [artifact #13593131296](https://github.com/hraaaaf/Digital_crown/actions/runs/42419219432/artifacts/13593131296) |
| P4 échec injecté / retour arrière | [run #42414723899](https://github.com/hraaaaf/Digital_crown/actions/runs/42414723899) SUCCESS sur un HEAD antérieur ; **pas** une preuve P4 normal |
| Interface React + FastAPI réelle, parcours non destructif | [run #42419221191](https://github.com/hraaaaf/Digital_crown/actions/runs/42419221191) SUCCESS, **full apply = NOT RUN**, artefact #13592653578 |
| Windows source SQLCipher et refus de packaging non certifié | [run #42419219419](https://github.com/hraaaaf/Digital_crown/actions/runs/42419219419) SUCCESS ; **pas un EXE installé** |
| Offsite copies chiffrées Linux + Windows | [run #42419219597](https://github.com/hraaaaf/Digital_crown/actions/runs/42419219597) SUCCESS en LAB, **pas un NAS/SMB physique** |
| Second-PC préflight non destructif | [run #42419219434](https://github.com/hraaaaf/Digital_crown/actions/runs/42419219434) SUCCESS sur runner, **pas un second PC physique** |
| Régression CODE candidate (sans package) | [run #42419219672](https://github.com/hraaaaf/Digital_crown/actions/runs/42419219672) trois jobs SUCCESS, **pas `CODE_CERTIFIED`** |
| Audit de readiness | [run #42419219402](https://github.com/hraaaaf/Digital_crown/actions/runs/42419219402) SUCCESS en lecture seule ; [artifact #13592986888](https://github.com/hraaaaf/Digital_crown/actions/runs/42419219402/artifacts/13592986888) |
| Blocage formel | `CODE_CERT_STATUS=NO_NONEXPIRED_EXACT_MASTER_CODE_CERTIFIED_ARTIFACT`; `INSTALLABLE_READY=false`. SRPose38 externe = SHA/taille conformes aux pins PR et master, **pas** validation scientifique clinique |

**Attention SHA :** toute écriture après `4168e4bf` crée un nouveau HEAD. Ne jamais attribuer automatiquement les 37 anciens PASS au nouveau commit. Recontrôler PR, CI et éventuel gate visuel au SHA final.

## Gate A — figer une candidate PR (autorisé, sans release)

- [ ] Vérifier HEAD 40 caractères, base `master`, diff, branches/runs actifs, zéro code ou secret clinique dans les artefacts.
- [ ] Faire passer tests ciblés + FUE pertinents au **nouveau HEAD** ; toute régression requise = STOP.
- [ ] Préparer les captures et approbations visuelles/humaines exigées par le produit au SHA courant. Ne pas recycler une approbation d'un SHA précédent.
- [ ] Préparer la décision humaine **distincte** de merge ; **ne pas fusionner** sur simple feu vert CI.

**Succès :** candidat documentalement prêt pour décision humaine. **Preuve :** matrice exacte SHA/runs/artefacts, gate visuel si applicable. **Pas de certificat installable à ce stade.**

## Gate B — CODE_CERTIFIED exact master (NON AUTORISÉ DANS CETTE MISSION)

Prérequis : **autorisation de merge distincte**, PR fusionnée, SHA courant de `master` immuable et CI vérifiée. Le workflow officiel `.github/workflows/cabinet-release-certification.yml` refuse volontairement tout SHA différent du HEAD exact de `master`.

Après autorisation future, sur `master` seulement :

```text
Workflow : Cabinet Certified Release
commit_sha=<SHA exact courant de master, 40 caractères>
```

- [ ] Backend complet, frontend, PostgreSQL 18, préservation données, profils BASIC/GOLD/ELITE PASS.
- [ ] Artifact `code-certified-dc-cabinet-<SHA12>-run<RUN_ID>` présent, non expiré, hash/manifeste `release-content.sha256` vérifiés.
- [ ] Attestation GitHub/Sigstore cryptographique reliée au repo, au workflow officiel, à `refs/heads/master` et au même SHA.

**STOP :** artifact manquant/expiré, manque d'attestation ou mismatch de SHA. **`CODE_CERTIFIED` reste non installable.**

## Gate C — assets puis composition INSTALLABLE_CERTIFIED (NON AUTORISÉ ICI)

Sources normatives : `docs/CABINET_CERTIFIED_RELEASE_POLICY.md`, `backend/scripts/certify_runtime_assets.py`, `backend/scripts/create_release.ps1`, `backend/runtime_asset_certification.py`.

Sur machine *isolée* détentrice des modèles externes autorisés et uniquement après Gate B :

```powershell
python backend\scripts\certify_runtime_assets.py `
  --code-release-dir "C:\<dossier-code-certifie>" `
  --ai-models-dir "C:\<dossier-modeles-valides>" `
  --output "C:\<dossier-sortie>\runtime-assets-<SHA12>.zip"

backend\scripts\create_release.ps1 `
  -CertifiedArtifactZip "C:\<dossier-sortie>\code-certified-....zip" `
  -RuntimeAssetsZip "C:\<dossier-sortie>\runtime-assets-<SHA12>.zip"
```

- [ ] SHA code et SHA bundle runtime **identiques** ; registre `backend/scientific_assets.json` épinglé.
- [ ] Hash/taille de chaque fichier embarqué : MATCH ; assets non scientifiquement épinglés séparés des assets scientifiquement vérifiés.
- [ ] GitHub/Sigstore vérifié par la voie canonique ; ne jamais reconstruire/copier le working tree.
- [ ] Vérifier les 7 fichiers d'identité/manifeste/certification attendus par `installer/DigitalCrown.iss` et le vérificateur du produit.
- [ ] Release finale revalidée, identité et preuves inscrites au dossier ; **aucune activation automatique**.

**STOP :** échec au vérificateur, manifest incomplet, asset externe absent, nouvelle source non épinglée ou mismatch. Ni changement manuel de modèle ni bypass de `DigitalCrown.spec`.

## Gate D — construire et tester l'installateur (NON AUTORISÉ ICI)

- [ ] Après `INSTALLABLE_CERTIFIED`, respecter la voie officielle `DigitalCrown.spec` puis `installer/DigitalCrown.iss` ; jamais `scripts/build_exe.py` (retiré pour sécurité).
- [ ] Émettre SHA du dossier certifié et du binaire/installeur, versions Python/PyInstaller/Inno et résultat d'un scan de secrets.
- [ ] Sur machine **synthétique / non clinique**, installer sans démarrage ni seed automatique ; démarrer seulement sous protocole de test explicitement autorisé.
- [ ] Prouver refus de l'EXE altéré et des preuves absentes ; tester reboot, sauvegarde/rollback et non-écrasement du répertoire utilisateur.
- [ ] Authenticode Windows est une couche distincte de la provenance GitHub/Sigstore.

**STOP :** installateur non signé si signature obligatoire dans le contexte, certificat absent, exécutable non traçable au SHA, divergence runtime, apparition de données/secrets réels.

## Gate E — deux machines A→B (MATÉRIEL ET ACCÈS REQUIS)

**Identités à relever sans données personnelles :** machine A/B distinctes, éditions/builds Windows, hash du binaire installé, emplacement isolé, configuration du réseau de test, compte utilisé, support du bundle, date, opérateur.

| Scénario | Critères PASS vérifiables |
|---|---|
| A : export | DB + médias **strictement synthétiques** dans un `.dcbundle` chiffré ; SHA256 stocké hors de l'archive ; aucun `backup.key`, `.env` ou `license_vault.bin` |
| B : préflight | `scripts/restore03_second_pc_preflight.ps1` vérifie bundle local, hash et manifeste ; refuse environnement cabinet, UNC/reparse et mauvais SHA |
| B : restauration normale | exécution du worker avec EXE certifié ; parcours réellement appliqué DB + médias ; journal opérationnel sans secret |
| B : vérification après redémarrage | identité des patients fictifs, compteur/IDs, hashes médias, DB, santé du backend, licence à revalider, cutoff mobile, tokens invalidés et appareils révoqués |
| B : échecs contrôlés | bundle altéré, mauvaise clé, rebind échoué, fumée HTTP non verte ; rollback DB/médias/coffre **après** la bascule, octet par octet |

**Important :** les runners Windows GitHub ne prouvent ni PC physique, ni EXE gelé, ni restauration via interface installée. Si un scénario manque, inscrire `NOT_RUN`, jamais PASS.

## Gate F — RESTORE-04 NAS/SMB réel (MATÉRIEL ET ACCÈS REQUIS)

- [ ] Partage SMB test non clinique, compte de service à droits minimum, ACL testées par lecture/écriture refusées ou autorisées selon rôles ; secret de connexion non consigné.
- [ ] Une paire DB/médias déjà chiffrée, hash côté source et destination, publication atomique sans écraser un objet existant.
- [ ] Coupure SMB au milieu d'une copie ; récupération et échec explicite sans supprimer le backup local.
- [ ] Concurrence/collisions, fichiers symlink/reparse/junction, chemin altéré, droits révoqués ; jamais de publication extérieure à la racine approuvée.
- [ ] Récupération autonome sur un autre poste avec clé d'escrow dédiée, contrôle humain, checksum et relecture DB/médias synthétiques.
- [ ] Remote retention DELETE reste **désactivé** tant que son propre gate n'est pas formellement autorisé.
- [ ] Rapports sans secret ni donnée patient et preuves d'une **vraie** cible NAS/SMB, pas simplement runner ou montage temporaire.

## Verdict à conserver dans chaque rapport

```json
{
  "tested_head": "SHA40",
  "code_certified": "NOT_RUN",
  "installable_certified": "NOT_RUN",
  "actual_frozen_exe": false,
  "physical_windows_a_b": "NOT_RUN",
  "nas_smb_real": "NOT_RUN",
  "real_patient_data_used": false,
  "clinical_go": false,
  "merge_authorized": false,
  "installation_authorized": false
}
```

Les champs ci-dessus sont un *modèle documentaire* de preuve, pas le résultat d'une exécution. Toute action sur un cabinet réel exige des validations de sécurité/données et une décision humaine distincte.

## Bloqueurs / Next exact

1. **Actuellement exécutable sans autorisation supplémentaire :** documenter, auditer en lecture seule, FUE synthétiques sur CI, préparer machines/supports non cliniques sans ouvrir de données réelles.
2. **Gate humain requis :** autorisation explicite de fusion + gates visuels applicables ; puis `CODE_CERTIFIED` sur le HEAD exact de `master`.
3. **Gate technique requis :** source des assets runtime autorisée, attestation GitHub/Sigstore, `INSTALLABLE_CERTIFIED`, hash du build.
4. **Gate matériel requis :** deux PC physiques et un NAS/SMB de test, autorisation d'accès et protocole non clinique.
5. **Gate clinique distinct :** aucune installation ni migration clinique sur la base de ce document.

**Fichier de reprise :** `docs/handovers/2026-11-07-restore03-installable-candidate-preflight.md`; dossier de suivi Notion RESTORE-03 lié à la PR #1221.
