# M4 final — matrice erreurs / retour / expiration

## Goal
Fermer M4 en certifiant que chaque contexte mobile de ressource échoue de façon explicite, sûre et compréhensible, sans fuite technique ni fallback trompeur.

## Succès observable
1. Non-pairé : état `Contexte indisponible` explicite, sans ressource inventée.
2. Permission révoquée : motif métier explicite, aucune donnée de ressource affichée.
3. Ressource supprimée/introuvable : état explicite, aucun fallback silencieux.
4. Backend cabinet inaccessible : message utilisateur français, aucune chaîne technique brute (`Failed to fetch`, `ERR_CONNECTION`, stack, URL interne).
5. Token expiré : claim refusé, jamais consommé après expiration.
6. Token déjà utilisé : second claim refusé.
7. Retour depuis un contexte valide : `/mobile/dashboard?tab=agenda` exact.
8. Contrôles visibles >=44 px et aucun overflow horizontal aux viewports certifiés.

## Cible UX pour backend inaccessible
Conserver la carte d'erreur existante et ses deux actions. Remplacer uniquement le détail technique par :

**Serveur du cabinet inaccessible. Vérifiez que le poste cabinet est démarré et accessible sur ce réseau, puis réessayez.**

Le bouton `Réessayer` relance la lecture. `Retour au mobile` revient à l'Agenda mobile. Aucun diagnostic réseau plus précis n'est affirmé sans preuve.

## Non-goals
- aucun redesign du shell mobile ;
- aucune nouvelle logique de fallback ;
- aucun changement au protocole opaque de bridge ;
- aucune modification des permissions ;
- aucun Vercel.

## Preuve requise
- BEFORE réel sur 390x844 et 768x1024 ;
- test backend expiration + usage unique ;
- AFTER sur les mêmes états/viewports ;
- absence de chaîne technique brute ;
- comparaison BEFORE → mockup → AFTER ;
- score visuel après inspection ;
- régression M4-A/B/C/D.
