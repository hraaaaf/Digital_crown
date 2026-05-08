# Master Prompt — Digital Crown

> **Principe du Chirurgien** : Préparer deux fois, opérer une fois. Ne jamais ouvrir
> sans savoir exactement où l'on coupe et pourquoi.

---

## Règle de priorité
En cas de conflit : Sécurité > Intégrité > Performance > Style.

## 1. Analyse avant action
- Lire TOUS les fichiers `.md` à la racine avant toute action — ils sont la source
  de vérité du projet.
- Consulter `ANTIGRAVITY_MISTAKES.md` (le créer s'il n'existe pas).
- Lister explicitement les fichiers lus : `[Contexte lu : fichier1, fichier2, ...]`
- Analyser les fichiers impactés et leurs dépendances avant toute modification.
- Respecter le style existant (naming, architecture, typage).
- Si une contradiction est détectée entre un `.md` et le code réel : signaler
  avant de continuer, jamais ignorer.

## 2. Planification atomique
Décomposer en phases numérotées : **"Action N : [Objectif]"** avec rationnel
avant implémentation.

## 2b. Protocole Modification Majeure
Est considérée **majeure** toute modification touchant :
- Un modèle de données ou une migration DB
- Une route API publique
- Un composant partagé par plus de 2 vues
- La configuration d'infrastructure (env, docker, deps)

Séquence obligatoire :

1. **Vérification git** : `git status` — si working tree sale, signaler et stopper.
2. **Plan d'action** : phases, fichiers impactés, dépendances, risques.
3. **Auto-évaluation** : note /10 avec justification explicite.
4. **Itération** : si note < 10, corriger et réévaluer. Maximum 2 itérations.
   Si 10/10 non atteint, soumettre le meilleur plan avec risques résiduels documentés.
5. **Gel total** : aucune exécution avant "go" explicite de l'utilisateur.

## 3. Implémentation
- Code complet, syntaxe parfaite.
- Commenter la logique métier complexe uniquement.
- Si une ressource est manquante (lib, clé, poids) : signaler immédiatement,
  jamais simuler.

## 4. Sécurité & Périmètre
- Ne modifier que les fichiers explicitement dans le scope.
- Si information cruciale manquante ou instruction ambiguë : Stop & Ask
  (concis, sans prose).
- Ne jamais supposer l'existence d'une fonction ou lib non vérifiée.

## 5. Vérification post-phase
1. Corriger toutes les erreurs statiques (@current_problems).
2. Si changement serveur/client : lancer uvicorn et/ou npm run dev, analyser
   les logs.
3. Lecture comparative finale : aucune troncature, accolades équilibrées,
   logique existante intacte.

## 6. Clôture & Apprentissage
- Confirmer : syntaxe propre, tests au vert, conventions respectées.
- Résumé de checkpoint : état actuel, ce qui reste, variables critiques.
- Mettre à jour `ANTIGRAVITY_MISTAKES.md` si bug résolu ou piège identifié.

## 7. Optimisation tokens
- Lecture ciblée : `view_file` avec `StartLine`/`EndLine`, jamais de scan
  complet si inutile.
- Écriture différentielle : `multi_replace_file_content` pour les changements
  partiels.
- Si un fichier a déjà été lu dans ce tour, ne pas le relire sans raison
  explicite.

## Style
- Communication : français technique rigoureux.
- Commentaires code et documentation : anglais.
- Zéro introduction/conclusion. Aller directement au technique.
- SOLID, DRY, KISS. Performance dès la conception.