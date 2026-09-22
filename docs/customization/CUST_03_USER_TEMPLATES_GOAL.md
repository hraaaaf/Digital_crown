# CUST-03 — User templates — Goal

Date: 2026-09-22

## Goal
Permettre au praticien de créer et réutiliser ses propres modèles de contenu sans créer une seconde source de vérité.

Premier flux: **Document Studio → Certificat médical libre**.

## Vérité actuelle vérifiée
- `DocumentTemplate` existe déjà et persiste `type`, `name`, `body_html`, `design_config`, `is_system`, `is_default`.
- `/api/templates` expose list/get/create/set-default/delete.
- Le générateur PDF certificat actuel n'utilise pas `DocumentTemplate`; il rend le champ libre `CertificatData.content`.
- Le type, la durée et le contenu du certificat restent sous validation explicite du praticien.
- Les suggestions documentaires existantes sont informatives et non mutantes.

## Décision d'architecture
Réutiliser `DocumentTemplate` comme source unique des modèles enregistrés.

Pour CUST-03A, un modèle CERTIFICAT personnalisé stocke un **brouillon de texte** dans `body_html`.
L'application d'un modèle copie explicitement ce texte dans le brouillon `certifCustomMotif`.
Le générateur PDF certifié reste inchangé et continue d'échapper/rendre le texte final.

Aucune application automatique.
Aucune déduction du type ou de la durée.
Aucune deuxième table.
Aucune migration DB.

## Target UI

```text
Certificat médical

[ Modèles du cabinet ]
[ Modèle A ] [ Modèle B ]        [+ Créer un modèle]

"Appliquer un modèle copie son texte dans le brouillon.
 Le praticien doit le relire et le valider."

Contenu du certificat médical
┌──────────────────────────────────────────────┐
│ texte final éditable                         │
└──────────────────────────────────────────────┘

Créer un modèle
┌──────────────────────────────────────────────┐
│ Nom du modèle                                │
│ Contenu                                      │
│                         Annuler  Enregistrer │
└──────────────────────────────────────────────┘
```

## Succès observable
1. Les modèles personnalisés CERTIFICAT sont chargés depuis `/api/templates?type=CERTIFICAT&is_system=false`.
2. Un modèle n'est appliqué qu'après clic explicite.
3. L'application remplit uniquement le texte du certificat libre.
4. Créer un modèle réutilise POST `/api/templates`, sans nouvelle persistance.
5. Le texte reste éditable après application.
6. Si un brouillon existe déjà, son remplacement requiert une confirmation explicite.
7. Les garde-fous type/durée/suggestion existants restent inchangés.
7. Mobile 390, tablette 768, desktop 1280: aucun overflow/chevauchement.
8. BEFORE et AFTER capturés aux mêmes viewports.

## Hors scope
- modification automatique du texte par IA;
- templates de durée ou d'arrêt de travail;
- refonte du moteur PDF;
- édition/suppression globale des modèles dans Réglages;
- ordonnance/presets cliniques (CUST-04);
- déploiement Vercel.


## CUST-03B — Document libre

### Décision
Le même `DocumentTemplate` porte les modèles de Document libre avec `type=DOCUMENT_LIBRE`.

Pour rester compatible avec le schéma existant sans migration :
- `name` = nom du modèle et titre appliqué au document ;
- `body_html` = contenu réutilisable ;
- destinataire, date/lieu, format A4/A5, alignement et visibilité de l'en-tête restent propres au document en cours et ne sont pas capturés par le modèle.

### Target UI
Dans l'éditeur Document libre :
- bloc discret **Mes modèles** ;
- boutons de modèles existants ;
- action **Enregistrer comme modèle** ;
- modal avec nom/titre appliqué + contenu ;
- application uniquement sur clic explicite ;
- titre et contenu restent éditables après application.

### Succès observable
1. lecture via `/api/templates?type=DOCUMENT_LIBRE&is_system=false` ;
2. zéro application automatique ;
3. clic modèle → titre + contenu uniquement ;
4. sauvegarde via le même POST `/api/templates` ;
5. aucune capture silencieuse des métadonnées patient/date/layout ;
6. remplacement d'un document déjà rédigé soumis à confirmation explicite ;
7. isolation tenant identique au certificat ;
8. BEFORE/AFTER 390×844, 768×1024, 1280×900 + modal.
