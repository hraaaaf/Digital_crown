# Rollback rapide — données patients

Procédure minimale en cas de problème après un déploiement/mise à jour, quand
des vrais patients sont dans le circuit. Complète `docs/PREPROD_RUNBOOK.md`
et `docs/CABINET_ONPREM_GUIDE.md` (procédures complètes) — ceci est la
version "je panique, je fais quoi maintenant" à garder imprimée/accessible.

## 1. Arrêter l'application

- EXE (mode cabinet) : fermer la fenêtre / `Stop-Process DigitalCrown`
- Service NSSM : `nssm stop DigitalCrown`

## 2. Où sont les données actuelles

- DB : `%APPDATA%\DigitalCrown\clinical_vault.db` (SQLite/SQLCipher) OU
  `DATABASE_URL` PostgreSQL si mode avancé
- Médias : `%APPDATA%\DigitalCrown\media\`
- Clé de déchiffrement des backups : `CABINET_MASTER_KEY_HEX` — **conservée
  hors machine**, jamais dans ce dossier

## 3. Où est le backup

- `backend/backups/backup_<horodatage>.sql.enc` ou `.db.enc` (DB)
- `backend/backups/media_backup_<horodatage>.zip.enc` (médias)
- Copie hebdomadaire sur disque externe/USB (recommandé)

## 4. Restaurer la DB

⚠️ **Toujours sauvegarder l'état actuel AVANT de restaurer**, même cassé —
il peut contenir des données saisies depuis le dernier backup :
```
python -m backend.scripts.backup_db
```

Puis restaurer (⚠️ écrase la cible — jamais sans confirmation `--yes`) :
```
python -m backend.scripts.restore_db <backup.sql.enc> --yes
```

## 5. Restaurer les médias

Procédure manuelle (déchiffrement + extraction) — voir
`docs/PREPROD_RUNBOOK.md` §3 "Restore média".

## 6. Redémarrer

- Relancer l'EXE / `nssm start DigitalCrown`
- Vérifier `http://127.0.0.1:8005/api/health` → `status: ok`

## 7. Vérifier patients/documents

- Login avec un compte connu
- Ouvrir un dossier patient connu → vérifier que les données sont là
- Ouvrir un document/RVG connu → vérifier qu'il s'ouvre
- Comparer le nombre de patients affiché avec le dernier chiffre connu avant
  incident (si disponible)

## Règle d'or

**En cas de doute, ne touchez à rien et faites d'abord un backup de l'état
actuel.** Un état cassé mais sauvegardé peut toujours être diagnostiqué à
tête reposée. Un état écrasé sans backup préalable est perdu.
