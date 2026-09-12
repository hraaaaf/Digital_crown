# Digital Crown — Politique canonique des releases cabinet certifiées

## Statut

**Règle absolue, fail-closed, transverse à tous les chantiers.**

Aucun cabinet réel ne doit installer ou démarrer `master`, `HEAD`, une branche, un tag, un working tree, un build ad hoc ou un simple artefact CI.

## Goal

L’unité installable est exclusivement une **release immuable `INSTALLABLE_CERTIFIED`**, liée à un SHA Git exact de 40 caractères et compatible avec les trois profils de distribution **BASIC / GOLD / ELITE**.

## Deux niveaux obligatoires

### 1. `CODE_CERTIFIED`

Émis uniquement par `.github/workflows/cabinet-release-certification.yml` pour **le HEAD courant exact de `master`**.

Il prouve :

- SHA Git exact 40 caractères ;
- backend complet vert ;
- frontend tests + build verts ;
- PostgreSQL 18 / compatibilité upgrade verts ;
- préservation Patient/Documents synthétique verte ;
- politique de release verte ;
- couverture des profils `BASIC / GOLD / ELITE` ;
- manifest `release-content.sha256` ;
- attestation GitHub/Sigstore cryptographique du manifest, liée au repo, au workflow signataire et au SHA source.

**`CODE_CERTIFIED` n’est pas installable.** Les modèles/assets scientifiques externes ne sont volontairement pas stockés dans Git.

### 2. `INSTALLABLE_CERTIFIED`

Créé localement uniquement par composition d’un `CODE_CERTIFIED` avec un bundle d’assets runtime certifié pour **ce même SHA**.

Il prouve en plus :

- provenance GitHub/Sigstore du manifest code vérifiée ;
- bundle d’assets ciblant exactement le même SHA ;
- digest exact de `backend/scientific_assets.json` ;
- SHA-256 de chaque asset réellement packagé ;
- vérification des pins scientifiques déjà présents dans le registre ;
- conservation explicite de la liste des assets encore non épinglés scientifiquement ;
- cohérence exacte entre sélection d’assets certifiée et sélection PyInstaller ;
- certificat final `installable-certification.json` ;
- revérification complète avant promotion atomique dans `releases/`.

**Seul `INSTALLABLE_CERTIFIED` peut être activé ou transformé en EXE/installer.**

## Profils BASIC / GOLD / ELITE

Un seul code/binaire universel est produit par SHA. Les profils `BASIC / GOLD / ELITE` sont les profils de distribution certifiés de la release.

Ils ne créent pas trois forks.

Les enums internes historiques actuellement présents dans le code de licence peuvent porter d’autres noms, notamment `GOLD / PREMIUM / ELITE`. Cette politique de release **ne renomme pas automatiquement ces données historiques**. Toute migration commerciale d’enums reste un chantier distinct avec migration et compatibilité explicites.

## Workflow officiel

### A. Développement / PR

Toute PR exécute notamment :

- CI générale ;
- `Cabinet Upgrade PostgreSQL Certification` sur PostgreSQL 18 ;
- tests de préservation Patient/Documents ;
- tests de politique release.

Le gate cabinet ne possède aucun filtre `paths:` : une PR ne peut pas contourner la protection en modifiant un fichier non listé.

### B. Merge

Le merge ne rend rien installable.

### C. Certification CODE

Depuis **`master` uniquement**, déclencher :

```text
Cabinet Certified Release
commit_sha=<HEAD master exact, 40 caractères>
```

Le workflow refuse notamment :

- `master`, `HEAD`, tag ou SHA court comme valeur mouvante ;
- un SHA différent du HEAD courant de `master` ;
- une exécution du workflow depuis une autre ref ;
- tout gate backend/frontend/PostgreSQL/préservation non vert.

Sortie :

```text
code-certified-dc-cabinet-<SHA12>-run<RUN_ID>
```

avec :

- `release-certification.json` → `certification_level=CODE_CERTIFIED` ;
- `.digitalcrown-release-sha` ;
- `release-content.sha256` ;
- attestation Sigstore GitHub de `release-content.sha256`.

### D. Certification des assets runtime

Sur la machine qui détient les modèles externes :

```powershell
python backend\scripts\certify_runtime_assets.py `
  --code-release-dir "C:\chemin\code-certified-extrait" `
  --ai-models-dir "C:\chemin\backend\ai_models" `
  --output "C:\chemin\runtime-assets-<SHA12>.zip"
```

Le script sélectionne exactement les fichiers que PyInstaller est autorisé à embarquer, hash chaque fichier et lie le bundle au SHA code + digest du registre scientifique.

### E. Composition `INSTALLABLE_CERTIFIED`

```powershell
backend\scripts\create_release.ps1 `
  -CertifiedArtifactZip "C:\chemin\code-certified-...zip" `
  -RuntimeAssetsZip "C:\chemin\runtime-assets-...zip"
