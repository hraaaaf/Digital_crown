# FAC-03 D3E.13 — Protocole préalable et revue de sécurité d'une attribution ETW Quick-demo

**Date :** 2026-10-10. **Statut :** DESIGN ONLY / LIVE CAPTURE BLOCKED. **Branche expérimentale :** `feat/cephalo-facad-direct-parity-runtime-probe`. **Lot :** D3E.13. **Sans merge, sans Vercel, sans patient Load/Save.**

## 1. Résultat de référence, sans surinterprétation

D3E.12d a démontré la faisabilité **sur un fichier synthétique** : commit `35c7798d2a8c7ee9d2c05e89ffabff6ea2e0468b` ; [CI source-only, 289/289](https://github.com/hraaaaf/Digital_crown/actions/runs/38079398080), [run Windows synthétique](https://github.com/hraaaaf/Digital_crown/actions/runs/38079398064). Les sorties filtrées du run Windows indiquent `Microsoft-Windows-Kernel-File` keywords `0x280`, `direct_etl`, un événement Write associé par `FileObject` à l'unique fichier sentinelle et au PID du processus enfant artificiel, et une suppression confirmée des traces brutes. Aucun enregistrement réel Ilexis n'a été capturé, aucune opération d'écriture n'est certifiée *complétée*, et la complétude ETW n'est pas démontrée.

Les essais D3E.11 sur Quick-demo ont observé 0 modification de taille avant lancement dans les deux bras passifs et 1 dans chacun des deux bras SACL, avec signal `FileSystemWatcher` et règle d'audit héritée présente sur le fichier modifié. **L'écrivain, sa causalité, et l'isolation restent inconnus.**

## 2. La limite de confidentialité est un BLOCKER de capture

La session `Microsoft-Windows-Kernel-File` est **globale à la machine**, et ses événements peuvent contenir des chemins, handles, PID, noms et métadonnées d'activité non liée à l'exemple Robert. Le simple fait de filtrer ensuite sur `AppData/Roaming/Ilexis` **ne rend pas le fichier ETL brut exempt de données externes**.

Le run éphémère GitHub Windows ne doit jamais être assimilé à une preuve de confinement du fournisseur ETW. Une publication d'ETL, d'EVTX, de XML, de dump de processus, de `Get-WinEvent.ToXml()`, de chemins/PID/hashes/fichiers individuels dans GitHub Actions ou Notion serait bloquante. Les données de patient réelles, configurations de licence, profils et registres applicatifs sont hors périmètre.

Sources externes : [ETW — Microsoft](https://learn.microsoft.com/en-us/windows/win32/etw/event-tracing-portal), [metadata ETW](https://learn.microsoft.com/en-us/windows/win32/etw/event-metadata-overview), [tracing et précautions de sécurité](https://learn.microsoft.com/en-us/windows/win32/wsw/tracing), [manifest Microsoft-Windows-Kernel-File (microsoft/Tx)](https://github.com/microsoft/Tx/blob/master/Generated/Microsoft_Windows_Kernel_File.cs). Ces références expliquent la portée et les risques ; elles ne prouvent pas la sécurité du runner spécifique.

### Contrôles obligatoires avant toute autorisation ultérieure

1. Réévaluer la nécessité d'une trace globale avant de l'activer : privilégier un observateur **scopé par mécanisme** ou un environnement parfaitement jetable et isolé ; si le risque de capture d'activité étrangère n'est pas suffisamment maîtrisable et revu, **STOP**.
2. Scoper explicitement un éventuel essai à la Quick-demo officielle Robert, copiée localement et autorisée, sur des runners Windows propres et indépendants ; **aucun dossier patient réel**, aucune inspection de licence, de profil ou de registre. La provenance du binaire et du jeu de données doit être contrôlée avant l'expérience.
3. Vérifier exact HEAD, provenance, signature/empreinte des scripts, portée des dossiers, jetabilité du runner, privilèges minimaux et absence de secrets additionnels. Refuser tout chemin non conforme, reparse point ou symlink.
4. Si et seulement si la capture est autorisée, prévoir : capture avant lancement Facad (maximum théorique 8 s), keyword mask fixe `0x280`, ETL circulaire plafonné 12 Mo et au plus 20 000 événements ; aucun élargissement silencieux, aucune augmentation de limites XML par défaut.
5. Garder en mémoire volatile la correspondance `Create/FileObject/Write/PID` et les *métadonnées* avant/après. **Aucune identité fichier/PID/horodatage précis n'est transférée, loggée ni persistée sous forme agrégée réversible.** Rejeter événements incomplets, ambiguïtés FileObject réutilisé, doublons, fenêtre temporelle douteuse, perte d'événements, lecture partielle ou trace saturée.
6. Séparer les observations : *notification de modification*, *write event ETW*, *PID associé à un événement*, *modification effective de taille/horodatage*, et *auteur causal*. Les quatre premières **ne démontrent pas automatiquement la cinquième**. Un événement ETW Write ne prouve ni le succès d'IO ni la persistance des octets.
7. Arrêter ETW dans un `finally` même si le scénario échoue ; supprimer intégralement ETL/EVTX/XML/dumps et fichiers temporaires AVANT toute publication ; échec cleanup = échec du job, **pas une suppression « presumée »**. Masquer stdout/stderr des commandes natives ; aucun upload `if: always()` ne doit ramasser de fichiers de trace.
8. Une sortie publique future doit être strictement autorisée par schéma, uniquement agrégée, bornée, sans faibles cardinalités ré-identifiantes si combinées à d'autres métadonnées ; aucun PID, nom de processus rare, chemin, hash, identifiant fichier, taille ou date exacte. Le gate ne peut jamais déclarer `CLINICAL_EDIT_ALLOWED=true`.
9. Exiger une revue de **confidentialité indépendante réelle** et une revue de **validité de preuve indépendante réelle**, documentées, sur le même HEAD et avec des preuves natives ; les deux perspectives de la présente note sont **revues internes** et ne satisfont pas ce critère. Autorisation préalable distincte pour une capture sur stockage partagé après passage des revues.
10. N'activer aucune capture si l'un de ces critères manque. Maintenir `FAC-03 D3 OPEN/RED`, `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `CLINICAL_EDIT_ALLOWED=false` même en cas de CI entièrement verte.

## 3. Design de l'expérience **future**, non exécutée par D3E.13

**Question falsifiable** : un éventuel événement ETW Write attribuable à un PID apparaît-il dans la fenêtre *pré-lancement Facad* pour **le même objet temporaire** que le fichier dont les métadonnées changent, sans événement correspondant dans les bras témoins ?

Le protocole proposé utilise 4 installations Quick-demo jetables et indépendantes (2 témoins passifs ; 2 instruments SACL), même chemin de préparation, mêmes captures autorisées, même limite de durée, même masque de keywords et même phase de métadonnées ; seul le traitement SACL diffère. Ordre/horodatage fixés dans le protocole avant exécution ; aucun cherry-picking. Ne pas prétendre causalité SACL sans indépendance des autres variables et exclusion explicite des effets d'instrumentation.

**Preuves minimales attendues** : (a) fichier initial/prélaunch et final comparé par métadonnées et identité uniquement en RAM ; (b) ETW capture réussie avec métriques de perte et de saturation connues ; (c) liaison non ambiguë `FileObject` et un write-event/PID à une fenêtre, puis vérification que l'objet est réellement le fichier changé ; (d) nettoyage vérifié ; (e) répétition contre factuelle. Si la source des événements est globale, la sécurité de cette collecte doit faire l'objet d'une preuve et d'une autorisation avant tout point (b).

**Arrêts obligatoires** : ETW provider/manifest différent, PID insuffisant/incohérent, FileObject réutilisé, timestamps hors fenêtre, segments manquants, compteur cap atteint, absence de vérification des pertes, erreur de lecture, signal seulement SACL/FSW, cleanup incertain, fichier de trace brut accessible aux artefacts, atteinte potentielle à la confidentialité. Tous => **INCONCLUSIF + D3 RED**.

## 4. Livrables effectifs de D3E.13

- `docs/audits/FACAD_314_D3E13_CAPTURE_READINESS_CONTRACT.json` : contrat fermé, `phase=DESIGN_ONLY`, preuve synthétique D3E.12d référence, risques ETW explicités, *tous* les indicateurs d'approbation, de causalité, de capture réelle et d'isolation à `false`.
- `scripts/facad_314_d3e13_capture_readiness_gate.py` : validateur Python hors ligne qui refuse champs supplémentaires, types trompeurs, revendications d'autorisations et branchements natifs. **Son succès ne permet jamais une capture**.
- `scripts/test_facad_314_d3e13_capture_readiness_gate.py` : deux groupes de tests adversariaux source-only (confidentialité et preuve/autorisation).
- CI source-only de la branche : vérification du contrat et des tests. **Aucun collecteur D3E.13 natif, aucun workflow Windows de capture Ilexis, aucun nouveau run Facad déclenché par ce lot.**

### Revues adversariales — deux perspectives INTERNES, non indépendantes

**A — Confidentialité : 7/10 pour le design, bloquant pour l'exécution.** Le périmètre est limité au design et les champs d'export sont contrôlés, mais ETW demeure une collecte globale susceptible d'enregistrer des chemins externes. Aucune attestation de confinement du runner ni revue indépendante réelle.

**B — Validité de preuve : 5/10 pour le design, 2/10 pour l'attribution réelle.** Le protocole distingue correctement événement de write, PID du fournisseur, notification, dérive de métadonnées et auteur causal. Cependant D3E.12d ne confirme qu'un seul essai synthétique ; ne donne ni pertes ETW prouvées, ni complétion de write, ni corrélation à l'Ilexis réel. La branche reste `CONVERGED=false`.

**Verdict final du lot :** un **protocole auditable et un verrou source-only**, pas un feu vert de capture ou d'isolation. Les étapes non validées restent ouvertes. **Aucune capture D3E.13 ne doit être exécutée à la suite de cette note seule.**
