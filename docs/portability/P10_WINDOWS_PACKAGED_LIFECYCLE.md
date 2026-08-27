# P10 — Windows Packaged Lifecycle Candidate

Status: ACTIVE / candidate. 0 EP credited.

## Goal

Certifier un cycle Windows packagé current → next via le moteur P10 existant et le packaging P6.

## Contract

- le manifeste signé est vérifié pendant la préparation puis vérifié de nouveau juste avant l'apply ;
- le job doit correspondre exactement à la version, la séquence, l'OS, l'architecture, le nom, la taille et le SHA-256 de l'installateur ;
- Windows auto-apply reste limité au package Inno amd64 certifié ;
- le rescue SQLCipher et sa checksum sont revérifiés ;
- la clé backup existante est obligatoire ;
- les workers PowerShell 5.1 sont externalisés hors du dossier programme avant mutation ;
- un échec de lancement du worker reste failed_pre_apply et ne modifie pas le package.

## Benchmark

Le workflow dédié construit le package courant et le package patch suivant, installe le courant, vérifie VERSION et /health, prépare l'update avec un manifeste Ed25519 éphémère de CI, lance le worker externe, puis exige :

- status health_pending ;
- package self-test exact sur la nouvelle VERSION ;
- DisplayVersion Inno exact ;
- /health avec DB ok ;
- conservation du sentinel de données cabinet ;
- artifact de preuve avec job, logs et rapports self-test.

## Limites

P10 reste ouvert. Restent notamment P7 macOS, les drills d'échec packagés, la gestion de confiance de production et le closeout cross-platform.

No Vercel.
