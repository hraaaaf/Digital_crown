# P7 visual acceptance

Goal visuel : la Page Patient reste un workspace compact en 5 espaces, sans régression de responsive ni réintroduction de labels legacy.

Critères :
- mêmes viewports 390×844, 430×932, 768×1024, 1280×900 ;
- 10 surfaces par viewport ;
- zéro overflow horizontal ;
- zéro erreur runtime ;
- zéro HTTP 5xx ;
- Clinique affiche les sources/persistances structurées ;
- Imagerie conserve RVG/Panoramique/Céphalométrie ;
- Documents ne réexpose pas le Compagnon ;
- Finances conserve les 4 KPI factuels ;
- Add Patient conserve sexe vide par défaut.

Références visuelles : wireframes et AFTER certifiés P1→P6. P7 n'introduit pas de redesign ; il certifie leur coexistence sur le HEAD consolidé.
