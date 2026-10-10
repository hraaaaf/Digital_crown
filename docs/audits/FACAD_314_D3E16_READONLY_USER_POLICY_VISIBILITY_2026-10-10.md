# FAC-03 D3E.16 — Diagnostic Windows de visibilité de politique par utilisateur

**Date :** 2026-10-10. **Statut :** lecture seule, **aucune activation de politique**, aucune capture Ilexis ni Facad. **FAC-03 D3 OPEN/RED**.

## Base vérifiée

Le commit D3E.15a `c9877769c56022128ce8c7da62bcf4340ddffe7f` a produit une [CI source-only verte 412/412](https://github.com/hraaaaf/Digital_crown/actions/runs/38083183793) et un [run Windows read-only vert](https://github.com/hraaaaf/Digital_crown/actions/runs/38083183751). Ce run a trouvé `system_success_audit_status=success_not_configured`, `per_user_inclusion_success_audit_status=unavailable`, `auditpol_user_query_succeeded=false`. Ces informations **ne permettent pas** de conclure que la politique par utilisateur n'existe pas ou n'est pas configurable ; elles indiquent seulement que la requête n'a pas abouti sur le runner interrogé.

Documentation Microsoft : [auditpol get](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/auditpol-get) accepte `/user:{SID}`, `/subcategory:{GUID}`, et `/category:*`, avec retour CSV possible `/r`. [auditpol list](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/auditpol-list) accepte `/list /user /v /r` pour énumérer les **comptes disposant d'une politique explicite**. Cette dernière commande peut exposer en sortie brute d'autres identités : seule une comparaison privée en mémoire contre le SID courant est acceptable dans ce test.

## Trois observations distinctes sans mutation

1. `auditpol /list /user /v /r` : le script lit la liste dans la RAM du runner jetable, la borne (nombre de lignes et longueur) et vérifie si le SID de **l'utilisateur courant** y apparaît **exactement**. La liste et le SID ne sont jamais loggés, mis en artefact ni transmis à Notion. Résultat autorisé : `exact_current_sid_seen`, `not_seen_in_successful_listing`, ou `undetermined` lorsque la liste n'est pas disponible.
2. `auditpol /get /user:{SID courant} /subcategory:{GUID File System} /r` : seul le statut anonymisé de la commande est enregistré (`zero`, `nonzero` ou `unavailable`).
3. `auditpol /get /user:{SID courant} /category:* /r` : même principe, autre portée de sélection pour distinguer une limitation liée à une sous-catégorie d'un refus général de lecture.

**Point épistémique** : un SID absent d'un inventaire lisible signifie uniquement « aucune entrée explicite de ce SID n'est apparue dans cette liste ». Cela ne prouve pas que la politique est inexistante à tous les niveaux, ni que son activation serait impossible, sans danger ou pertinente. Un code `nonzero` est **inconclusif** (pas une preuve de désactivation ou de restriction administrative).

Le script n'exécute aucun `auditpol /set`, `auditpol /restore`, `auditpol /clear`, aucune lecture de journal Security, aucun ETW, aucun traitement d'ACL ni d'objet du patient. Il n'utilise les chemins GitHub qu'afin d'écrire deux fichiers JSON agrégés, sans nom utilisateur, SID, chemin source, PID, registre, hash, sortie native ni message d'exception.

## Revue adversariale interne

**A. Sécurité et confidentialité : 7,5/10 pour le protocole (provisoire avant run natif).** La limitation à des commandes de consultation évite la mutation de la politique de sécurité et la collecte ETW, mais **`auditpol /list /user /v` lit en RAM une liste de politiques de comptes**, potentiellement plus large que l'utilisateur courant. Le confinement de cette sortie reste un critère strict. Blocage immédiat si fuite dans logs ou artefacts, si modification de politique, ou si un programme se met à consulter les ressources Ilexis.

**B. Qualité de la preuve : 6/10 pour le diagnostic de configuration, 2/10 pour l'attribution Ilexis.** Les deux variantes GET et le listing peuvent distinguer un état non listé d'un échec générique, mais ne prouvent ni réception d'événements 4663 ni capacité de configuration future. Aucun écrivain, aucune causalité et aucune isolation partagée validés. Deux perspectives **internes**, **aucune revue indépendante** ; `CONVERGED=false`.

## Critère observable et suite

Pour clôturer **uniquement D3E.16** : CI sur SHA exact avec tests source-only et exécution Windows read-only rapportant ses trois statuts, validateur strict, aucune donnée privée diffusée. La suite dépend de ces états : si la politique individuelle du runner n'est pas visible, éviter de répéter la même commande ou d'activer `auditpol` sans autorisation. Examiner une autre voie d'attribution à périmètre démontrablement sûr.

**Invariants : `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `CLINICAL_EDIT_ALLOWED=false`, D3 OPEN/RED, aucun merge, aucun déploiement.**