# FAC-03 D3E.17 — Revue adversariale des alternatives d'attribution confinée

**Date :** 2026-10-10. **Périmètre :** recherche d'architecture et contrôle CI source-only, sans nouvelle capture Windows, sans accès Ilexis ni données patient, sans politique auditpol modifiée, sans installation de pilote et sans déploiement. **Verdict : DESIGN ONLY ; NO SAFE CAPTURE CLEARED.**

## 1. Contexte canonique vérifié dans les preuves GitHub

- **D3E.11** : dans deux bras SACL pré-lancement Quick-demo, dérive de taille de 1 fichier et notification FileSystemWatcher, 0 dans les deux témoins ; SACL héritée présente ; **aucun événement Security 4663**. Cela ne révèle ni le processus responsable ni la causalité de Set-Acl. [Essais Windows #38061805750](https://github.com/hraaaaf/Digital_crown/actions/runs/38061805750).
- **D3E.12d** : avec un **fichier synthétique seulement**, un événement de type Write ETW a été relié à un FileObject et à un PID enfant dans un runner éphémère, 1 correspondance dans un essai. La capture ETW Kernel-File n'est pas limitée au fichier et l'essai ne prouve pas un Write complété. [Windows synthétique #38079398064](https://github.com/hraaaaf/Digital_crown/actions/runs/38079398064).
- **D3E.14–16** : sur un runner Windows, la politique File System Success Audit n'était pas configurée ; sous D3E.16, la liste des politiques d'audit individuelles était lisible mais **le SID courant n'y figurait pas**, et les deux requêtes `auditpol /get /user` échouaient. C'est un résultat de visibilité sur **ce runner**, non une preuve que la politique est impossible à configurer ou qu'un écrivain n'existe pas. [CI #38086797632](https://github.com/hraaaaf/Digital_crown/actions/runs/38086797632) **449/449**, [Windows #38086797658](https://github.com/hraaaaf/Digital_crown/actions/runs/38086797658), HEAD de référence `eb9f2c2bd316ef85ff91e76759f293e869fec655`.

**Problème restant :** obtenir une observation permettant d'attribuer une écriture au bon objet **sans aspirer des métadonnées du système hôte ou des données hors scope**. Réduire les sorties publiques à des agrégats ne suffit pas si la collecte brute reste globale.

## 2. Alternatives comparées — état réel, non hypothétique

| Solution | Portée **à la source** | Événement écrivain / PID | Dépendances et risques bloquants | Score sévère de préparation au contexte (/10) |
| --- | --- | --- | --- | --- |
| **ETW Kernel-File actuel** | Hôte entier, `0x280` limite les types, pas les chemins | Liaison FileObject/PID **synthétique** démontrée une fois | ETL brut peut contenir des chemins, PID et activités non liées ; pertes non exclues | **3/10** |
| **ETW filter PID EnableTraceEx2** | Filtre par processus selon le fournisseur et les modalités | **Non démontré pour Kernel-File**, en particulier pour activité de noyau | La documentation PID filter indique une portée user-mode ; ne **pas** transposer à Kernel-File sans preuve fournisseur | **2/10** |
| **SACL objet + 4663** | Déclenchement conditionnel à la SACL de l'objet ; **journal Security partagé** | PID d'accès documenté, mais 4663 absent dans les essais | Politique File System Success non configurée sur runner ; modification d'audit globale ou par utilisateur interdite sans revue/accord | **3/10** |
| **FileSystemWatcher** | Dossier surveillé | **Aucun PID** ; notification ≠ écrivain | Perte de notification possible ; aucune causalité | **1/10** |
| **Sysmon** | Service/driver hôte, filtres sur types d'événements journalisés | FileCreate lié à l'image/processus, pas une preuve générale des écritures complétées de fichiers existants | Installation/portée collecteur et rétention d'autres activités ; règles de filtre ≠ confinement prouvé | **2/10** |
| **Pilote minifilter FltMgr** | Callback noyau pour opérations sur des volumes, restriction logique des objets possible | Observe I/O et peut différencier pre/post-operations **par conception**, pas prouvé dans ce produit | Driver signé, installation, altitude FltMgr, privilèges noyau, crash/régression du système, validation indépendante indispensable | **3/10** |
| **Procmon** | Instrumentation système, filtres d'affichage ou de collecte à auditer | Événements processus/fichier utiles potentiellement, pas certifiés ici | Trace potentiellement globale, driver/sensibilité, licence et contrôle du périmètre non validés | **2/10** |
| **VM Windows autonome / Windows Sandbox à image jetable + ETW synthétique** | ETW reste **global dans l'invité**, mais pas sur le Windows hôte si l'invité est vraiment isolé | Liaison synthétique possible ; attribution Quick-demo non réalisée | Ne pas partager host mounts, réseau, presse-papiers ni secrets ; pureté guest, intégrité demo et effacement à prouver | **6/10 pour la voie de revue**, **0/10 pour une capture réelle aujourd'hui** |

**Les scores sont des évaluations internes de préparation**, pas des garanties de sûreté. Aucun des huit mécanismes n'est aujourd'hui **certifié** pour capturer l'écrivain Ilexis avec un confinement suffisant.

### Sources Microsoft vérifiées (faits extérieurs à Digital Crown)

- [ETW sessions et EnableTraceEx2](https://learn.microsoft.com/en-us/windows/win32/etw/configuring-and-starting-an-event-tracing-session) ; [EVENT_FILTER_DESCRIPTOR](https://learn.microsoft.com/en-us/windows/win32/api/evntprov/ns-evntprov-event_filter_descriptor) : les filtres de PID existent, mais le comportement d'activation est dépendant du mode/provider ; **ne pas supposer** que Kernel-File bénéficie d'un filtre de fichier ou d'un PID limitant toute la collecte.
- [Audit File System](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/audit-file-system) ; [événement 4663](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4663) : les règles SACL, la politique d'audit et l'accès effectif se combinent ; un événement ne prouve pas l'écriture persistée des octets.
- [Sysmon configuration](https://learn.microsoft.com/en-us/windows/security/operating-system-security/sysmon/sysmon-configuration-files) : les règles configurent les événements journalisés et leurs critères de sélection, pas une preuve automatique de confinement d'un moniteur noyau.
- [Minifilter callbacks](https://learn.microsoft.com/en-us/windows-hardware/drivers/ifs/registering-preoperation-and-postoperation-callback-routines), [enregistrement](https://learn.microsoft.com/en-us/windows-hardware/drivers/ifs/registering-the-minifilter-driver), [installation/signature](https://learn.microsoft.com/en-us/windows-hardware/drivers/ifs/creating-an-inf-file-for-a-minifilter-driver) : pilotes hautement privilégiés et besoin d'une validation spécifique.
- [Windows Sandbox (configuration)](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file) : les options réseau, dossiers hôte mappés, presse-papiers et vGPU exposent des surfaces de partage. Le défaut réseau peut être activé, et des dossiers hôte peuvent être montés en lecture/écriture ; **une VM isolée ne se présume pas**.
- Les comparaisons avec Procmon et FileSystemWatcher s'appuient sur leur mode de fonctionnement général : ce lot n'a pas réalisé de benchmark Windows de ces deux outils ni démontré leur capacité d'attribution.

## 3. Décision D3E.17 : privilégier un **modèle de menace de l'invité**, pas une capture

**Recommendation : `ISOLATED_GUEST_SECURITY_REVIEW_ONLY`**. Ce choix minimise **potentiellement** les données étrangères susceptibles d'être capturées, mais **ne transforme pas ETW en collecteur par fichier**. Aucune VM ou Windows Sandbox dédiée à cet essai n'a été créée, exécutée ou contrôlée dans D3E.17.

Conditions à satisfaire avant de solliciter **séparément** l'autorisation d'un essai ultérieur :
1. Invité Windows réellement indépendant, jetable, sans dossiers hôte montés, profil utilisateur réel, connexions cloud, licence ou secrets de production, réseau/presse-papiers désactivés lorsque possible, absence de vGPU si non indispensable ; preuve des réglages guest sur l'image concernée.
2. Provenance des binaires et jeux de données Quick-demo **officiels et non cliniques**. Ne jamais recopier de répertoires patients, licences ou configurations privées. Aucune opération de patient Load/Save.
3. Collecte ETW brute gardée dans l'invité uniquement ; aucune projection/récupération de chemin, SID, PID, nom de fichier, hash, date ou taille individualisée. Éviter les agrégats de cardinalité faible identifiants. Nettoyage vérifié et suppression effective de la VM.
4. Contrat causal préalablement fixé : une correspondance événement Write + FileObject + PID + fenêtre temporelle et une dérive metadata **ne démontrent pas** à elles seules une écriture réussie et persistée. Vérifier la complétude des événements, les handles réutilisés et les erreurs/erreurs de flush avant d'émettre un diagnostic ; fail-closed si ambigu.
5. Deux **vraies revues indépendantes** sur le même HEAD (confidentialité de la collecte et validité de la preuve), sans BLOCKER/MAJOR, plus approbation explicite distincte pour un éventuel essai. Ce lot n'effectue **aucun de ces contrôles**.

### Gates et bornes d'exécution

Le JSON de décision `docs/audits/FACAD_314_D3E17_CAPTURE_METHOD_DECISION.json` maintient **toutes** les cases d'autorisation à `false`. Le gate Python `scripts/facad_314_d3e17_capture_method_decision_gate.py` vérifie par correspondance stricte 8 profils de mécanismes, 12 prérequis guest, 17 statuts non prouvés, et l'absence de tout workflow D3E.17 de capture réelle. La CI teste les altérations, faux claims, méthodes oubliées ou périmètres élargis.

**Le succès du gate signifie uniquement : « analyse cohérente, pas de capture autorisée ».** Aucun collector natif D3E.17, aucun nouveau run Windows Facad.

## 4. Revue adversariale interne (deux angles, NON indépendante réelle)

**Perspective A — sécurité/confidentialité, score 7/10 sur qualité de la revue, BLOCKER live.** Le périmètre source-only est explicite et le gate interdit de qualifier un mécanisme dangereux comme sécurisé par une simple déclaration. **BLOCKER** : confidentialité de la capture brute hors-scope dans l'invité non évaluée sur un environnement réel, provenance des données et absence de host mounts non vérifiées. Risque de ré-identification via compteurs agrégés non démontré nul.

**Perspective B — validité de la preuve, score 6/10 sur méthode d'analyse et 2/10 sur attribution réelle, BLOCKER live.** La distinction entre notification, événement d'accès, événement Write, écritures complétées et dérive est maintenue. **BLOCKER** : pas de donnée native Windows Quick-demo attribuant la dérive à un processus, pas d'exhaustivité ETW, pas de contrôles causaux indépendants. Le test positif synthétique D3E.12d ne ferme pas D3.

Ces deux perspectives sont **internes**. Pas de reviewer extérieur, pas de deux revues propres sur même HEAD et preuves natives ; **`CONVERGED=false`**.

## 5. Prochain lot proposé

**D3E.18 — Threat model / préflight isolé** : établir un dossier d'architecture VM ou Windows Sandbox **sans l'exécuter**, une matrice des sorties autorisées, une preuve attendue d'absence de répertoires hôte montés, et le plan des deux revues indépendantes. La validation d'une configuration statique ne vaudrait pas validation runtime ; ne jamais utiliser les runners GH Windows actuels comme preuve qu'une VM nested est disponible.

**État final : FAC-03 D3 OPEN/RED ; SHARED_APP_STORAGE_ISOLATION=UNVERIFIED ; CLINICAL_EDIT_ALLOWED=false ; aucun merge/déploiement, pas de patient Load/Save.**
