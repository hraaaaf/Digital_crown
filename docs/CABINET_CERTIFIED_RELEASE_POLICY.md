# Digital Crown — Politique canonique des releases cabinet certifiées

## Statut

**Règle absolue et fail-closed.** Ce document gouverne toute installation ou mise à jour d'un cabinet Digital Crown.

## Goal

Garantir qu'aucun cabinet réel ne puisse installer ou démarrer un checkout, une branche, `master`, un working tree ou un build ad hoc. L'unité installable est exclusivement une **release immuable certifiée**, liée à un SHA Git exact et validée pour les trois packs commerciaux **BASIC / GOLD / ELITE**.

## Invariant d'installation

Une version est `INSTALLABLE` si et seulement si toutes les conditions suivantes sont prouvées :

1. son `commit_sha` est un SHA Git complet de 40 caractères ;
2. ce SHA est déjà intégré à `master` ;
3. le workflow GitHub Actions `Cabinet Certified Release` a été exécuté sur ce SHA exact ;
4. backend complet, frontend tests/build, PostgreSQL 18, préservation Patient/Documents/médias synthétique et règles de release sont verts ;
5. l'artefact contient :
   - `release-certification.json` ;
   - `.digitalcrown-release-sha` ;
   - `release-content.sha256` ;
6. le certificat couvre simultanément `BASIC`, `GOLD`, `ELITE` ;
7. le manifest SHA-256 correspond à tous les fichiers certifiés ;
8. `create_release.ps1` importe l'artefact sans jamais le reconstruire depuis le working tree ;
9. `run_real_backend.ps1` revérifie identité + hashes avant toute activation réelle ;
10. un build PyInstaller vérifie le payload certifié avant compilation et embarque l'identité certifiée ;
11. l'installeur Inno Setup refuse de compiler sans identité certifiée ;
12. l'EXE packagé vérifie l'identité certifiée avant tout bootstrap/écriture cabinet.

**`master` n'est jamais installable en tant que ref mouvante.** Un SHA appartenant à `master` peut devenir installable uniquement après émission de son certificat.

## Release universelle et packs

Il n'existe qu'un seul binaire/source runtime par SHA certifié. Le même artefact est certifié pour :

- `BASIC`
- `GOLD`
- `ELITE`

La licence et les entitlements déterminent les capacités commerciales après installation ; ils ne créent pas trois forks/binaires différents.

Les noms de certification `BASIC/GOLD/ELITE` sont le contrat commercial d'installation. Ils ne constituent pas, à eux seuls, une migration des enums historiques éventuellement présents en base/code. Une évolution du modèle de licence reste un chantier séparé avec migration explicite.

## Workflow officiel de certification

### 1. Développement

Les changements vivent sur une branche/PR. Toute PR exécute notamment :

- CI générale ;
- `Cabinet Upgrade PostgreSQL Certification` sur PostgreSQL 18 ;
- tests de préservation Patient/Documents ;
- tests de la politique de release.

Le gate PostgreSQL/release ne possède **aucun filtre `paths:`** : une PR ne peut pas l'éviter en modifiant un fichier non listé.

### 2. Merge

Une fois les preuves du lot acquises, la PR est mergée selon le processus du chantier. Le merge ne crée pas automatiquement une version installable.

### 3. Certification

Déclencher manuellement `.github/workflows/cabinet-release-certification.yml` avec :

```text
commit_sha=<SHA EXACT 40 caractères>
```

Le workflow refuse :

- `master` ;
- `HEAD` ;
- un tag ;
- un SHA court ;
- un SHA non ancêtre de `master`.

Il rejoue les preuves de release et produit uniquement après succès l'artefact :

```text
dc-cabinet-<12 premiers caractères SHA>-run<GITHUB_RUN_ID>
```

### 4. Import cabinet

Télécharger l'artefact ZIP GitHub Actions, puis :

```powershell
backend\scripts\create_release.ps1 `
  -CertifiedArtifactZip "C:\chemin\dc-cabinet-...zip"
```

Le script :

- ne lit/copiera jamais le working tree ;
- vérifie certificat, SHA, packs et hashes ;
- refuse tout écrasement d'une release existante ;
- crée une release immuable hors dépôt ;
- n'active rien.

### 5. Activation réelle

Après backup/rehearsal requis par le niveau de risque :

```powershell
backend\scripts\run_real_backend.ps1 `
  -ReleaseId "dc-cabinet-..." `
  -ConfirmRealActivation "YES"
```

Le launcher revalide le certificat et tous les fichiers certifiés **avant** de lire/utiliser la configuration du cabinet.

## EXE / installeur Windows

Un EXE de production doit être construit depuis le contenu extrait de l'artefact certifié :

1. `DigitalCrown.spec` vérifie le payload source certifié intégral ;
2. il embarque certificat + SHA + manifest ;
3. `run.py` vérifie cette identité avant le first boot ;
4. `installer/DigitalCrown.iss` refuse de compiler si ces fichiers ne sont pas présents dans `dist/DigitalCrown`.

Un `DigitalCrownSetup.exe` produit autrement est **NON CERTIFIÉ / NON INSTALLABLE**, même s'il semble fonctionner.

## Données réelles et rehearsal

La certification automatisée est nécessaire mais ne remplace pas un rehearsal sur copie fraîche lorsqu'une évolution touche ou peut toucher :

- schéma DB / migrations / enums ;
- `Patient` / `DocumentArchive` / actes / paiements ;
- chemins DB/médias ;
- startup/bootstrap/seeds ;
- installer/restore/backup ;
- tenant/isolation pouvant masquer des dossiers historiques.

Dans ces cas, avant de certifier une nouvelle release destinée à un cabinet existant :

1. inventaire read-only réel ;
2. backup DB + médias ;
3. copie/rehearsal isolé ;
4. BEFORE/AFTER compteurs + IDs + hashes ;
5. smoke fonctionnel ;
6. verdict explicite `GO INSTALLATION`.

Aucune écriture de test ne doit toucher la DB ou les médias réels.

## Interdictions permanentes

- installer `master`, `HEAD`, une branche ou un tag directement ;
- fabriquer une release depuis le working tree ;
- copier manuellement des fichiers modifiés dans une release certifiée ;
- éditer une release déjà importée ;
- supprimer/bypasser le verifier pour « débloquer » un cabinet ;
- émettre un certificat ne couvrant pas les trois packs ;
- considérer une CI verte comme équivalente au rehearsal réel quand le risque données l'exige ;
- auto-déployer/auto-upgrader un cabinet vers le dernier `master`.

## Preuves techniques canoniques

- `.github/workflows/cabinet-upgrade-postgres-cert.yml`
- `.github/workflows/cabinet-release-certification.yml`
- `backend/release_certification.py`
- `backend/scripts/verify_certified_release.py`
- `backend/scripts/create_release.ps1`
- `backend/scripts/run_real_backend.ps1`
- `backend/tests/test_certified_release_policy.py`
- `DigitalCrown.spec`
- `run.py`
- `installer/DigitalCrown.iss`

## Limite supply-chain explicite

Le certificat et le manifest SHA-256 empêchent les dérives accidentelles/working-tree et détectent la modification des fichiers certifiés. Ils ne remplacent pas encore une signature Authenticode ou une attestation cryptographique externe avec clé matérielle. Cette couche pourra être ajoutée ultérieurement sans affaiblir le présent fail-closed.
