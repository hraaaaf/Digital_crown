# V1.5-08.2-D / 08.4 — Contrat parallèle QR de présence & API Queue Core (PRE, 2026-11-10)

**Statut : contrat de conception isolé / DRAFT ; aucun QR réel, API nouvelle, service, migration ou intégration clinique créé par ce document.**  
**Base examinée :** `master@027a82aca4cc37308f6323e759283c4ca0e45fad`.  
**Indépendance :** 08.2-C Kiosk/Wall identity + 08.3 moteur transactionnel sont deux branches séparées, non fusionnées. La spécification 08.4 peut progresser parallèlement ; le check-in QR atomique 08.2-D ne peut être connecté avant les deux frontières.

## Réemploi strict : trois QR différents, aucun amalgame

1. **03.2 — Pairing Station** (déjà existant) : identification et gestion d'une Station clinique avec code HMAC à usage unique, tenant/appareil/administrateur. Les droits du futur Queue Kiosk/Wall et les certificats ne doivent pas absorber ni remplacer ce registre.
2. **03.3 — Handoff Patient QR/NFC** (déjà existant) : session Patient Companion de 120 secondes, liée à Station, transfert d'identité patient, **aucun ARRIVED**. Le Queue QR 08.2-D ne peut jamais porter un jeton Patient Companion, numéro patient ou dossier clinique.
3. **08.2-D — QR de présence autonome** (**non réalisé**) : secret opaque lié à une VISITE Queue Core de type `APPOINTMENT` déjà existante ; seul un Kiosk Queue appairé avec capacité `qr.redeem` peut en réclamer l'effet. Le Wall ne peut jamais consommer un QR.
4. **03.4 — Arrivée Station clinique** (existant) : `EN_S_ATTENTE` dans Agenda après identification patient et confirmation. Aucun calcul de ticket/rang. **LOT09** établira la correspondance idempotente entre Agenda et Queue Core sans écriture double non maîtrisée.

## Contrat sécurité 08.2-D — QR autonome

- **Émission :** Reception humaine autorisée, tenant/queue/visite retrouvés dans la base serveur ; permission `qr.issue`, statut de VISITE autorisé (`PLANNED` ou `EN_ROUTE`), `VisitKind.APPOINTMENT` obligatoire. Le client ne fixe pas le tenant.
- **Secret :** `secrets.token_urlsafe(32)` ou équivalent CSPRNG ; lien/QR opaque sans nom, patient, contact, date de naissance, RDV clinique ni informations de soins. Stockage persistant **empreinte** uniquement (SHA-256 avec séparateur de domaine dédié), jamais le bearer dans les logs, audit, journaux SSE ou exceptions. La recherche d'empreinte est serveur et au scope cabinet.
- **Expiration :** 15 minutes par défaut, réglable **5 à 30 min** après configuration validée ; comparer l'expiration côté serveur, jamais l'horloge du navigateur.
- **Réémission :** invalide l'ancien code non consommé dans **la même transaction** ; au plus un code utilisable par VISITE au même instant ; contrainte SQL et contention à démontrer dans 08.3.
- **Consommation :** sous verrou/transaction unique avec 08.3 : 1) identité Kiosk authentifiée et active (08.2-C), 2) capacité `qr.redeem`, tenant/queue/visite égaux aux enregistrements serveur, 3) code ni expiré, ni révoqué, ni consommé, 4) visite APPOINTMENT et état autorisé au **moment** de l'exécution, 5) version/CAS et position séquentielle déterminée **côté serveur**, 6) écriture consommation + version visite + `ARRIVED` + `WAITING_ENTERED` avec même horodatage/acteur/méthode `KIOSK_QR`, commit unique.
- **Rollback :** toute erreur (DB, version, session révoquée, duplicate, perte de connexion avant commit) laisse intacte la visite et les deux événements ; après commit, réponse perdue = retry idempotent associé à la même tentative, sans second ARRIVED/position. Aucun « exactly once » réseau promis.
- **Interdits :** walk-in QR, NO_SHOW réentrée autonome, `queue.call`, `queue.chair`, `queue.done`, `queue.override` ou administration via Kiosk ; refus générique cross-tenant, sans existence de visite divulgable.
- **Audit :** résultat minimal et expurgé (actor device opaque, tenant, version/état autorisés) ; ne pas inclure secret QR ni identité patient.
- **Aucune activation** avant preuve de persistance isolée, reprise après crash et absence de collision de bases cliniques ; migrations critiques soumises au gate humain.

