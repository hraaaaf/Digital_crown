# V1.5 / LOT06-K — Journal de migration authentifié simulé

Portée : bibliothèque **LAB uniquement**, purement en mémoire, compatible avec les snapshots synthétiques 06-J. Ni installation, ni migration sur disque, ni patient, ni SQL.

## Modèle et garanties dans les limites du LAB

Chaque Record immuable inclut séquence (1..256), HMAC précédent, snapshot 06-J et HMAC-SHA256 du manifeste canonique. Le manifeste lie domaine/version, séquence, chaînage précédent, cabinet, poste, identifiant de capture, digest, phase, révision, key_id et empreintes des bytes source/candidat. Une clé HMAC de 256 bits **distincte** de la clé DC6A legacy et des clés DC6B cible est obligatoire. Ni clair ni clés sont écrits dans le manifeste ; les données restent en mémoire dans le checkpoint objet.

Chaque enregistrement est comparé à son HMAC **avant** la vérification/décryption AEAD du média ; aucune entrée modifiée n'est traitée comme un checkpoint valide.

Le journal exige SOURCE (révision 0), puis transitions autorisées SOURCE -> PREPARED -> VERIFIED -> COMMITTED ou rollback explicite de PREPARED/VERIFIED/COMMITTED -> ROLLED_BACK -> PREPARED. Le blob source est immuable, les conditions de scope et de progression sont revalidées, comme les authentifications AEAD 06-I/J. La phase VERIFIED/COMMITTED ne peut altérer le candidat déjà authentifié. Le rollback est un nouvel événement authentifié, jamais une suppression du suffixe.

**Protection anti-rejeu conditionnelle** : tout verify_chain exige une TrustedAnchor indépendante (séquence et MAC de tête) correspondant exactement au journal. Si une ancre actuelle est conservée par un tiers fiable, toute troncature, permutation, altération ou replay d'un vieux journal est bloqué. **LIMITATION CRITIQUE** : la TrustedAnchor n'est ici qu'un objet Python fourni par l'appelant, non persistant, non authentifié, non monotone et non protégé du rollback. Un acteur qui restaure ENSEMBLE journal et ancienne ancre peut rejouer sans détection. Le LAB ne fournit donc pas de preuve anti-rejeu réelle.

## Scénarios et crash recovery

Avant publication du Record : journal/ancre anciens, reprise possible. Après nouvelle publication du Record, avant avancement d'ancre : divergence détectée, lecture **refusée** en attendant une réconciliation autorisée, non implémentée. Après avancement des deux objets en mémoire : reprise simulée sur état vérifié. Aucune transaction atomique entre ces deux objets, aucune récupération automatique ni acceptation fail-open d'un journal « en avance » n'est permise.

## Critères réels encore BLOQUANTS — NO-GO

Avant mise en service : ancre monotone indépendante durable et autorisée, secret HMAC DPAPI/escrow et rotation de key_id, WAL/journal sur disque avec fsync fichier et dossier, atomicité NTFS et SQLite après coupure électrique, verrouillage lecteurs multi-process, protocole de réconciliation sûr, transition comparée via CAS réellement persisté, protection anti-replay des backups, audit signé/autorisation humaine, contraintes d'identité patient et ACK B2, tests Windows sur vrai poste/driver.

Tests de laboratoire Windows et Linux sur SHA final ; deux revues internes adversariales sans prétendre à l'indépendance externe. Aucun merge, déploiement, changement du collector/CLI actif, SQL, LOT04/05, appareil clinique ni activation.
