# V1.5-04.4 — Session QR/NFC bornée à la Station — implémentation empilée DRAFT

**Statut : EN COURS / non fusionné / FUE-I non certifiée.** Branche empilée sur la PR produit [#837](https://github.com/hraaaaf/Digital_crown/pull/837) au HEAD `db2756a5de97967260c8f1e1b248beff564cdb6e`. Ne pas fusionner ce lot avant le closeout et post-merge de 04.3. La PR #839 reste la campagne FUE laboratoire indépendante. Aucun Vercel, aucun appareil physique ni patient réel.

## Goal canonique (3 SP, FUE-I)

> **Session QR/NFC** : identité patient bornée ; jeton court lié à la station ; expiration et anti-replay.

Ce contrat se distingue du delivery 04.5 (impression locale, Pocket, QR de remise du document), de la purge renforcée 04.6 et du gate adversarial complet 04.7. La station demeure un point de **retrait de documents déjà autorisés**, jamais un éditeur clinique.

## Réutiliser, ne pas dupliquer

Le sous-lot **03.3 déjà présent** émet un token opaque aléatoire dont seul le hash SHA-256 est stocké, valide **120 secondes**, attaché au tenant et à une station enregistrée. Le QR et le payload NFC portent le même lien d'identification `/companion?stationSession=...`, sans identité clinique. Un Patient Companion **authentifié** avec `accessId` actif et de même tenant effectue un **claim atomique unique**. Expiration, remplacement et purge rendent le token inutilisable ; le GET de document demeure soumis au 04.1 Eligibility Engine et à l'autorisation du praticien 04.3, liée à patient+SHA.

Il ne faut **pas** confondre ce QR d'identification avec un QR de **téléchargement du PDF** : ce dernier relève de 04.5. Ne jamais injecter le hash du document, l'identité du patient ou des données cliniques dans l'URL QR/NFC.

## Invariants 04.4 à vérifier

1. Un handoff valide ne doit pas survivre à la révocation **ou au changement du mode Station vers Cabinet** entre émission et claim. Le garde est évalué lors de la recherche initiale **et** dans le `UPDATE` atomique.
2. Le statut Station et le retrait du PDF sont interdits tant que la session n'est pas identifiée ; le token brut ne constitue **jamais** une autorisation clinique/documentaire.
3. QR et NFC réutilisent le même token ; le premier claim valide est unique, toute deuxième utilisation retourne un refus. Chaque nouvelle session purge l'ancienne sur la même station.
4. Si le patient appartient à un autre tenant, si la session est expirée, purgée ou remplacée, ou si la station est révoquée / plus en mode Station, le claim échoue et ne lie aucun patient.
5. L'accès documentaire après identification reste lié à la session, au patient exact et à la station exacte, avec vérification SHA des octets de la feuille de soins finalisée.
6. Le rejet renvoie un code générique sans patient, token brut ni chemin de PDF. Audit/bout de chaîne ne promet pas l'impression, transfert Pocket ni confirmation de lecture sur téléphone.

## FUE-I à apporter en preuves

Persona : patient avec Patient Companion déjà identifié, sans connaissance préalable du flux ; un patient d'un autre cabinet en attaque négative. Premier résultat intermédiaire observable : station passe de attente QR/NFC à **patient identifié**, puis ne montre qu'un chemin vers documents éligibles quand le composant documents sera disponible. Cas d'erreur : mauvais tenant, replay, expiration, remplacement, station révoquée, sortie du mode Station, connexion interrompue.

- **Required pour ce changement backend :** tests HTTP + SQLite intégrés, suites 03.3 et 04.3 de non-régression, syntaxe, mêmes SHA et log exacts.
- **FUE-I UX :** réutiliser captures responsive 03.3 FR/EN/AR, 390/430/768/1280 + zoom 200 % et navigation QR -> identifié ; distinguer API mock des faits terrain et état UI Documents (toujours en cours de construction).
- **Hors scope 04.4 :** lecture NFC matérielle, imprimante physique, Pocket réception, QR de remise à usage unique du PDF et panel clinique.
- **Risques ouverts à réévaluer avant certification terrain :** le lien QR actuel est dérivé de `request.base_url` ; politique de confiance du Host/origine et configuration réelle LAN/TLS restent à vérifier dans le déploiement. Une CI verte sur auth ne prouve pas la résistance à un Host falsifié.
- Deux perspectives adversariales sur **même HEAD**, puis confirmation ; aucun PASS FUE-I sans une preuve UX réellement liée au produit, pas simplement une collecte GitHub.

## Périmètre du candidat

- Backend : une condition sur le WorkstationMode actif, tenant et expérience Station dans la recherche et l'UPDATE du claim, sans créer de second mécanisme ni changer la durée de vie 120 s.
- Régressions : vrai HTTP (hors matériel) : QR=NFC, session identifiée puis retrait, replay, station révoquée, changement de mode, remplacement et expiration.
- **Pas de modification UI 04.5**, pas de données patients réelles, pas de changement runtime 04.3.

**Verdict initial :** CANDIDATE OPEN ; le 04.4 FUE-I devra encore franchir la preuve d'usage intermédiaire et la revue de confiance des URL QR avant CLOSED.