## Contrat 08.4 — API autonome, non implémentée ici

- REST **versionné `/v1`** / OpenAPI ; formes précises des routes et enveloppes réponse/erreur à geler après lecture du transport HTTP/SSE de 08.2-B. Le préfixe est un contrat, **pas une preuve d'existence d'une route**.
- Toute mutation nécessite authentification tenant-scopée, droits de la ressource, version attendue et **idempotency key** unique par acteur/tenant/commande, rétention de déduplication **7 jours** ; même clé + payload divergent = refus, jamais écriture silencieuse.
- Les erreurs ne divulguent ni identité, ni patient, ni détails de tenant externe. Cas 401/403/409/429/503 vérifiés par tests négatifs. `NO_SHOW` seulement humain, `CHAIR` et `DONE` séparés, override explicitement autorisé avec motif.
- **SSE + snapshot** : notifications en lecture seulement, `Last-Event-ID` et reprise dans la fenêtre de rétention, un contrôle d'autorisation nouveau à chaque message/heartbeat, refus immédiat après révocation ; toute mutation reste REST. Aucune donnée clinique directe.
- **Webhooks sortants** : LAN HTTPS / TLS vérifié, destinataires autorisés, HMAC-SHA256 et timestamp/nonce, rejets d'horodatage ou signature non conformes, retries bornés depuis une outbox durable *après commit*, prévention SSRF/DNS-rebinding / destinations privées non explicitement autorisées ; aucune confiance accordée à un webhook entrant non authentifié.
- G3 : les durées d'audit/retenue, purges, sauvegardes et restauration restent des obligations d'exécution distinctes (pas prétendues réalisées par une documentation). Données visit identifiables 30 j après clôture, audit minimisé 12 mois, logs opérationnels 7 j, backups 7 quotidiens + 4 hebdos selon politique préexistante, sous validation juridique appropriée.
- Sans Internet WAN : le moteur fonctionne localement ; jamais de dépendance Firebase pour les commandes Queue. Firebase reste séparé pour l'authentification/licence Digital Crown selon la politique projet.

## Matrice de FUE à exécuter plus tard

| Cas négatif ou comportement | Oracle bloquant |
| --- | --- |
| Deux scans simultanés même QR | une seule transaction peut consommer, un seul couple ARRIVED/WAITING |
| QR expiré, révoqué, ancien après réémission | zéro arrivée / zéro événement |
| Kiosk révoqué pendant transaction, mauvais tenant ou queue | 401/403 générique et zéro écriture |
| Wall tente un redeem QR, Kiosk tente action Staff | 403, zéro écriture |
| Walk-in, NO_SHOW, DONE, CANCELLED | QR rejeté ; reprise NO_SHOW humain seulement |
| Crash avant commit / erreur insertion événement 2 | aucune consommation partielle, aucun ARRIVED isolé |
| Timeout réponse après commit puis retry idempotent | même résultat sans second événement |
| Concurrent check-in staff et QR | une seule transition gagnante, pas deux numéros de rang |
| Client falsifie `queue_sequence`, tenant ou version | jamais autorité, rejet ou résolution serveur |
| SSE ouvert avant révocation puis heartbeat / retry | fail-closed, pas de flux réservé ultérieur |
| Webhook signature invalide / cible hostile / retry | pas de livraison non autorisée, journal outbox intact |
| Redémarrage et restauration labo | résultat déterministe sans double ticket, sans données patients |

## Critères de jonction / gates

**C + 08.3 seulement après FUE-0 et FUE-I exact-head :** identité durable, droits Kiosk/Wall, retour de révocation, chargement serveur complet sous verrou, commit atomique et rejeu. **08.2-E** teste ensuite le parcours lié. **08.5–08.6** sont l'acceptation standalone FUE-G et résilience ; **LOT09** est le raccord clinique Digital Crown, **LOT10** les appareils physiques. Aucun QR de présence n'est utilisable dans la clinique à la date de ce document.

**NO_GO invariant :** zéro patient réel, zéro migration, zéro installation, zéro déploiement, zéro modification de `master` depuis ce document. Ne pas confondre la validation de ce contrat documentaire avec une réussite de runtime.
