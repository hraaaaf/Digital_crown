# P3 — Certificat + Document Libre : pré-audit statique

## Statut de preuve

Pré-cartographie **lecture seule** réalisée pendant les gates CI P2.

- **CODE VÉRIFIÉ** : oui, pour les constats ci-dessous.
- **TESTS EXÉCUTÉS P3** : non.
- **INTERACTION RUNTIME** : non exécutée.
- **CERTIFICATION CLINIQUE / DOCUMENTAIRE / PRODUCTION** : non revendiquée.

## P3-A — Certificat : suggestion auto-appliquée

### Frontend vérifié
`CertificateForm` appelle `/prescriptions/certif-suggest/{patient_id}` au chargement.

Si la réponse contient `confidence === 'high'`, l’UI applique **automatiquement** :
- `setCertifType(res.data.type)` ;
- `setCertifDays(res.data.days)`.

Aucune action explicite du praticien n’est requise pour cette mutation.

### Backend vérifié
Le niveau `high` ne provient pas d’un modèle clinique validé. Le routeur inspecte le libellé du dernier acte / motif de RDV et utilise une détection lexicale.

Pour les mots-clés `extraction`, `chirurgie`, `implant`, `lambeau`, `resection`, il renvoie :
- type : `Repos Post-Opératoire` ;
- durée : **3 jours** ;
- confidence : `high`.

### Risque
Une heuristique documentaire fixe peut donc modifier silencieusement un certificat médical et sa durée comme si elle constituait une décision patient-spécifique suffisamment certaine.

### Décision P3 recommandée
- conserver éventuellement la suggestion comme **information non appliquée** ;
- supprimer toute auto-application de type/durée ;
- durée et nature du certificat restent une validation explicite du praticien ;
- renommer `confidence` si conservé afin de ne pas suggérer une validation clinique.

---

## P3-B — Certificat « Autre » : fallback médical silencieux

### Fait vérifié
Dans `useDocumentGenerator.buildPayload()`, lorsque `certifType === 'Autre'`, le motif envoyé est :
`certifCustomMotif || 'Repos Post-Opératoire'`.

La validation certificat contrôle la durée mais ne bloque pas un motif libre vide.

### Risque
Le praticien peut sélectionner un certificat libre, laisser le motif vide, puis générer un document dont le motif devient silencieusement `Repos Post-Opératoire`.

### Décision P3 recommandée
- `Autre` exige un motif explicite non vide ;
- aucun motif médical de remplacement ne doit être synthétisé ;
- validation frontend + contrat backend cohérents.

---

## P3-C — Document Libre : balises utilisateur interprétées par ReportLab

### Frontend vérifié
La toolbar insère directement dans la textarea des balises :
- `<b>...</b>` ;
- `<i>...</i>` ;
- `<u>...</u>` ;
- `<font size="16">...</font>` ;
- tableaux Markdown simplifiés.

### Validation frontend vérifiée
`useDocumentGenerator.validatePayload()` vérifie uniquement que `libreTitle` et `libreContent` ne sont pas vides. Aucun contrôle de structure/whitelist des balises n’est effectué à cette frontière.

### Backend vérifié
`LibreGenerator` :
- injecte les lignes utilisateur dans `ReportLab Paragraph` ;
- laisse ReportLab interpréter le markup supporté ;
- fait la même chose dans les cellules de tableaux ;
- interpole également `custom_patient` dans un `Paragraph` sans étape d’échappement dédiée.

### Risque
Aucune exécution de code n’est démontrée. Le risque vérifié est **documentaire / robustesse de rendu** : une balise invalide, non fermée ou inattendue peut provoquer un rendu incorrect ou une erreur de génération.

### Décision P3 recommandée
- définir une whitelist explicite du markup accepté ;
- échapper les champs textuels qui ne sont pas destinés au markup, notamment destinataire/date ;
- parser/valider le contenu avant génération ;
- conserver les fonctions gras/italique/souligné/tableau via une représentation déterministe plutôt que du HTML libre si possible.

---

## P3-D — Points restant à cartographier

- comportement preview/save/print pour certificat et libre ;
- dirty-state et protection navigation ;
- format A4/A5 et compression single-page ;
- cas de contenu long / tableaux larges / balises mal formées ;
- cohérence entre `Certificat de Présence`, `Arrêt de travail`, `Autre` et les valeurs backend ;
- accessibilité clavier/ARIA des contrôles custom ;
- tests runtime ciblés avant toute certification.
