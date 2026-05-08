#!/usr/bin/env python3
"""
Suppression des lignes vides excessives
"""
def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    result = []
    prev_empty = False
    
    for line in lines:
        is_empty = line.strip() == ''
        
        # Garde la ligne si elle n'est pas vide, ou si c'est la première ligne vide après du contenu
        if not is_empty:
            result.append(line)
            prev_empty = False
        elif not prev_empty:
            # Garde une seule ligne vide
            result.append('\n')
            prev_empty = True
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(result)
    
    print(f"Fichier optimise: {len(lines)} -> {len(result)} lignes")

if __name__ == "__main__":
    fix_file("frontend/src/features/ortho/CephaloWorkspace.tsx")
