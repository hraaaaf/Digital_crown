# TECHDOUBT — Digital Crown

## 2026-10-18 — CEPH-FAC-PARITY / P2TER-ATOMIC-ARCHIVE (étape 1/3)

Statut : **OUVERT / BLOQUÉ POUR MERGE ET CABINET**. Aucun changement produit `master` autorisé par cette entrée.

1. **Crash disque/SQL** : une panne `SIGKILL` après `open('xb')` et avant COMMIT peut laisser un PDF non indexé. Un audit **READ_ONLY**, un test à crash réel et le runbook `docs/clinic/CEPH_P2TER_POST_CRASH_ARCHIVE_AUDIT.md` ont été ajoutés à la PR #955 ; **ceci ne réalise pas la récupération automatique** et n'autorise aucune suppression ni rattachement d'archive patient.
2. **Gate trusted humain** : le `pull_request_target` exécute le code du `master` de confiance ; corriger le script seulement dans #955 serait inopérant. PR compagnon **#959 DRAFT**, tests de contrôle visuel anti-bypass, sera soumise à validation propriétaire. Tant que #959 n'est pas fusionnée avec autorisation, le code de confiance de la branche principale n'est pas corrigé. Aucune approbation `visual-approved-by-achraf` ne peut être ajoutée sans consentement explicite sur les captures exact HEAD.
3. **Base cabinet / preuves** : la migration SQLCipher a été répétée sur copie chiffrée **synthétique minimale**, pas encore sur sauvegarde/restauration d'une base existante de cabinet ; PG concurrence a été démontrée sur clone de contrainte, pas la totalité de l'API JWT sous PG.
4. **Clinical parity / release** : aucune équivalence numérique avec FACAD ni certification clinique. Aucun merge, déploiement ou installation. PR parent #953 DRAFT.

**Conditions de sortie** : 2 revues adversariales/confirmation sur le même HEAD ; CI required exact SHA verte ; audit post-crash documenté et modalités de reprise cabinet approuvées ; rehearsal sur copie restaurée de base cabinet avant installation ; approbation visuelle humaine légitime du HEAD exact ; conformité canonique et permissions de merge.
