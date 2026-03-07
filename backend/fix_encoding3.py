#!/usr/bin/env python3
"""
Nettoyage final - suppression des caractères restants
"""
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Supprime les caractères spéciaux restants
    content = re.sub(r'œ', '*', content)
    content = re.sub(r'Ã—', '*', content)
    content = re.sub(r'â€ ', '-', content)
    content = re.sub(r'â†', '->', content)
    content = re.sub(r'†', '*', content)
    content = re.sub(r'·', '*', content)
    content = re.sub(r'—', '-', content)
    
    # Supprime les lignes vides multiples (plus de 2 sauts de ligne)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Nettoyage final termine")

if __name__ == "__main__":
    fix_file("frontend/src/features/ortho/CephaloWorkspace.tsx")
