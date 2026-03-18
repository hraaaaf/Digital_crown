import sqlite3
conn = sqlite3.connect('digital_crown.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tables: {tables}")

if 'cephalo_analyses' in tables:
    cursor.execute('SELECT COUNT(*) FROM cephalo_analyses')
    count = cursor.fetchone()[0]
    print(f'\nNombre d analyses cephalo: {count}')
    if count > 0:
        cursor.execute('SELECT id, patient_id, created_at FROM cephalo_analyses ORDER BY created_at DESC LIMIT 5')
        for row in cursor.fetchall():
            print(f"  ID:{row[0]} Patient:{row[1]} Date:{row[2]}")
else:
    print("\nTable cephalo_analyses non trouvee")

conn.close()
