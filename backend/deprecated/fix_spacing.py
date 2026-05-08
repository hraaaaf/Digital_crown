#!/usr/bin/env python3
"""
Corrige l'espacement excessif (ligne vide apres chaque ligne)
"""
def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split en lignes
    lines = content.split('\n')
    
    # Filtre: garde les lignes qui ont du contenu OU qui suivent une ligne avec contenu
    result = []
    for i, line in enumerate(lines):
        # Garde la ligne si elle a du contenu
        if line.strip() != '':
            result.append(line)
        # Ou si c'est une ligne vide mais qu'elle ne suit pas une ligne vide
        elif i > 0 and lines[i-1].strip() != '':
            # Ne garde pas les lignes vides isolées
            pass
    
    # Rejoint avec des sauts de ligne
    new_content = '\n'.join(result)
    
    # Ajoute des sauts de ligne autour des blocs pour la lisibilite
    new_content = new_content.replace('}\n', '}\n\n')
    new_content = new_content.replace(';\n', ';\n\n')
    new_content = new_content.replace('*/\n', '*/\n\n')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Correction terminee: {len(lines)} -> {len(result)} lignes effectives")

if __name__ == "__main__":
    fix_file("frontend/src/features/ortho/CephaloWorkspace.tsx")
