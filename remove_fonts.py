import os
import re

directory = r'c:\Users\lenovo\Documents\Cabinet\DigitalCrown\frontend\src\features\admin\Settings\tabs'

def remove_fonts(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Matches font-['Inter'], font-['Outfit'], etc.
    new_content = re.sub(r"font-\['[^']+']\s?", "", content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file_path}")

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            remove_fonts(os.path.join(root, file))
