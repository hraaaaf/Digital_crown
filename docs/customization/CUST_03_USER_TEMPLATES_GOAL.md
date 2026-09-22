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
6. Les garde-fous type/durée/suggestion existants restent inchangés.
7. Mobile 390, tablette 768, desktop 1280: aucun overflow/chevauchement.
8. BEFORE et AFTER capturés aux mêmes viewports.

## Hors scope
- modification automatique du texte par IA;
- templates de durée ou d'arrêt de travail;
- refonte du moteur PDF;
- édition/suppression globale des modèles dans Réglages;
- ordonnance/presets cliniques (CUST-04);
- déploiement Vercel.
