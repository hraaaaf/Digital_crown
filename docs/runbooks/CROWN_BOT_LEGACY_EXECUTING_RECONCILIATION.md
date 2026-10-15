# Crown Bot — rapprochement des anciennes actions `executing`

**État : opérationnel en lecture seule, PAS de reprise automatique.** La PR #894
ne doit pas être mergée ou activée pour clinique sans validation humaine.

## Pourquoi ce document est nécessaire

Les versions antérieures du Crown Bot enregistraient `executing` avant la
transaction métier. Après un crash, il est impossible d'inférer du seul statut
si le rendez-vous ou le changement de statut a été committé. Ces lignes
préexistantes ne doivent **jamais** être remises automatiquement à `pending`
ou réexécutées. Pour les nouvelles actions de la PR, un unique commit regroupe
l'écriture métier et la transition `executed`.

## Inventaire sans modification

Un utilisateur connecté peut consulter **ses propres actions**, au sein de son
cabinet, via `GET /api/bot/execute/reconciliation?limit=50`. Les résultats
contiennent uniquement action_id, type, dates, état `executing` et consigne
d'intervention ; ils ne révèlent ni paramètres du patient, ni données cliniques.
L'endpoint est volontairement READ-ONLY. Les autres utilisateurs et cabinets ne
sont pas énumérables par cet inventaire.

Le résultat `safe_to_retry=false` et `automatic_reset=false` est impératif,
même pour un `executing` ancien ou expiré.

## Procédure réservée à un opérateur habilité

1. Identifier l'action, son cabinet et son propriétaire, la période concernée et
   le type d'opération. Documenter l'identifiant d'action et l'heure.
2. Comparer **dans l'outil clinique existant**, avec droit d'accès, le dossier
   concerné et les rendez-vous ou statuts avant/après, les journaux et les
   sauvegardes lorsque disponibles. Une simple correspondance d'horaire ou
   d'homonyme ne prouve pas l'origine de l'écriture.
3. Si une preuve métier fiable existe, tracer la décision et la validation
   humaine avant tout changement de statut par procédure approuvée. L'API de
   cette PR ne fournit volontairement **aucun** endpoint de résolution mutable.
4. Si l'exécution reste incertaine, garder l'action bloquée, interdire le
   rejeu et escalader. Ne pas créer une nouvelle action équivalente pour
   contourner le blocage.
5. Confirmer séparément la cohérence des rendez-vous, des ressources occupées,
   du patient et de l'audit. Archiver une trace de clôture opérateur.

## Ce que les tests prouvent et ce qu'ils ne prouvent pas

- PostgreSQL : deux vraies sessions SQL sur tables synthétiques, conflit de
  réservation et rollback avant commit.
- SQLCipher : vrai fichier chiffré, deux connexions et rollback simulé,
  toujours sur schéma synthétique.
- API : tests FastAPI/TestClient avec SQLite mémoire, actions et tenants
  synthétiques.
- NON prouvés : le redémarrage d'un processus clinique réel sur toutes les
  plateformes installées ; l'attribution d'un ancien `executing` sans
  identifiant de transaction métier ; la sûreté de tous les chemins
  de création externes ; UX mobile/desktop avant/après.

Aucun reset automatique, aucun merge ni déploiement autorisé par ce document.
