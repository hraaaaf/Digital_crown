file_path = r'c:\Users\lenovo\Documents\Cabinet\DigitalCrown\frontend\src\features\admin\Settings\tabs\branding\StudioPreview.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("'var(--primary)'", "profile.primary_color || 'var(--primary)'")
content = content.replace("'var(--secondary)'", "profile.secondary_color || 'var(--secondary)'")
content = content.replace("'var(--accent)'", "profile.accent_color || 'var(--accent)'")
content = content.replace("'var(--primary)15'", "profile.primary_color ? profile.primary_color + '26' : 'var(--primary)15'")
content = content.replace("'var(--secondary)15'", "profile.secondary_color ? profile.secondary_color + '26' : 'var(--secondary)15'")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated StudioPreview.tsx')
