# P6 — Document Libre : audit canonique exhaustif

## Baseline et périmètre

- Branche de certification : `cert/p6-document-libre`.
- PR de certification : `#405`.
- HEAD comportemental certifié avant closeout documentaire : `218e7ef1580e69958f02d9e8319750772f273376`.
- Portée : `LibreForm`, validation, toolbar, A4/A5, alignement, destinataire/date libre, preview, archive/réouverture, impression, PDF multi-page, permissions, protection de brouillon et responsive éditeur.
- **CODE VÉRIFIÉ** : oui pour les constats ci-dessous.
- **TESTS EXÉCUTÉS** : oui, CI principal #3183 / run `34528255939` et T2 Runtime Browser #2191 / run `34528255978`, tous deux en succès sur le HEAD comportemental certifié.
- **INTERACTION RUNTIME / VISUELLE** : oui pour la matrice navigateur authentifiée et le probe P6 dédié 390/768/1280 ; inspection humaine des trois captures réalisée.
- **CERTIFICATION PRODUCTION / RÉGLEMENTAIRE** : non revendiquée.

---

## 1. Architecture réelle P6

Flux principal :

`LibreForm.tsx` → état Document Studio → `useDocumentGenerator` → `/documents/generate` → `LibreData` → `LibreGenerator.generate()` → PDF → archive/réouverture.

Sous-flux : toolbar markup autorisé, tableau Markdown simple, format A4/A5, alignement, masquage en-tête patient, destinataire/date libre, dirty-state, preview et impression fraîche.

---

## 2. Matrice produit

### GARDER

1. Titre et contenu explicitement requis au générateur, avec bornes de taille.
2. Backend fail-closed sur format `A4|A5` et alignement autorisé.
3. Markup utilisateur échappé ; seule l'allowlist issue de la toolbar est conservée.
4. Balises autorisées déséquilibrées rendues sûres.
5. Tableaux Markdown rendus avec largeur bornée et en-tête répétable.
6. Noms de fichiers assainis.
7. Branding sous-compte résolu depuis le cabinet employeur.
8. Âge calculé à la date du document.
9. Document long multi-page sans compression microscopique.
10. Permission `clinical` requise pour émission/archivage/téléchargement.
11. Dirty-state sur les mutations de saisie + protection `beforeunload` et navigation inter-onglets.
12. Impression finale préparée depuis un PDF frais.
13. Archive réhydratable avec titre, contenu, destinataire, date/lieu, masquage en-tête, format et alignement.

### AMÉLIORER — hors gate P6

1. La toolbar insère du markup visible (`<b>`, `<i>`, `<u>`, `<font...>`) dans un textarea : fonctionnel mais non WYSIWYG.
2. Bibliothèque de templates dédiée absente : amélioration produit, pas défaut de sécurité.
3. Hiérarchie « Grand Titre » limitée à `<font size="16">` : amélioration UX, sans élargir arbitrairement l'allowlist HTML.
4. Densité structurelle du petit écran 390 encore perfectible, sans clipping/overflow bloquant observé dans la certification.

### CORRIGER — P0/P1

Aucun nouveau P0 statique démontré. Les deux gaps P1 historiques de certification finale et de runtime/rendu réel sont fermés par les preuves exact-head ci-dessous.

---

## 3. Contrat cible P6

Un Document Libre doit garantir :
- titre/contenu explicites ;
- aucun markup arbitraire interprété ;
- rendu PDF déterministe et lisible ;
- options de mise en page limitées à un contrat fermé ;
- patient/destinataire/date correctement échappés ;
- permission clinique ;
- aucun archivage lors d'une simple preview ;
- impression depuis un PDF frais ;
- round-trip archive → édition sans perte des champs supportés ;
- protection contre abandon involontaire du brouillon.

---

## 4. Connexions inter-pages

| Connexion | État code | Verdict |
|---|---|---|
| P6 → dossier patient | archive + réouverture | **GARDER** |
| P6 → impression | préparation PDF fraîche | **GARDER** |
| P6 → templates génériques | non branché dans le parcours actif | **OPTION PRODUIT** |
| P6 → autres pages | pas de conversion métier nécessaire démontrée | **NE PAS INVENTER** |

---

## 5. Certification finale observée

### Exact HEAD

HEAD comportemental : `218e7ef1580e69958f02d9e8319750772f273376`.

### CI principal

- workflow : CI ;
- run : `#3183` / `34528255939` ;
- conclusion : **success** ;
- frontend `Test suite` : **success** ;
- frontend `Build` : **success** ;
- les jobs de durcissement du workflow sont verts sur le même HEAD.

### T2 Runtime Browser

- workflow : T2 Runtime Browser Certification ;
- run : `#2191` / `34528255978` ;
- conclusion : **success** ;
- `Certify strict runtime PDF` : **success** ;
- `Execute authenticated browser matrix` : **success** ;
- `Certify P6 Document Libre editor` : **success** ;
- `Certify browser print and PDF freshness` : **success** ;
- artefact navigateur uploadé avec succès.

### Responsive / visuel P6

Probe P6 dédié :
- `390x844` : PASS ;
- `768x1024` : PASS ;
- `1280x900` : PASS ;
- aucun overflow horizontal document ;
- aucun clipping des contrôles P6 ciblés : titre, contenu, tableau, A5, A4, alignement justifié ;
- aucune erreur de page remontée par le probe.

Inspection humaine des trois captures : aucune régression visuelle bloquante observée. Score visuel de certification : **9/10**. Réserve : densité mobile 390, amélioration non bloquante.

---

## 6. Verdict P6

**P6 engineering/runtime/PDF/responsive automatisé est certifié sur le HEAD comportemental `218e7ef...`.**

Le closeout documentaire modifie uniquement les rapports canoniques ; il doit donc repasser les checks requis sur son nouveau HEAD avant merge de la PR #405.

Restent hors certification engineering :
- production sur cabinet réel ;
- éventuelle validation réglementaire humaine selon l'usage ;
- WYSIWYG/templates et polish supplémentaire, qui restent des améliorations produit.

Ces éléments ne rouvrent pas P6 engineering sauf défaut observé.
