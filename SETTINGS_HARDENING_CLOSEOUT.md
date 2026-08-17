# Settings Hardening — Closeout vérifié

Date : 2026-08-17
Repo : `hraaaaf/Digital_crown`
Base canonique : `ab5d559e3704d9a9cd361687f046b4d93b154937`

## Doctrine de preuve

Un lot n'est marqué fermé que si ses preuves requises ont été acquises sur le HEAD exact puis mergées. Aucun déploiement Vercel n'a été effectué pendant ce chantier.

## Lots fermés vérifiés

- S1 — baseline visuelle Settings : 70/70 captures, 0 erreur runtime.
- S4A — isolation tenant.
- S4B — catalogue tenant.
- S4C — init-status tenant-scopé/authentifié.
- S5A — mutations catalogue réservées à la permission `settings`.
- S5B — séparation opérations Agenda / configuration structurelle.
- S5C — RBAC frontend Settings ; secrétaire agenda-only sans surfaces admin. Certification visuelle réelle mobile : 9,4/10.
- S6 — Truth Layer de sauvegarde globale.
- S6B — préférences runtime IA committées seulement après persistance backend réussie. Certification visuelle réelle : 9,4/10.
- S7A — révocation mobile persistante, immédiate et tenant-scopée.
- S7B — vérité Sécurité/Backup, export via contrat de sauvegarde et libellés d'appairage corrigés. Certification visuelle réelle : 9,3/10.
- S12A — politique mot de passe 8..128 caractères sur les schémas concernés.
- S12C — mode cabinet fail-closed avant fallback SQLCipher faible ; CI #880 et T2 #158 SUCCESS sur HEAD `0d65b25cc06574abb1e1bac4221cbebc799de6dd`, merge `ab5d559e3704d9a9cd361687f046b4d93b154937`.

## Correctifs structurants validés

- Les surfaces Settings sont filtrées côté frontend selon RBAC réel.
- Les mutations structurelles Catalogue et Agenda exigent les permissions adéquates côté backend.
- Les réglages runtime IA ne deviennent durables qu'après succès backend.
- La révocation mobile invalide les accès existants selon le contrat tenant-scopé.
- Le flux Backup/Sécurité n'affirme plus un format SQLite quand le backend actif peut être PostgreSQL/SQLCipher.
- Le mode cabinet refuse les secrets crypto absents/faibles avant initialisation de la base.

## État documentaire

`ROADMAP.md`, `STATUS.md` et `CHANGELOG.md` ne sont pas présents à la racine au moment de ce closeout. Par conséquent, aucun nouveau pourcentage global n'est déclaré ici sans dénominateur canonique vérifiable.

## État de déploiement

Vercel : aucun déploiement effectué.
