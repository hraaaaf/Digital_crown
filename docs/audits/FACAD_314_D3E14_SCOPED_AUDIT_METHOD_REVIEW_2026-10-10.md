# FAC-03 D3E.14 — Comparaison des mécanismes de traçage mieux circonscrits

**Date :** 2026-10-10. **Statut :** EXPERIENCE SYNTHETIQUE UNIQUEMENT, aucun essai Ilexis autorisé par ce lot. **D3 : OPEN/RED**.

## Problème à résoudre

D3E.13 (HEAD edd38ff1e4a3cd3d85679a2f3956721837097d1b ; [source CI 331/331](https://github.com/hraaaaf/Digital_crown/actions/runs/38081577373)) a identifié un risque bloquant de confidentialité : le provider ETW Microsoft-Windows-Kernel-File surveille des activités d'autres objets de la machine. Même un filtrage local et un nettoyage intégral de l'ETL ne prouvent pas un confinement à Ilexis.

D3E.11 a révélé deux fichiers dont la taille change dans les bras SACL pré-lancement (une modification par bras), zéro dans les témoins passifs, et **aucun événement 4663** sur ces fichiers. Mais les règles SACL effectives étaient héritées et confirmées dans D3E.11, sans preuve que la sous-politique Windows File System Success Audit ait été effectivement activée, ou que le fournisseur Security 4663 livre ses événements pour cet objet.

## Alternatives examinées (non équivalentes)

| Mécanisme | Portée du capteur | Information de processus | Risque/limites | Décision D3E.14 |
| --- | --- | --- | --- | --- |
| Kernel File ETW `0x280` | Système entier | PID associé à un événement et FileObject en mémoire | Collecte globale avec chemins et autres processus possibles ; pertes de flux, événement pas égal à écriture complétée | **Ne pas relancer sur Ilexis** |
| SACL d'objet File System + Security 4663 | Déclenchement conditionné aux objets/SID/droits explicitement audités, mais le journal Security Windows reste partagé | Champ Process ID dans 4663 ; type d'accès WriteData/AppendData | Dépend de la politique d'audit, des privilèges et de la livraison ; SACL peut elle-même modifier les métadonnées | **Tester le fonctionnement sur un fichier synthétique isolé** |
| FileSystemWatcher .NET | Dossier surveillé uniquement | Aucun PID | Perte possible d'événements et absence de causalité | Garder comme contrôle complémentaire |
| Journal NTFS USN | Volume NTFS entier | Pas d'attribution PID fiable par entrée | Large portée, observateur de changements, pas auteur | Non sélectionné |
| Sysinternals Procmon / minifilter | Capture potentiellement large, filtre d'affichage ≠ confinement garanti | Certains noms/PID et opérations | Conducteur et traces potentiellement sensibles ; dépendances et droits plus invasifs | Non sélectionné |

Sources de référence Microsoft : [Audit File System](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/audit-file-system) et [événement 4663](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4663). Microsoft précise qu'un événement n'est généré qu'avec une SACL pertinente et une politique d'audit en vigueur ; l'événement 4663 documente notamment Process ID et les droits WriteData/AppendData. **4663 ≠ confirmation que l'écriture est terminée ni attribuable avec certitude au changement ultérieur de taille.**

## Expérience autorisée par ce commit

Un seul runner Windows jetable, **sans aucune installation de Facad** : création sous RUNNER_TEMP d'un fichier synthétique, pose de SACL Success WriteData/AppendData uniquement sur CE fichier pour le SID utilisateur du runner, vérification des ACE en lecture, processus enfant Python/PowerShell écrivant une valeur artificielle, lecture bornée et filtrée par intervalle du journal Windows Security pour l'événement 4663, comparaison des champs ObjectName, AccessMask et ProcessId **uniquement en mémoire**.

La politique d'audit globale est interrogée en lecture seule (`auditpol /get`) et n'est jamais modifiée. Si elle n'est pas activée ou si l'accès au journal Security échoue, la calibration reste **inconclusive**, et jamais « aucun écrivain ». L'absence d'événements n'autorise aucun assouplissement.

Aucun ETL/EVTX/XML, aucune collecte globale ETW, aucune écriture réelle Ilexis, aucun Load/Save patient. La règle SACL initiale est restaurée et le dossier synthétique détruit dans un `finally`, avant export des JSON agrégés ; tout échec de nettoyage arrête le job. Les événements Security bruts, chemins, noms, PID, hash, tailles ou horodatages individuels ne sortent pas du runner.

Un validateur JSON strict rejette les métadonnées sensibles et les affirmations `write_completion_proven`, `real_ilexis_writer_proven`, `shared_app_storage_isolation_verified` ou `clinical_edit_allowed`. **Un workflow vert n'est pas une preuve que 4663 a été reçu.**

## Perspectives adversariales internes — pas de revue indépendante externe

**A — confidentialité : 8/10 de design**, sous réserve de la validation native. Le capteur basé sur SACL est conditionné à un fichier précis, sans étendre auditpol ni interroger des objets d'application. Limite : le journal Security est toujours global et pourrait avoir des données non liées pendant l'interrogation ; aucun événement brut ne doit être exporté. Erreur SACL/restauration = BLOCKER.

**B — validité de preuve : 5/10 de design, 2/10 d'attribution Ilexis.** La comparaison avec D3E.11 ne permet pas de conclure sans calibration réelle : SACL présente peut ne pas produire 4663 si politique de succès désactivée, privilèges insuffisants ou journal inaccessible. Un match synthétique prouve une possibilité de provenance, pas l'identité de l'écrivain Ilexis ni une isolation.

**Critère pour une étape suivante :** obtenir des événements synthétiques 4663 pour le bon objet et PID sous Windows et/ou diagnostiquer proprement leur absence, puis revoir indépendamment les implications de politique d'audit et de confidentialité. Aucune capture Ilexis autorisée par le présent lot.

**État immuable :** `FAC-03 D3 OPEN/RED` ; `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED` ; `CLINICAL_EDIT_ALLOWED=false` ; `CONVERGED=false`. Aucun merge ni déploiement.
