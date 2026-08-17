# Settings Hardening — Closeout vérifié

Date : 2026-08-17
Repo : `hraaaaf/Digital_crown`
Base canonique : `622c6b0e7a40ee50879454baf61175e3c82d5705`

## Doctrine de preuve

Un lot n'est marqué fermé que si ses preuves requises ont été acquises sur le HEAD exact puis mergées. Aucun déploiement Vercel n'a été effectué pendant ce chantier.

## Lots fermés vérifiés

- S1 — baseline visuelle Settings : 70/70 captures, 0 erreur runtime.
- S2 — local-first patient/Firebase.
- S3 — backup SQLCipher restaurable/vérifiable.
- S4A — isolation tenant.
- S4B — catalogue tenant.
- S4C — init-status tenant-scopé/authentifié.
- S5A — mutations catalogue réservées à la permission `settings`.
- S5B — séparation opérations Agenda / configuration structurelle.
- S5C — RBAC frontend Settings ; secrétaire agenda-only sans surfaces admin. Certification visuelle réelle mobile : 9,4/10.
- S6 — Truth Layer de sauvegarde globale.
- S6B — préférences runtime IA committées seulement après persistance backend réussie. Certification visuelle réelle : 9,4/10.
- S6C — thème Branding prévisualisé sans persistance locale avant vérité backend ; responsive conservant l'UI existante. Certification visuelle réelle : 9,5/10.
- S6D-A — Agenda + Catalogue : échec de lecture explicite, aucune fausse valeur par défaut ni mutation sur donnée non chargée. Certification visuelle réelle : 9,5/10.
- S6D-B — Profil + Équipe : échec de lecture explicite, aucune fausse valeur fallback/équipe vide, mutations bloquées tant que la source n'est pas vérifiée. CI #960, T2 #227, Profile/Team Visual #3, IA #5, RBAC #34 SUCCESS sur HEAD `1d826b491b7f9d24a8a359f792194c532149a00f`. Certification visuelle réelle : 9,5/10. Merge `622c6b0e7a40ee50879454baf61175e3c82d5705`.
- S6D-C — Journal d'Audit : panne API distincte d'un historique réellement vide. Certification visuelle réelle : 9,5/10.
- S7A — révocation mobile persistante, immédiate et tenant-scopée.
- S7B — vérité Sécurité/Backup, export via contrat de sauvegarde et libellés d'appairage corrigés. Certification visuelle réelle : 9,3/10.
- S12A — politique mot de passe 8..128 caractères sur les schémas concernés.
- S12B — lecture licence fail-closed sur erreur DB ; aucune mutation sans preuve positive.
- S12C — mode cabinet fail-closed avant fallback SQLCipher faible ; CI #880 et T2 #158 SUCCESS.
- P1-3 — whitelist stricte `CabinetConfigUpdate` contre mass-assignment.
- P1-4 — détection doublons patients tenant-scopée.

## Correctifs structurants validés

- Les surfaces Settings sont filtrées côté frontend selon RBAC réel.
- Les mutations structurelles Catalogue et Agenda exigent les permissions adéquates côté backend.
- Les réglages runtime IA et le thème Branding ne deviennent durables qu'après succès backend.
- Une panne de lecture Settings n'est plus présentée comme une configuration réelle vide ou par défaut sur Profil, Agenda, Catalogue, Équipe et Journal d'Audit.
- La révocation mobile invalide les accès existants selon le contrat tenant-scopé.
- Le flux Backup/Sécurité n'affirme plus un format SQLite quand le backend actif peut être PostgreSQL/SQLCipher.
- Le mode cabinet refuse les secrets crypto absents/faibles avant initialisation de la base.
- L'état licence échoue fermé si sa lecture DB est indisponible.
- Les écritures cabinet sont protégées contre les champs non autorisés et les recherches de doublons sont isolées par tenant.

## Re-audit final

- Upload logo, upload papier-en-tête, suppression logo et suppression papier-en-tête : mutations backend-first avec succès affiché uniquement après réponse positive.
- Sécurité mobile et Backup : erreurs explicites ; aucune lecture permanente supplémentaire ne transforme une panne en état métier vide.
- `switchCabinet()` reste présent dans `useSettingsStore` comme logique locale suspecte, mais aucun appelant actif n'a été démontré dans les surfaces Settings auditées. Il est consigné comme dette/cleanup non bloquante, pas comme bug utilisateur prouvé.
- Aucun autre gap fonctionnel Settings actif n'a été démontré lors du re-audit final.

## État documentaire

`ROADMAP.md`, `STATUS.md` et `CHANGELOG.md` ne sont pas présents à la racine. Le pourcentage global historique n'est donc pas recalculé sans dénominateur canonique exhaustif ; la fermeture fonctionnelle ci-dessus repose uniquement sur les lots et preuves listés.

## État de déploiement

Vercel : aucun déploiement effectué.
