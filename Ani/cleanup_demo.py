import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Delete health_readings for demo user's animals
cursor.execute('''
    DELETE FROM health_readings 
    WHERE animal_tag IN (
        SELECT tag FROM animals WHERE user_email = 'demo@example.com'
    )
''')
deleted = cursor.rowcount
print(f'Deleted {deleted} demo user readings')

# Also delete demo user's animals
cursor.execute("DELETE FROM animals WHERE user_email = 'demo@example.com'")
deleted_animals = cursor.rowcount
print(f'Deleted {deleted_animals} demo user animals')

conn.commit()
conn.close()

print('Cleanup complete!')
