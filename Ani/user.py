import sqlite3
from flask import session

def init_animals_table():
    """Initialize the animals table in users.db - table is defined in schema.sql"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create animals table if not exists (also defined in schema.sql)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS animals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            weight REAL,
            age INTEGER,
            gender TEXT,
            user_email TEXT NOT NULL,
            date_added TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    ''')
    conn.commit()
    
    # Check if sample animals exist for demo purposes
    cursor.execute("SELECT COUNT(*) FROM animals")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Add sample animals (will be associated with first registered user later)
        sample_animals = [
            ('C-001', 'Daisy', 'Cow', 680, 5, 'Female', 'demo@example.com'),
            ('C-002', 'Luna', 'Cow', 450, 3, 'Female', 'demo@example.com'),
            ('G-001', 'Billy', 'Goat', 85, 2, 'Male', 'demo@example.com'),
            ('S-001', 'Woolly', 'Sheep', 65, 3, 'Male', 'demo@example.com'),
        ]
        cursor.executemany('''
            INSERT OR IGNORE INTO animals (tag, name, species, weight, age, gender, user_email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_animals)
        conn.commit()
    
    conn.close()

def generate_animal_tag(species):
    """Generate a unique animal tag based on species"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Get species prefix
    prefix_map = {
        'Cow': 'C',
        'Buffalo': 'B',
        'Goat': 'G',
        'Sheep': 'S',
        'Horse': 'H',
        'Pig': 'P'
    }
    prefix = prefix_map.get(species, 'A')
    
    # Find the highest tag number for this prefix
    cursor.execute("SELECT tag FROM animals WHERE tag LIKE ?", (f'{prefix}-%',))
    tags = cursor.fetchall()
    conn.close()
    
    max_num = 0
    for tag in tags:
        try:
            num = int(tag[0].split('-')[1])
            if num > max_num:
                max_num = num
        except:
            pass
    
    new_tag = f"{prefix}-{str(max_num + 1).zfill(3)}"
    return new_tag

def add_animal(name, species, weight, age, gender, user_email):
    """Add a new animal to the database"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    tag = generate_animal_tag(species)
    
    try:
        cursor.execute('''
            INSERT INTO animals (tag, name, species, weight, age, gender, user_email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (tag, name, species, weight, age, gender, user_email))
        conn.commit()
        
        # Get the inserted animal
        cursor.execute("SELECT * FROM animals WHERE tag = ?", (tag,))
        animal = cursor.fetchone()
        conn.close()
        
        if animal:
            return {
                'id': animal[0],
                'tag': animal[1],
                'name': animal[2],
                'species': animal[3],
                'weight': animal[4],
                'age': animal[5],
                'gender': animal[6],
                'user_email': animal[7],
                'date_added': animal[8]
            }
    except sqlite3.IntegrityError as e:
        conn.close()
        return None
    
    return None

def get_animals_by_user(user_email):
    """Get all ACTIVE animals belonging to a user"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM animals WHERE user_email = ? AND (is_active = 1 OR is_active IS NULL) ORDER BY date_added DESC", (user_email,))
    animals = cursor.fetchall()
    conn.close()
    
    result = []
    for animal in animals:
        result.append({
            'id': animal[0],
            'tag': animal[1],
            'name': animal[2],
            'species': animal[3],
            'weight': animal[4],
            'age': animal[5],
            'gender': animal[6],
            'user_email': animal[7],
            'date_added': animal[8],
            'is_active': animal[9] if len(animal) > 9 else 1
        })
    
    return result

def get_inactive_animals_by_user(user_email):
    """Get all INACTIVE animals belonging to a user (for history)"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM animals WHERE user_email = ? AND is_active = 0 ORDER BY date_added DESC", (user_email,))
    animals = cursor.fetchall()
    conn.close()
    
    result = []
    for animal in animals:
        result.append({
            'id': animal[0],
            'tag': animal[1],
            'name': animal[2],
            'species': animal[3],
            'weight': animal[4],
            'age': animal[5],
            'gender': animal[6],
            'user_email': animal[7],
            'date_added': animal[8],
            'is_active': animal[9] if len(animal) > 9 else 0
        })
    
    return result

def get_all_animals_by_user(user_email):
    """Get ALL animals belonging to a user (both active and inactive)"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM animals WHERE user_email = ? ORDER BY is_active DESC, date_added DESC", (user_email,))
    animals = cursor.fetchall()
    conn.close()
    
    result = []
    for animal in animals:
        result.append({
            'id': animal[0],
            'tag': animal[1],
            'name': animal[2],
            'species': animal[3],
            'weight': animal[4],
            'age': animal[5],
            'gender': animal[6],
            'user_email': animal[7],
            'date_added': animal[8],
            'is_active': animal[9] if len(animal) > 9 else 1
        })
    
    return result

def get_all_animals():
    """Get all animals in the database"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM animals ORDER BY date_added DESC")
    animals = cursor.fetchall()
    conn.close()
    
    result = []
    for animal in animals:
        result.append({
            'id': animal[0],
            'tag': animal[1],
            'name': animal[2],
            'species': animal[3],
            'weight': animal[4],
            'age': animal[5],
            'gender': animal[6],
            'user_email': animal[7],
            'date_added': animal[8]
        })
    
    return result

def get_animal_by_tag(tag):
    """Get a specific animal by its tag"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM animals WHERE tag = ?", (tag,))
    animal = cursor.fetchone()
    conn.close()
    
    if animal:
        return {
            'id': animal[0],
            'tag': animal[1],
            'name': animal[2],
            'species': animal[3],
            'weight': animal[4],
            'age': animal[5],
            'gender': animal[6],
            'user_email': animal[7],
            'date_added': animal[8]
        }
    
    return None

def update_animal(tag, name, species, weight, age, gender):
    """Update an existing animal"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE animals 
        SET name = ?, species = ?, weight = ?, age = ?, gender = ?
        WHERE tag = ?
    ''', (name, species, weight, age, gender, tag))
    
    conn.commit()
    conn.close()
    
    return get_animal_by_tag(tag)

def delete_animal(tag):
    """Mark an animal as inactive (soft delete)"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("UPDATE animals SET is_active = 0 WHERE tag = ?", (tag,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0

def deactivate_animal(tag):
    """Deactivate an animal - moves it to history"""
    return delete_animal(tag)

def assign_sample_animals_to_user(user_email):
    """Assign sample animals to a specific user"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("UPDATE animals SET user_email = ? WHERE user_email = 'demo@example.com'", (user_email,))
    conn.commit()
    conn.close()
