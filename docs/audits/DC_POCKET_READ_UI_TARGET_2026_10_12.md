# Pocket commun — cible du branchement UI

Before : build test de `4c13a9f` (helper non consommé), composant MobileDashboard réel, API fictive interceptée, Chromium, 16 cas verts / 48 captures. Référence conservée dans `pocket-after-reference/capabilities-before-built`. Le rôle seul donne encore la trésorerie au dentiste restreint et la refuse à l'assistante autorisée.

Goal : préserver la présentation Pocket dentiste de #838, ses cinq positions de navigation, tokens, cartes et tailles ; appliquer aux destinations de lecture les droits du serveur. Patients et agenda restent en place mais désactivés si refusés ; les entrées Plus refusées disparaissent ; les liens directs affichent un refus sans monter le composant. Vérification initiale/en échec : pas de droits implicites du rôle ni du cache ; message et nouvelle tentative. Les gardes backend restent l'autorité.

Target : dentiste autorisé identique ; dentiste restreint sans dossiers/finance ; assistante standard sans finance ; assistante avec permission comptabilité voit le résumé financier en lecture seule. Révocation lors d'une reprise de focus retire l'écran ouvert. Même comparaison Today/Plus/finance aux formats 390×844, 430×932, 768×1024 et 1280×900. Données exclusivement fictives. WebKit automatisé ne prouve pas un iPhone physique.

Périmètre : branchement staff de lecture uniquement. La coque patient et le transport distant ne sont pas achevés par ce lot. Validation humaine des captures et CI au SHA final restent à obtenir. Aucun merge autorisé.

Étape Before : EXECUTION_SCORE 7.9 ; ADVERSARIAL_SCORE 7.9 ; RETAINED_SCORE 7.9. Gates finaux manquants, pas de statut VERIFIED. Next exact : implémentation puis capture After et comparaison.
