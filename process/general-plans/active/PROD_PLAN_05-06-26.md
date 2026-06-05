# DIGITALCROWN - PLAN DE MISE EN PRODUCTION (PROD-READY)

**Date** : 05 Juin 2026
**Statut** : DRAFT (En attente de validation)
**Type** : Infrastructure & Sécurité

---

## 1. Objectifs de la Phase de Production
Passer l'application DigitalCrown d'un environnement de développement local à un environnement d'exécution de production hautement disponible pour un cabinet médical (LAN-First).
L'objectif est d'assurer :
- La sécurité absolue des données médicales (PHI) via ZKA.
- La résilience hors-ligne (LAN-First).
- La pérennité et la récupération des données (Backups).

---

## 2. Débats Pré-Mise en Production (Rapport vc:predict)

### Verdict: CAUTION ⚠️
*Le système est robuste fonctionnellement, mais l'architecture LAN-First déplace le fardeau de la disponibilité sur le matériel du cabinet.*

### Résolution des Conflits (Les 5 Personas)

| Persona | Point de Vue | Risque Soulevé | Résolution / Action Requise |
|---------|--------------|----------------|-----------------------------|
| **Architecte** | L'app tourne sur la machine locale du médecin. Si le PC redémarre, qui relance les serveurs ? | *Indisponibilité post-redémarrage* | Créer des services Windows (ou utiliser PM2) pour lancer PostgreSQL, FastAPI et le Frontend au démarrage. |
| **Sécurité** | Le ZKA et la caméra mobile exigent un contexte cryptographique sécurisé. | *Blocage de l'Onboarding Scanner* | Forcer le HTTPS localement (certificats auto-signés ou reverse proxy Caddy) et strict CORS `allow_origins`. |
| **Performance** | FastAPI tourne avec `--reload` et les logs saturent le disque dur. | *Fuite de mémoire et I/O saturé* | Démarrer Uvicorn en mode production (`workers=4`), supprimer `--reload`. |
| **UX** | Si l'IP du PC serveur change (DHCP dynamique), le mobile ne pourra plus s'y connecter le lendemain. | *Rupture de l'Appairage Mobile* | Configurer une IP LAN Statique pour le PC hébergeur sur le routeur du cabinet. |
| **Avocat du Diable** | Si le PC prend feu ou le disque dur lâche, le cabinet perd tout son historique patient. | *Perte Totale de Données (Catastrophe)* | Implémenter un script `pg_dump` quotidien avec upload chiffré vers un Cloud ou disque dur externe. |

---

## 3. Feuille de Route (Roadmap - Étape par Étape)

### ÉTAPE 1 : Verrouillage Sécuritaire & Environnement
- [ ] Générer de nouveaux secrets cryptographiques forts pour `.env` (`JWT_SECRET`, etc.).
- [ ] Désactiver le mode debug/reload dans FastAPI.
- [ ] Configurer les origines CORS strictes (ex: autoriser uniquement l'IP statique du serveur local).
- [ ] Configurer HTTPS en local (via mkcert ou Caddy) pour garantir le fonctionnement du ZKA et des caméras mobiles.

### ÉTAPE 2 : Persistance & Lancement Automatique (Infra LAN)
- [ ] Fixer l'adresse IP locale du PC serveur sur le routeur du cabinet.
- [ ] Configurer un gestionnaire de processus (PM2 ou Service Windows) pour lancer :
    - La base de données PostgreSQL.
    - Le backend FastAPI (`uvicorn main:app --host 0.0.0.0 --port 8000`).
    - Le frontend Vite (`npm run preview` ou un serveur statique Nginx/Caddy).

### ÉTAPE 3 : Stratégie de Résilience & Backup (Le point critique)
- [ ] Écrire un script automatisé (Batch/PowerShell) de `pg_dump` quotidien.
- [ ] Automatiser l'envoi de ces sauvegardes vers un emplacement sécurisé hors-site (Cloud chiffré ou NAS local).

### ÉTAPE 4 : Tests Finaux In-Situ (Le "Crash Test")
- [ ] Test de redémarrage : Redémarrer le PC serveur et vérifier si l'app est accessible sur le réseau après 1 minute.
- [ ] Test ZKA Mobile : Réaliser un appairage complet depuis un téléphone sur le réseau Wi-Fi local avec la nouvelle IP fixe.
- [ ] Test de bascule Offline : Couper la connexion internet du routeur, ajouter un patient, rebrancher internet, vérifier la synchronisation.

---
*Ce plan est prêt à être exécuté dès validation de l'ordre de priorité.*
