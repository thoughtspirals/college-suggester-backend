import sqlite3

conn = sqlite3.connect("cutoffs.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM cutoffs")
rows = cursor.fetchall()

for row in rows:
    print(row)
    
conn.close()    