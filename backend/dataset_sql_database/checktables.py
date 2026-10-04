import sqlite3

# Apni db file ka naam likhein
conn = sqlite3.connect("mimic_iv_demo.db")
cursor = conn.cursor()

# Yeh query database mein mojood sab tables ke naam nikal kar layegi
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

tables = cursor.fetchall()

print(f"Total Tables: {len(tables)}")
print("Tables name is :")
for table in tables:
    print("-", table[0])

conn.close()