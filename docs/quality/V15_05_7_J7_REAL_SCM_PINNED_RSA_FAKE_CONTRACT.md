# Digital Crown — LOT05.7-J phase 7 — vrai SCM Windows et clé publique épinglée sur FAKE

**Mission** : uniquement LOT05 SQL Migration Wizard / 05.7-J, empilée sur [PR Draft #981](https://github.com/hraaaaf/Digital_crown/pull/981), base HEAD `3f9af11433529d10b50188bec8e00a67fc330982`. Aucune restauration clinique activée, aucun routeur/worker/migration/base/UX/média patient touché, PR Draft sans merge ni déploiement. Périmètre de fichiers : workflow parent J6 borné, workflow REQUIRED J7, exécutable ServiceBase C# uniquement fictif, script PowerShell CI, présent contrat et techdoubt.md.

## Propriétés effectivement mises à l'épreuve

Le runner GitHub **Windows administratif éphémère** compile un vrai exécutable `ServiceBase` .NET Framework. Le script crée deux services SCM `DCJ7A_<nonce>` et `DCJ7B_<nonce>` sous `NT AUTHORITY\LocalService`, A `sidtype UNRESTRICTED`, B `sidtype NONE`. Il résout `NT SERVICE\DCJ7A_<nonce>` en authentique SID `S-1-5-80-...` et vérifie la correspondance avec `sc showsid`. Un répertoire de **clé publique RSA 2048** et un journal fictif `consumed` reçoivent uniquement les ACE SYSTEM, Administrators, SID A ; ni LocalService ni Users générique dans leurs trois ACE explicites ; `Get-Acl` vérifie la liste physique des SIDs et DACL non héritée. La télémétrie est séparée et non considérée comme preuve cryptographique en soi.

L'identité **interactive de CI** crée une paire RSA temporaire, signe en SHA-256 RSA-PKCS1 un ordre FAKE strict (`owner=17`, audience constante `LOT05J7_FAKE_WORKER`, nonce hex 128-bit, durée maximale 120 secondes). **Seule la clé publique** modulus/exponent est écrite dans la zone de pin ; la clé privée n'est pas enregistrée dans l'arborescence fictive et est détruite après signature. Le service A **exécuté réellement par SCM avec LocalService + SID A** lit la clé ACL-pinnée, vérifie la signature en C# et refuse la variante tampered. Un jeton de rejeu est créé par `FileMode.CreateNew` dans un dossier réservé à A ; à son **redémarrage SCM réel**, A vérifie la signature mais refuse le nonce déjà consommé. Le service B sous le **même compte LocalService sans SID A** échoue à lire le pin, donc ne peut pas vérifier la signature. Le `finally` doit arrêter/supprimer les deux services, supprimer les fixtures et confirmer `sc query` non disponible. Aucun test n'appelle `request_apply` autrement que pour constater le refus hérité.

## Gates REQUIRED

- Workflow J7 : vrai test SCM / C# / ACL / signature / falsification / anti-rejeu inter-démarrage de service et refus de même compte sans SID, parse PowerShell obligatoire, marqueurs log exigés, HEAD exact.
- Workflow J7 : rejoue en Linux et Windows **280 exécutions héritées J6** (130 Linux + 150 Windows, dont 42 exécutions de tests I répétées, pas 280 scénarios distincts), incluant JWT réel et SQLCipher natif, NTFS/J6 et désactivation clinique.
- Un autre job Windows rejoue le laboratoire J3 du vrai SCM + ACL et tokens ; CI Scope Gate au HEAD final. Parent J6 et autres workflows historiquement empilés SKIPPED **HORS SCOPE**, leurs suites vraiment rejouées dans J7.
- Deux perspectives adversariales **internes**, notes sévères, vérification après corrections sur même HEAD, POST Notion. Un résultat rouge de CI n'est jamais effacé des réserves `techdoubt.md`.

## BLOCKERS à conserver, indépendamment d'un SUCCESS

Cette signature RSA est initiée par **l'administrateur du test** qui crée également la clé publique épinglée. L'ACL Service SID protège la lecture dans cette seule expérience ; elle ne démontre PAS que le signataire était réellement autorisé par un JWT ni que le pin provient d'un installateur clinique signé. Le service testé est une fixture C# éphémère et **n'est PAS un worker Digital Crown installé**. Le journal `FileMode.CreateNew` démontre une unicité locale de nom, pas une preuve crash-safe, anti-rollback ni de persistance face à une panne d'alimentation. L'administrateur/SYSTEM garde FullControl, et `UNRESTRICTED` ne crée pas un jeton Windows restreint. Le service a besoin de contrôles de chemins/handles et de DACL produits, d'un canal JWT→job signé autorisé→Service SID SCM attesté ; il manque transaction SQLCipher DB+WAL/SHM+coffre/médias, powerfail, RPO/RTO, consentement et traçabilité patient.

Les points d'entrée cliniques actifs `request_apply` et `GuidedRestoreWorker.run` sont **DENY** depuis #976. **Statut maximal si toutes preuves passent : J7 CONVERGED LAB, CLINIQUE NO-GO.** Aucun merge, déploiement ou restauration clinique.

**Roadmap** : LOT05 → 05.7-J phases 1–6 LAB → J7 SCM/SID/pin RSA et nonce inter-redémarrage → intégration, autorité et durabilité clinique NON certifiées → LOT10 hors périmètre.
