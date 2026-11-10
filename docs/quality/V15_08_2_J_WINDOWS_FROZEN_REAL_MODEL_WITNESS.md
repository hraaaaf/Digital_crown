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

**Status initial :** protocole préparé ; CI Windows et preuves réelles non acquises tant que le run du HEAD exact n'a pas réussi.
