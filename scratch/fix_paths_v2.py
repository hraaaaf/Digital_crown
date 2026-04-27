import os
import re

files = [
    "backend/services/generators/ordonnance_gen.py",
    "backend/services/generators/certificat_gen.py",
    "backend/services/generators/libre_gen.py",
    "backend/services/generators/accounting_gen.py"
]

for f in files:
    if not os.path.exists(f): continue
    
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remplacer les mauvais remplacements par le bon (avec double backslash pour la chaÃ®ne Python)
    content = content.replace('return filepath.replace("\\", "/")', 'return filepath.replace("\\\\", "/")')
    
    with open(f, 'w', encoding='utf-8', newline='\n') as file:
        file.write(content)
    print(f"Fixed {f}")
