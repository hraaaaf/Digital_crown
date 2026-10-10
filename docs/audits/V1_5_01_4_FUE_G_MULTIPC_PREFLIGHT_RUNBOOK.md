# Digital Crown V1.5-01.4 — FUE-G Multi-PC : runbook et protocole de preuves

**État : PREPARED / BLOCKED_HARDWARE / NON VERIFIED — vérifié le 2026-10-10.** Repo `hraaaaf/Digital_crown` ; [PR #803](https://github.com/hraaaaf/Digital_crown/pull/803) **MERGED** (la baseline historique du PRE était `25f15aef224d9e67a5075d9bac761594884855de`). Le HEAD de référence observé pour la préparation terrain est `master@8a12864a6a28753b3f0c666470f644e2010cfaa5`, issu de [PR #815](https://github.com/hraaaaf/Digital_crown/pull/815) ; il ne constitue **ni une release certifiée ni une installation terrain**. Le [handover PRE/GOAL Notion](https://app.notion.com/p/3f377c6633628187a51ee94a983d7267) reste canonique ; règles `AGENTS.md`, `STATE.md`, `.claude/rules/execution-scoring-verification.md` et `docs/CABINET_CERTIFIED_RELEASE_POLICY.md`.

## Goal

Installer **à partir de zéro** sur banc isolé autorisé un serveur S et deux postes annexes A/B réellement distincts. Attester, sur un vrai LAN, l'autorité serveur du bon cabinet, HTTPS :8005 et **chaîne de confiance TLS depuis A et B**, authentification, appairage propriétaire à usage unique, identité/permissions séparées, Hub et Station PIN, redémarrages S/A/B et restauration après coupure réseau sans fail-open, perte de données synthétiques ou fuite de tokens. Comparer BEFORE/AFTER aux mêmes étapes/personas/viewports, mesurer les durées réelles et obtenir la validation humaine.

## Gate 0 — Matrice PRE de disponibilité (lecture seule)

| REQUIRED avant toute installation | S | A | B |
|---|---|---|---|
| Machine isolée/autorisation, OS, navigateur, profil vierge | UNKNOWN | UNKNOWN | UNKNOWN |
| LAN/VLAN/IP ou DNS local, horloge, accès port 8005 | UNKNOWN | UNKNOWN | UNKNOWN |
| Cert SAN/CA/expiration et confiance TLS côté client | UNKNOWN | UNKNOWN | UNKNOWN |
| Propriétaire, identité, mode, rôle, PIN géré sûrement | UNKNOWN | UNKNOWN | UNKNOWN |
| Démarrage/reboot, approbation explicite et rollback | UNKNOWN | UNKNOWN | UNKNOWN |
| Backup DB+médias synthétiques + **restore isolé démontré** | UNKNOWN | N/A | N/A |
| Release **INSTALLABLE_CERTIFIED correspondant au produit exact testé** | UNKNOWN | N/A | N/A |

Au PRE, Desktop Commander présentait `DESKTOP-3MAJEEH` **OFFLINE**, aucun S+A+B observé. Aucune adresse/certificat/résultat matériel n'est inventé. **STOP** si un seul gate requis d'installation est inconnu ; les contrôles **pré-installation** peuvent inclure l'inventaire de la CA et du SAN prévus, mais le **handshake TLS effectif** sur A et B doit être testé **après démarrage de S**, avant toute authentification/appairage. « Go » préparation ≠ permission d'installer, redémarrer, couper le LAN, toucher une DB clinique ou activer un service.

**Frontière release** : l'historique PR #803 (désormais fusionnée) et le HEAD courant de `master` ne sont pas des binaires installables. La politique exige `CODE_CERTIFIED` produit sur le HEAD exact de `master` et assets attestés de **même SHA**, composition finale `INSTALLABLE_CERTIFIED`, hashes/manifest/signature et gate humain. Un ancien bundle V1 ne prouve pas les changements de #803. Interdiction d'utiliser HEAD/branche/master directement, EXE ad hoc, `uvicorn --reload`, contournement HTTPS `curl -k`, exception navigateur ou désactivation de guards. Les éléments de certification ne sont pas un certificat clinique/scientifique.

## Gate de traçabilité produit : code mergé versus installable
Le protocole est distinct en deux phases : **(1) vérifications code/laboratoire** sur un SHA exact et ses dépendances, puis **(2) FUE-G matériel** uniquement sur une release `INSTALLABLE_CERTIFIED` correspondant au code réellement évalué. **Impossible de revendiquer que le code déjà fusionné (#803 puis #815) a été éprouvé sur trois PC** en installant une ancienne release qui ne contient pas ses changements. Le simple merge n'atteste ni `CODE_CERTIFIED` ni `INSTALLABLE_CERTIFIED` ; tant que le bundle exact SHA n'est pas vérifié, le gate reste `BLOCKED_RELEASE_PARITY`. Ne pas effectuer un merge uniquement pour obtenir un score.

## Reprise terrain — observation du 10 octobre 2026 (aucune exécution sur matériel)

- **Cible de traçabilité documentaire :** `master@8a12864a6a28753b3f0c666470f644e2010cfaa5`. [PR #815](https://github.com/hraaaaf/Digital_crown/pull/815) MERGED, [master-push PostgreSQL/PowerShell #38005856102](https://github.com/hraaaaf/Digital_crown/actions/runs/38005856102) SUCCESS ; [Photo Lifecycle PR #38004636980](https://github.com/hraaaaf/Digital_crown/actions/runs/38004636980) SUCCESS sur son **ancien HEAD de PR**. Ces runs n'attestent ni `CODE_CERTIFIED`, ni `INSTALLABLE_CERTIFIED`, ni TLS/PC/webcam physiques.
- **Disponibilité réelle observée :** Desktop Commander liste uniquement `DESKTOP-3MAJEEH` **OFFLINE** (dernier contact ~83 h avant le contrôle). Aucun trio S+A+B simultanément accessible. Les identités machines physiques, OS, topologie LAN, CA/SAN clients A/B, confiance du certificat, release installable et backup/restore demeurent **UNKNOWN** ; les UNKNOWN du tableau Gate 0 restent inchangés.
- **Feu rouge vérifiable :** aucun déclenchement d'installation, release compose, reboot, migration, coupure réseau, transfert de credential ou simulation vendue comme preuve terrain ; **REQUIRED physiquement NOT RUN**. L'issue GitHub de suivi ne peut pas être créée actuellement car le repository a les Issues **désactivées (HTTP 410)** ; le présent document et le [handover Notion](https://app.notion.com/p/3f377c6633628187a51ee94a983d7267) servent de registre, sans inventer de numéro de ticket.
- **Déblocage en trois prérequis cumulatifs :** (1) opérateur met à disposition S et **deux** annexes réelles distinctes sur un banc d'essai isolé, avec OS/rôles/réseau et sans exposer de secret ; (2) une source immuable `INSTALLABLE_CERTIFIED` exact-SHA et son attestation d'assets est vérifiée ; (3) propriétaire autorise explicitement installation et, séparément, manipulations disruptives. En leur absence, poursuivre seulement vérifications code/contrat LAB sur une autre tâche FUE non dépendante du matériel.
- **Prochaine preuve attendue :** inventaire S/A/B avec horodatages/consentement, provenance de release, `BEFORE` réels et état TLS sur A et B ; ne pas remplacer le test de handshake réel par un diagnostic `tlsReady` ou un TCP `Test-NetConnection`. Garder les observations sensibles hors GitHub/Notion.

## Étapes et preuves BEFORE

1. Nommer S/A/B, environnement isolé, approbateur/opérateur, rôle topologique distinct du mode UX, versions, DNS/IP LAN constatées, routage/pare-feu, horodatage UTC. Sur machine Windows autorisée, `ipconfig /all`, `Get-Date`, `Test-NetConnection -ComputerName <DNS-local-S> -Port 8005` sont des contrôles **lecture seule**. La connexion TCP ne démontre pas la confiance TLS.
2. Sur **A puis B**, constater le certificat présenté et la validation native de SAN pour l'adresse réellement saisie, l'émetteur et les intermédiaires, les dates/horloges, la confiance CA et le refus si non valide. **Pas de -k, d'exception TLS ou de clé privée dans une capture**.
3. Contrôler release ID/code SHA 40 caractères, attestations GitHub/Sigstore, manifest/hash code et assets, rapport `INSTALLABLE_CERTIFIED`, correspondence binaire ; contrôler sauvegarde des fixtures synthétiques DB+médias et **restauration dans clone isolé**. Backup réussi seul = insuffisant.
4. Capturer BEFORE des profils vierges, Target attendu, états erreur et navigation : viewports applicables **390×844, 430×932, 768×1024, 1280×900**, texte 200 % si pertinent. Justifier les tailles non applicables. Secrets, PIN, JWT, données patient réelles exclus des logs/captures/Notion/GitHub.

## Parcours S → A → B (exécution **seulement après GO humain spécifique**)

1. **S** : installer uniquement le bundle certifié sur machine non clinique/DB PostgreSQL isolée. Configurer sur S `CABINET_HOST` = IP/DNS stable et réel, `CABINET_PORT=8005`, `DIGITALCROWN_ENABLE_HTTPS=true`, `DIGITALCROWN_TLS_CERT_FILE` et `DIGITALCROWN_TLS_KEY_FILE` protégés, `ALLOWED_ORIGINS` sans wildcard correspondant aux origines HTTPS réellement servies. Observer `/api/health`, `/api/health/db`, `/api/health/storage`, `/api/health/topology` ; aucun fichier env/secret ni token partagé.
2. **Annexe A**, profil vierge : découvrir/saisir `https://<nom-ou-IP-SAN>:8005`, confirmer le cabinet exact et sa chaîne TLS approuvée, refus avant autorisation, propriétaire habilité, appairage à usage unique, identité A, mode et accès Hub/Station PIN. Capturer sans code.
3. **Annexe B**, second profil vierge et autre machine : procédure réellement indépendante, nouveau code/identité B, permissions séparées ; constater simultanéité A+B et isolation entre identités, permissions, données et médias synthétiques. Un rôle descriptif topologique n'accorde aucun droit clinique.
4. **Négatifs** : mauvaise IP/segment, HTTP LAN, certificat non fiable/expiré/SAN faux, serveur arrêté, 503 service ou DB, 423 identité, Station PIN verrouillé, replay appairage. Vérifier UI avec action utile et accès fail-closed. Injecter des pannes **uniquement sur banc isolé avec accord distinct**.
5. **Récupération** : service restart S, reboot serveur et clients A/B, coupure LAN contrôlée puis restauration sous autorisation spécifique ; mesurer chronologie, temps réel d'indisponibilité et retour, états auth/Hub/Station, absence de rebond ou faux serveur indisponible, intégrité des fixtures et preuve rollback.
6. **AFTER** : mêmes machines/personas/états/viewports que BEFORE, comparer Target ↔ Render, focus/clavier/200 %, erreurs/console expurgées, compteurs/hashes des fixtures, nettoyage du seul banc ; classer P0/P1/P2 sans dissimuler le manque de preuve.

## Matrice de tests (aucun exécuté)

| ID | Oracle et résultat requis | Pièce matérielle exigée | Statut |
|---|---|---|---|
| S01 | S installable certifié, PostgreSQL isolé, HTTPS :8005 | SHA/manifeste + health/topologie + cert | NOT RUN |
| A01 | A neuve, bonne autorité, TLS, auth et pairing | AFTER + trace et identité A expurgées | NOT RUN |
| B01 | B neuve, appairage/identité distincts | AFTER + trace et identité B expurgées | NOT RUN |
| AB01 | A/B simultanées, isolation rôles/tenant/médias | refus positif/négatif et audit expurgé | NOT RUN |
| TLS01 | HTTP LAN/mauvais LAN/cert/SAN refusés | erreurs client sans bypass | NOT RUN |
| ERR01 | 503/DB/423/PIN/replay restent fail-closed | captures et tests négatifs | NOT RUN |
| RST01 | Restart S/A/B conserve identités/permissions | BEFORE/AFTER + temps mesurés | NOT RUN |
| OFF01 | Coupure/reconnexion cohérente | états dégradés/rétablis + temps | NOT RUN |
| DATA01 | Backup et restore clone, intégrité fixtures | compteurs et hashes synthétiques | NOT RUN |
| UX01 | Responsivité, focus, 200 % si pertinent | captures comparables | NOT RUN |

Par cas : timestamp UTC, release ID, code SHA réellement testé, machine/persona, étapes, attendu/observé, durée réelle, artifact sécurisé, anomalies P0/P1/P2, approbateur. Les runs historiques [01.1](https://github.com/hraaaaf/Digital_crown/actions/runs/37852925851), [01.2](https://github.com/hraaaaf/Digital_crown/actions/runs/37852925790) et [01.3](https://github.com/hraaaaf/Digital_crown/actions/runs/37852926051) sont **LAB ONLY**. Le [run rouge 03.6](https://github.com/hraaaaf/Digital_crown/actions/runs/37849251464) reste un gate distinct à classifier REQUIRED/EXPERIMENTAL/HORS SCOPE lors de la revue globale, pas un pass tacite.

## Chronométrie et registre matériel minimal
Pour chaque poste, enregistrer le même référentiel d'horloge, la version OS/navigateur, le numéro de scénario et la release exécutée. Capturer : **t0** (action/panne), **t1** (premier échec explicite), **t2** (réseau/service rétabli), **t3** (UI utilisable après authentification si requise) ; calculer indisponibilité et temps de récupération **à partir des observations**. Consigner les redémarrages S/A/B indépendamment, si l'identité et les permissions persistent, et une capture BEFORE/OFFLINE/AFTER par viewport applicable. Masquer identifiants, tokens, images et chemins sensibles. Ne pas fabriquer de SLO.

## Revue adversariale puis confirmation sur le même HEAD

**A — installateur / UX / reprise** : « Reconstitue S→A→B depuis zéro avec preuve matériel, étapes de pairing, états UI BEFORE/AFTER, 4 viewports si pertinents, a11y/200 %, reboot/coupure, mesures, rollback, anomalies. Trouve les omissions, contradictions, faux PASS mock, BLOCKER/MAJOR et dette. »

**B — sécurité / TLS / release / données** : « Reconstitue indépendamment code SHA et certification asset/installable, SAN/CA côté A et B, refus HTTP/cert incorrect, permissions et tenant isolation, replay/PIN/423, fuites tokens/PHI, restoration et fail-open. Trouve toute preuve manquante, risque patient, faux vert et dette cachée. »

Exécuter séparément les deux perspectives, corriger et re-tester ; tout nouveau HEAD impose deux nouvelles revues sur ce HEAD puis **passe de confirmation depuis zéro sur le même HEAD**. Si pas d'évaluateur indépendant, qualifier de **revues adversariales internes**, plafond 9.4. Scores sévères `EXECUTION_SCORE`, `ADVERSARIAL_SCORE`, `RETAINED_SCORE=min`, écart >0.5 investigué, preuve requise absente = plafond 7.9. `VERIFIED` nécessite ≥9, tous REQUIRED verts, 0 BLOCKER/MAJOR, Perfection Pass et validation humaine. Aucun merge/déploiement/installation n'est autorisé par cette page.

**NEXT EXACT** : identifier/autoriser S+A+B et leur réseau/TLS, obtenir la release `INSTALLABLE_CERTIFIED` exactement traçable au code sous test, capturer BEFORE réel ; en attendant `BLOCKED_HUMAN/HARDWARE` et **NON VERIFIED**.
