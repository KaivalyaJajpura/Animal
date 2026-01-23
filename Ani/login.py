import sqlite3
from flask import session
from werkzeug.security import check_password_hash

def login_user(email, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return 'not_found'
    
    if check_password_hash(user[4], password):
        session['user'] = user[1]  # full_name
        session['user_email'] = user[2]  # email
        session['user_mobile'] = user[3]  # mobile
        
        # Assign sample animals to this user if they don't have any
        assign_animals_if_needed(email)
        
        return 'success'
    return 'invalid_password'

def assign_animals_if_needed(user_email):
    """Create sample animals for new user if they don't have any"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        # Check if user has any animals
        cursor.execute("SELECT COUNT(*) FROM animals WHERE user_email = ?", (user_email,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Create new sample animals for this specific user (not sharing demo animals)
            sample_animals = [
                ('Daisy', 'Cow', 680, 5, 'Female', user_email),
                ('Luna', 'Cow', 450, 3, 'Female', user_email),
                ('Billy', 'Goat', 85, 2, 'Male', user_email),
                ('Woolly', 'Sheep', 65, 3, 'Male', user_email),
            ]
            
            # Generate unique tags for each animal
            for name, species, weight, age, gender, email in sample_animals:
                # Get the next available tag number for this species
                prefix_map = {'Cow': 'C', 'Goat': 'G', 'Sheep': 'S', 'Buffalo': 'B', 'Horse': 'H'}
                prefix = prefix_map.get(species, 'A')
                
                cursor.execute("SELECT tag FROM animals WHERE tag LIKE ? ORDER BY tag DESC LIMIT 1", (f'{prefix}-%',))
                last_tag = cursor.fetchone()
                
                if last_tag:
                    try:
                        num = int(last_tag[0].split('-')[1])
                        new_tag = f"{prefix}-{str(num + 1).zfill(3)}"
                    except:
                        new_tag = f"{prefix}-001"
                else:
                    new_tag = f"{prefix}-001"
                
                # Insert the animal with generated tag
                cursor.execute('''
                    INSERT INTO animals (tag, name, species, weight, age, gender, user_email)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (new_tag, name, species, weight, age, gender, email))
            
            conn.commit()
    except sqlite3.OperationalError:
        # Table doesn't exist yet, will be created on app init
        pass
    
    conn.close()

def login_vet(email, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vets WHERE email = ?", (email,))
    vet = cursor.fetchone()
    conn.close()

    if not vet:
        return 'not_found'
    
    # Check password (index 3 for new schema: id, full_name, email, password, license_id, region)
    if vet[3] == password:
        session['vet'] = vet[1]  # full_name
        session['vet_email'] = vet[2]  # email
        session['vet_license'] = vet[4]  # license_id
        session['vet_region'] = vet[5]  # region
        return 'success'
    return 'invalid_password'

def get_user_by_email(email):
    if not email:
        return None
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'full_name': user[1],
            'email': user[2],
            'mobile': user[3],
            'age': user[5],
            'gender': user[6]
        }
    return None

def get_vet_by_email(email):
    if not email:
        return None
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vets WHERE email = ?", (email,))
    vet = cursor.fetchone()
    conn.close()
    
    if vet:
        return {
            'id': vet[0],
            'full_name': vet[1],
            'email': vet[2],
            'license_id': vet[4],
            'region': vet[5]
        }
    return None
