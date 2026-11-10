# LOT08.2-J — vrai ONNX 267 Mo dans un témoin PyInstaller Windows jetable (NON CLINIQUE)

## Décision / périmètre

**Goal :** démontrer sur un runner Windows natif qu'un *processus réellement figé par PyInstaller* contient une copie du modèle SRPose38 de 267 484 931 octets au SHA-256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`, sélectionnée par le même sélecteur d'actifs que l'application, tout en refusant automatiquement toute inférence céphalo, y compris en présence de variables de laboratoire.

**Limite stricte :** le témoin `DCSRPose38NoClinicalWitness.exe` n'est **pas** `DigitalCrown.exe`. Il ne compile pas `DigitalCrown.spec`, ne crée aucun installateur, ne copie aucun patient, ne lance aucune inférence ONNX ni service FastAPI. Le `DigitalCrown.spec` de production conserve impérativement son exigence `INSTALLABLE_CERTIFIED`, inchangée. Il serait faux d'appeler ce témoin une preuve que l'application Desktop distribuable est certifiée.

**Séquence sûre :** code produit et gate clinique **inchangés** ; branche de laboratoire dédiée dérivée du HEAD DRAFT de LOT08.2-I `e47f707bb087cba205351a652de5b397de151487` ; aucun merge, téléchargement sur poste de cabinet, déploiement ou installation.

## Preuves requises (aucune conclusion anticipée)

1. GitHub Actions Windows 2025, SHA exact et diff strictement limité à la présente workflow, au témoin et à ce document.
2. Source unique : GitHub run officiel `34281082926` SUCCEEDED, artefact `10077697721`, digest ZIP `sha256:ad1caa8ee1474a1405305fc91a29eaa3c0c5b20572095faad0c2e63723284e17`, ensemble exact de sept fichiers.
3. Vérifier la taille et le SHA du réel ONNX **avant copie**, puis le registre `backend/scientific_assets.json` et `iter_runtime_asset_files`.
4. Construire **un témoin distinct** avec PyInstaller Windows ; exécuter son vrai `.exe` et relire les octets **depuis `sys._MEIPASS`**. Vérifier l'identité du modèle et les mêmes sources du contrat, du sélecteur et du verrou clinique.
5. **DENY** clinique en mode frozen normal et malgré `ENVIRONMENT=test`, SQLite mémoire, `DIGITALCROWN_ISOLATED_RUNTIME=true` et `GITHUB_ACTIONS=true`.
6. Altérer 1 octet **uniquement dans la copie jetable du témoin**, garder la même taille, relancer le `.exe` et exiger un code d'échec avec `MODEL_SHA256_MISMATCH`.
7. Ne publier qu'un JSON de **méta-preuve**, jamais les 267 Mo, ni la build EXE ni un installer. Nettoyage des répertoires de labo.

## Jalons NON prouvés par ce témoin

- Packaging de l'application `DigitalCrown.exe` via `DigitalCrown.spec` : **NON VÉRIFIÉ**, nécessite une release `INSTALLABLE_CERTIFIED` valide pour un SHA exact.
- Validation des 38 canaux anatomiques : **NON VÉRIFIÉE** ; garde clinique `DENY` obligatoire.
- Installation cabinet, disponibilité clinique, licence/droits de distribution : **NON AUTORISÉES** dans ce lot.

## Résultat d'exécution — Windows natif, première preuve acquise

[GitHub Actions run #42927150978](https://github.com/hraaaaf/Digital_crown/actions/runs/42927150978), HEAD exécuté `a7409d28ace00c2ed3970188f55a90420361cfdf` : **COMPLETED / SUCCESS**, job `actual-windows-frozen-witness` #130216387629 **SUCCESS**. Vérification des logs réels :

- `LOT08J_EXACT_SCOPE_AND_INSTALLABLE_SPEC_GATE_PRESERVED` : diff strict **3 fichiers**, `DigitalCrown.spec` inchangé, pas de certificat de distribution injecté.
- `LOT08J_GITHUB_SOURCE_METADATA_PIN_PASS` et `LOT08J_SOURCE_RUN_ARTIFACT_PIN_AND_REAL_MODEL_SELECTOR_PASS` : provenance de l'artefact ONNX officiel, sept fichiers, modèle réel et sélection à un seul modèle.
- `LOT08J_WINDOWS_REAL_ONEDIR_FROZEN_WITNESS_BUILT_NO_APP_NO_INSTALLER` : EXE PyInstaller Windows construit, distinct du produit.
- Ligne JSON de l'**EXE réellement exécuté** : `witness_os=win32`, `actually_frozen=true`, `model_embedded_in_frozen_bundle=true`, `model_size_bytes=267484931`, `model_sha256=a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`, `selected_models=1`, `clinical_gate_deny_production=true`, `clinical_gate_deny_even_lab_flags=true`, `model_inference_executed=false`, `patient_data_used=false`, `actual_digitalcrown_app_exe=false`, `installable_certified=false`, `clinical_release=false`.
- `LOT08J_TEST_PACKAGE_BYTE_TAMPERED_EXPECT_FROZEN_DENIAL` puis `LOT08J_REAL_WINDOWS_FROZEN_MODEL_HASH_DENY_AND_TAMPER_EVIDENCE_PASS` : copie du modèle altérée d'un seul octet, taille inchangée ; l'EXE est sortie en échec avec `MODEL_SHA256_MISMATCH`. 
- [Artefact metadata-only #13813364310](https://github.com/hraaaaf/Digital_crown/actions/runs/42927150978/artifacts/13813364310) : 626 octets compressés, **pas de poids ONNX ni EXE**. `LOT08J_RUNNER_MODEL_AND_SYNTHETIC_SCRATCH_CLEANED` confirme le nettoyage.

**Verdict :** l'objectif restreint `Windows frozen witness + hash réel + gate deny + tamper test` est **PROUVÉ**. La construction du vrai `DigitalCrown.exe` reste **NON VÉRIFIÉE ET BLOQUÉE** par `INSTALLABLE_CERTIFIED`. La validation anatomique des 38 points reste distincte ; aucune activation clinique.

**Handover exact :** conserver ce run et la méta-preuve, ne pas utiliser ce témoin comme preuve de release clinique. Next : code release certification + validation scientifique avant de pouvoir tester le packaging authentique de l'application selon ses gates.

