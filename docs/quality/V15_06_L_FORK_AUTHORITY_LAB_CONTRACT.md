# V1.5 / LOT06-L — Arbitrage de forks et autorité monotone VOLATILE (LAB)

## Objet et contrat de l'expérience

Un objet VolatileAuthority en mémoire représente la valeur courante TrustedAnchor (séquence, HMAC) pour une capture dont l'origine DC6A et l'identité sont vérifiées à la construction. Un Draft représente un append du journal HMAC 06-K conçu depuis une ancre observée, sans modifier l'autorité. La méthode compare_and_swap accepte le candidat seulement si sa séquence et sa MAC parent correspondent au head actuel, que le journal progresse exactement d'un événement valide, que le HMAC et les médias AEAD sont revérifiés, et que le scope de capture est identique.

Deux auteurs peuvent préparer séparément des candidats valides depuis la même ancre. Un seul candidat passe dans le modèle d'exécution séquentiel ; l'autre est refusé en tant que STALE_FORK et ne devient pas l'état lu. Les rollback sont représentés par un nouvel événement chaîné, jamais par une diminution de la séquence.

La lecture recover refuse tout journal local en avance, en retard, corrompu ou appartenant à une autre branche. Une interruption simulée après la préparation d'un journal mais avant l'avancement de l'autorité refuse le candidat. Inversement, une autorité avancée et un journal local perdu déclenchent un refus de reprise. Aucun auto-merge ou résolution de conflit hasardeuse.

## Limitations critiques et preuves négatives

**Aucune ancre persistante, indépendante ou matériellement monotone n'est créée.** VolatileAuthority peut être reconstruite depuis un ancien genesis et accepte alors l'ancien journal : un test explicite prouve cet échec de protection contre le rollback global. Les accès Python peuvent aussi manipuler ou cloner l'état. compare_and_swap n'est pas atomique entre processus ni entre machines, et n'effectue aucune transaction disque, fsync, sauvegarde, ou persistance de registre, service ou TPM. La clé HMAC est détenue dans le même processus que le simulateur ; aucune autorité distante ni séparation de privilèges.

Une future autorité réelle doit fournir un stockage durable monotone, scope par capture, des droits restrictifs, un compare-and-swap atomique et journal d'audit, une gestion/escrow/rotation des clés indépendante, une protection contre fork interprocess et rollback simultané de l'ancre et du journal, puis une procédure de réconciliation après panne vérifiée sur Windows et en cas de perte de connexion. Les décisions d'opérateur et associations patient restent conditionnées aux autres gates LOT06-B2/LOT04.

## Preuves et règles de portée

Tests synthétiques Windows/Linux sur SHA final : collisions de deux forks, ancien head, rejeu de suffixes, corruption HMAC/AAD, incorrect scope, faux draft, avance d'autorité avant publication du journal et inverse, rollback avec nouvel événement, et reconstruction dangereuse d'une autorité ancienne. Deux revues adversariales internes sur même HEAD et POST Notion.

Trois fichiers nouveaux LOT06 uniquement ; collecteur et CLI actifs inchangés, pas de service Windows, ni SQL, Vercel, master, LOT04/05 ou matériel. Statut : LAB-only, PR DRAFT, NO-GO clinique.
