import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

print('=== USERS ===')
cursor.execute('SELECT id, email, full_name FROM users LIMIT 10')
for row in cursor.fetchall():
    print(row)

print('\n=== ANIMALS ===')
cursor.execute('SELECT id, name, species, user_email FROM animals LIMIT 10')
for row in cursor.fetchall():
    print(row)

print('\n=== TOTAL ANIMALS ===')
cursor.execute('SELECT COUNT(*) FROM animals')
print(f'Total animals: {cursor.fetchone()[0]}')

print('\n=== ANIMALS BY USER_EMAIL ===')
cursor.execute('SELECT user_email, COUNT(*) as count FROM animals GROUP BY user_email')
for row in cursor.fetchall():
    print(row)

conn.close()