```

Le script :

1. extrait les ZIP avec protection path traversal ;
2. vérifie les hashes du CODE artifact sans exécuter son code ;
3. vérifie cryptographiquement l’attestation GitHub/Sigstore avec :
   - repo `hraaaaf/Digital_crown` ;
   - workflow signataire exact ;
   - SHA source exact ;
   - ref source `refs/heads/master` ;
   - refus des runners self-hosted ;
4. extrait le bundle runtime ;
5. exécute ensuite seulement le composeur provenant du CODE artifact désormais attesté ;
6. revalide code + assets ;
7. crée `installable-certification.json` ;
8. revalide la release finale ;
9. promeut atomiquement la release dans `RuntimeRoot\releases\<release_id>` ;
10. n’active rien.

### Vérification Sigstore hors ligne

`create_release.ps1` accepte :

```powershell
-AttestationBundle "...jsonl" `
-TrustedRoot "trusted_root.jsonl"
```

Les deux doivent être fournis ensemble. Sans eux, la vérification se fait via GitHub CLI en ligne.

## Activation réelle

```powershell
backend\scripts\run_real_backend.ps1 `
  -ReleaseId "dc-cabinet-..." `
  -ConfirmRealActivation "YES"
```

Avant de lire la configuration réelle du cabinet, le launcher exige et revérifie :

- `release-certification.json` ;
- `.digitalcrown-release-sha` ;
- `release-content.sha256` ;
- `installable-certification.json` ;
- `runtime-assets-certification.json` ;
- `runtime-assets-content.sha256` ;
- `github-attestation-verification.json` ;
- tous les fichiers code certifiés ;
- tous les assets runtime certifiés.

Toute divergence = **activation refusée**.

## EXE / installeur Windows

`DigitalCrown.spec` :

- refuse tout dossier qui n’est pas `INSTALLABLE_CERTIFIED` ;
- utilise la même sélection d’assets que le certifieur ;
- revalide code + assets avant PyInstaller ;
- embarque les certificats/manifests/preuves nécessaires.

`run.py` :

- revérifie l’identité INSTALLABLE + les assets embarqués **avant le first boot** ;
- aucun `.env`, secret, DB ou média n’est créé/touché avant ce gate.

`installer/DigitalCrown.iss` :

- refuse de compiler si les preuves INSTALLABLE ne sont pas présentes dans `dist/DigitalCrown`.

Tout `DigitalCrownSetup.exe` produit autrement est **NON CERTIFIÉ / NON INSTALLABLE**.

## Assets scientifiques

`backend/scientific_assets.json` reste la source de vérité scientifique.

La certification runtime distingue explicitement :

- **asset épinglé scientifiquement** : path + taille + SHA-256 connus, obligatoirement vérifiés ;
- **asset non encore épinglé scientifiquement** : ses octets sont figés pour l’intégrité de cette release mais cela ne constitue aucune validation scientifique.

La certification d’installation ne doit jamais être présentée comme une validation clinique/scientifique.

## Données réelles / rehearsal

La certification automatisée est nécessaire mais ne remplace pas un rehearsal sur copie fraîche lorsqu’une évolution peut toucher :

- schéma DB / migrations / enums ;
- Patient / DocumentArchive / actes / paiements ;
- chemins DB/médias ;
- bootstrap/seeds ;
- installer/restore/backup ;
- tenant/isolation pouvant masquer des dossiers historiques.

Dans ces cas : inventaire réel read-only → backup DB+médias → copie isolée → BEFORE/AFTER compteurs/IDs/hashes → smoke → verdict explicite `GO INSTALLATION`.

## Interdictions permanentes

- installer `master`, `HEAD`, une branche ou un tag ;
- installer directement un `CODE_CERTIFIED` ;
- créer une release depuis le working tree ;
- éditer une release déjà composée ;
- remplacer/copier manuellement un asset après certification ;
- contourner le verifier pour « débloquer » un cabinet ;
- certifier moins que BASIC/GOLD/ELITE ;
- considérer une CI verte comme rehearsal réel quand le risque données l’exige ;
- auto-upgrader un cabinet vers le dernier `master`.

## Preuves techniques canoniques

- `.github/workflows/cabinet-upgrade-postgres-cert.yml`
- `.github/workflows/cabinet-release-certification.yml`
- `backend/release_certification.py`
- `backend/runtime_asset_certification.py`
- `backend/scripts/verify_certified_release.py`
- `backend/scripts/verify_installable_release.py`
- `backend/scripts/certify_runtime_assets.py`
- `backend/scripts/compose_installable_release.py`
- `backend/scripts/create_release.ps1`
- `backend/scripts/run_real_backend.ps1`
- `backend/tests/test_certified_release_policy.py`
- `DigitalCrown.spec`
- `run.py`
- `installer/DigitalCrown.iss`

## Supply-chain

La provenance code repose désormais sur une attestation GitHub/Sigstore cryptographiquement vérifiable, liée au repo/workflow/SHA. La signature Authenticode du futur installateur reste une couche distincte de distribution Windows et ne doit pas être confondue avec cette certification de provenance + intégrité.
