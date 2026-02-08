import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in users.db:")
for t in tables:
    print(f"  - {t[0]}")

print("\n" + "="*50)
print("Checking treatment_history table:")
print("="*50)

try:
    cursor.execute("SELECT COUNT(*) FROM treatment_history")
    count = cursor.fetchone()[0]
    print(f"Records in treatment_history: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM treatment_history LIMIT 5")
        cols = [description[0] for description in cursor.description]
        print(f"\nColumns: {cols}")
        print("\nSample records:")
        for row in cursor.fetchall():
            print(row)
except Exception as e:
    print(f"Error: {e}")

conn.close()
