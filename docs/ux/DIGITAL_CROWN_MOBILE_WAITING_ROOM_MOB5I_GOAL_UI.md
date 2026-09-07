# DIGITAL CROWN — MOB-5I Salle d’attente — Goal UI

## Goal
Rendre la salle d’attente réellement exploitable sur mobile à partir du modèle Appointment canonique existant, sans dupliquer le métier ni inventer de données.

## Succès observable
- le mobile distingue `EN_SALLE_ATTENTE` de `PLANIFIE` ;
- un rendez-vous peut passer de `PLANIFIE` à `EN_SALLE_ATTENTE`, puis `EN_FAUTEUIL`, puis `TERMINE` depuis le flux mobile autorisé ;
- la vue mobile affiche les patients actuellement en salle d’attente avec leur heure de RDV et `ticket_number` quand présent ;
- aucune métrique de temps d’attente n’est affichée tant qu’aucun timestamp d’arrivée canonique n’est prouvé ;
- tenant scope et permission `agenda` restent imposés côté serveur ;
- aucun nouveau modèle/table ;
- aucun débordement horizontal aux viewports 390×844, 430×932 et 768×1024 ;
- score visuel >= 9/10.

## Référence UX livrée
Surface mobile clinique compacte, centrée sur l’état opérationnel du patient :
1. compteur Salle d’attente ;
2. liste des patients présents ;
3. ticket quand disponible ;
4. action explicite `Au fauteuil` ;
5. accès secondaire dans `Plus` sans remplacer l’Agenda ni ajouter une sixième destination principale.

## Preuves Goal → résultat
- BEFORE run `34168710412` — SUCCESS ;
- AFTER/cert run `34169388445` — SUCCESS ;
- artifact AFTER `10035225974` ;
- digest `sha256:efa961010bb3c1d189f8447c99a70d5dfaf42c893f49fd8a4db558b5dbccbd50` ;
- backend contract SUCCESS ;
- frontend contract SUCCESS ;
- frontend build SUCCESS ;
- 390×844 / 430×932 / 768×1024 : HTTP 200, 0 page error, 0 console error, 0 overflow ;
- Salle d’attente, compteur, patient, ticket `#12`, CTA `Au fauteuil`, entrée `Plus` et badge présents ;
- score visuel certifié : **9.3/10** ;
- PR `#367` mergée ;
- merge exact `e2522a6d8b4794e64253eb4af36500e18cd87b40`.

## Hors périmètre maintenu
- nouvelle table de file d’attente ;
- estimation du temps d’attente ;
- timestamp d’arrivée reconstruit depuis l’heure du RDV ;
- notifications patient ;
- déploiement Vercel.

## Post-merge
- run master `34170398551` ;
- état au moment de cette mise à jour : `pending`.

Statut : `GOAL DELIVERED — PRODUCT MERGED — POST-MERGE PENDING`.
