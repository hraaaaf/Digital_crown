# Crown Bot — certification clinique préalable aux revues finales

**Statut du gate : REQUIRED / OUVERT jusqu'aux preuves CI exact HEAD.**
**Séquence ordonnée et impérative :** certification clinique réelle -> seulement
après succès, trois revues adversariales FINALES sur un unique HEAD immuable.
Les anciennes revues internes ne sont pas des approbations indépendantes.

## Portée des contrôles

| Voie de mutation | Sémantique | Garde de réservation |
| --- | --- | --- |
| Agenda POST /appointments | RDV confirmé / prévu | verrou tenant + contrôles canonique |
| Agenda PUT /appointments/{id} | déplacement/praticien/ressource | verrou tenant avant conflits |
| Agenda POST /appointments/bulk | plusieurs RDV en une transaction | verrou tenant avant validation totale |
| Crown Bot POST /bot/execute | RDV après confirmation utilisateur | claim+RDV+audit+executed, commit unique, verrou tenant |
| Mobile legacy POST /appointments | RDV depuis Pocket | délégation à validation canonique, praticien explicite pour personnel non praticien |
| Patient Companion create/reschedule | créneau opaque, patient autorisé | verrou tenant avant double-check+claim de slot |
| Frontdesk confirm | une demande devient confirmée | verrou tenant, revalidation ouverture et collisions |
| Frontdesk appointment-request | demande non confirmée, sans praticien | **ne pas présenter comme réservation médicale confirmée** |

La validation d'ouverture/fermeture partage le moteur Agenda existant. Il
retourne actuellement `None` si la table ou les réglages cabinet sont
manquants : cette politique historique peut être fail-open et DOIT être
résolue/encadrée avant toute déclaration de sûreté clinique complète.
Le format d'heure local et les données patient identifiées seulement par
un nom partiel doivent aussi être encadrés.

## Tests REQUIRED de la PR

1. Gate clinique avec vrais modèles ORM de l'app (SQLite mémoire CI) :
   chevauchement mobile, bulk, update, frontdesk, jour fermé, exception cabinet ;
   suites de non-régression praticien/ressources/companion/accueil.
2. **Vrai PostgreSQL 16 migré Alembic** : appel des routes FastAPI HTTP
   avec deux connexions/sessions concurrentes, une réservation + une réponse
   409, fermeture réelle, création /bot/execute, vérification audit, statut
   executed et refus du replay. Base fictive de CI.
3. **Vrai SQLCipher chiffré sur disque, schéma clinique migré Alembic** :
   mêmes scénarios HTTP via le véritable driver cabinet, vérification
   `PRAGMA cipher_version`; jamais accepter SQLite clair comme substitut.
4. Tests de crash, concurrence et anti-replay sur schéma SQL synthétique déjà
   verts avant ce lot ; utiles mais *insuffisants* à eux seuls.

## Éléments empêchant « CONVERGED »

- Un rouge REQUIRED / HTTP 5xx / données inter-tenant / double RDV,
  même si les tests synthétiques passent.
- Des voies de création, confirmation et import non couvertes par un contrôle
  de verrou équivalent.
- Une politique fail-open de l'agenda quand les réglages sont absents,
  une attribution ambiguë du patient, ou une confirmation qui produit un
  succès trompeur.
- Absence de tests BEFORE/AFTER du parcours utilisateur réellement exposé
  sur desktop et mobile, s'il est inclus dans la décision de livraison.
- Absence de deux revues propres sur même HEAD. Les trois finales ne sont
  lancées **qu'après** certification clinique REQUIRED complète et concluante.

**Interdit sans autorisation explicite :** merge PR, activation du flag,
déploiement Vercel, données réelles, modification de l'instance clinique.
