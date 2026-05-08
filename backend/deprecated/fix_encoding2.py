#!/usr/bin/env python3
"""
Nettoyage agressif des caractères corrompus
"""
import re

def clean_line(line):
    """Nettoie une ligne de caractères corrompus"""
    # Supprime les box-drawing corrompus
    line = re.sub(r'[\u00e2\u20ac\u201d\u201c\u2018\u2019\u02c6\u2030\u00a6]+', '', line)
    line = re.sub(r'€+', '', line)
    
    # Caractères accentués corrompus
    replacements = [
        ('\u00c3\u00a9', 'é'), ('\u00c3\u00a8', 'è'), ('\u00c3\u00a7', 'ç'),
        ('\u00c3 ', 'à'), ('\u00c3\u00b4', 'ô'), ('\u00c3\u00aa', 'ê'),
        ('\u00c3\u00a2', 'â'), ('\u00c3\u00ae', 'î'), ('\u00c3\u00af', 'ï'),
        ('\u00c3\u00bc', 'ü'), ('\u00c3\u2030', 'É'), ('\u00c3\u02c6', 'È'),
        ('\u00c3\u20ac', 'À'), ('\u00c3\u201d', 'Ô'), ('\u00c2\u00b0', '°'),
        ('\u00e2\u20ac', '→'), ('\u00e2\u2013', ''), ('\u00e2\u201c', ''),
        ('\u00e2\u2018', ''), ('\u00e2\u2019', ''), ('\u00c2', ''),
        ('\u00e2\u20ac', '→'), ('\u00e2\u201e', ''), ('\u00e2', ''),
    ]
    
    for old, new in replacements:
        line = line.replace(old, new)
    
    return line

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    empty_count = 0
    
    for line in lines:
        cleaned = clean_line(line)
        
        # Supprime les lignes qui ne contiennent que des espaces
        if cleaned.strip() == '':
            empty_count += 1
            if empty_count <= 1:  # Garde max 1 ligne vide consécutive
                cleaned_lines.append('\n')
        else:
            empty_count = 0
            cleaned_lines.append(cleaned)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print(f"Fichier nettoye: {len(lines)} -> {len(cleaned_lines)} lignes")

if __name__ == "__main__":
    fix_file("frontend/src/features/ortho/CephaloWorkspace.tsx")
