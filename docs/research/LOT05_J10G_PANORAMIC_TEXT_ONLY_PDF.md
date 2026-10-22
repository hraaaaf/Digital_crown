# LOT05 / J10G — PDF panoramique = compte rendu écrit uniquement

Date : 22 octobre 2026. Demande explicite du propriétaire : **« Je veux que le PDF ait seulement le bilan, le rapport de la radio panoramique. Je ne veux pas qu'il y ait l'image de la radio. »**

## Contrat fonctionnel immuable

L'espace Imagerie / Panoramique conserve le fichier radiographique comme média clinique séparé, consultable sous ses permissions habituelles. Le bouton **Aperçu PDF / Télécharger PDF** produit **uniquement le compte rendu textuel du praticien**, et non une copie de la radiographie.

Le PDF contient : titre « Bilan radiographique panoramique », identité/référence patient, date de l'examen, praticien associé, sections structurées des constatations rédigées ou validées par le praticien, synthèse, avertissement de non-inférence automatique, confidentialité. Les domaines non évalués restent explicitement non évalués. La confirmation humaine reste indispensable.

Le PDF **ne contient pas** : image panoramique, image de dents numérotées, capture d'écran, téléradiographie, annexe de mesures céphalométriques, QR en image, ou autre illustration radiologique. Ne pas faire apparaître une image même si le fichier radiographique est accessible localement. Pas de photographie radio ni de miniature sur quelque page du PDF que ce soit.

L'image originale reste stockée séparément dans Imagerie ; le rapport PDF peut être exporté, visualisé et archivé comme document indépendant. L'absence d'image dans le PDF ne doit **pas** effacer l'image de la base de données ni supprimer son lien d'accès existant. La génération PDF ne doit pas nécessiter de lire le fichier d'imagerie.

## Implementation du sous-lot expérimental

- `backend/templates/panoramic_elite.html` : suppression des blocs radiographiques, de l'annexe céphalométrique et du sceau QR ; préservation de la carte patient, des observations, du praticien et des avertissements.
- `backend/services/generators/panoramic_elite_gen.py` : génération à partir des seules observations déjà stockées ; abandon du chargement panoramique/cephalo et de la génération QR ; la protection `assert_patient_access` est préservée.
- `backend/services/generators/panoramic_gen.py` : compatibilité de la signature, suppression de l'insertion radiographique dans le générateur historique.
- `backend/routers/ia.py` et le frontend `PanoramicStudio.tsx` conservent leur endpoint PDF authentifié, le téléchargement blob et la prévisualisation. Aucun changement de stockage patients, aucun déploiement.
- `backend/tests/test_panoramic_pdf_text_only_j10g.py` + workflow dédié : test sur compte rendu 100 % synthétique avec **vraie sortie WeasyPrint PDF** ; extraction des informations de synthèse ; parcours de toutes les pages à la recherche d'images intégrées `/Image` ; vérification que les URL sensibles fournies comme pièges de test ne se retrouvent jamais dans le HTML. Tests des deux générateurs et du maintien des permissions de téléchargement.

## Frontières

Cette modification concerne le **contenu du PDF panoramique**, pas la décision clinique ou la sélection de modèle. Le modèle FDI actuellement retenu ne possède toujours pas de droits de commercialisation confirmés ; l'interface FDI demeure development-only. Les observations doivent provenir du praticien et aucune pathologie ne doit être automatiquement inférée des dents détectées. Les PR #1006, #1012 et #1013 restent DRAFT et non fusionnées. Aucun cabinet ou dossier patient réel n'a été touché.

Critère de clôture : CI exact HEAD SUCCESS sur vrai PDF synthétique sans image ; rapport et métadonnées conservés ; chaîne d'autorisation patient inchangée ; statut V1.5 NO-GO pour le reste.
