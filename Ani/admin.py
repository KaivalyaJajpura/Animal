import sqlite3
from flask import session, render_template, request, redirect, flash, url_for

def login_admin(username, password):
    """Login admin user"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
    admin = cursor.fetchone()
    conn.close()

    if admin:
        session['admin'] = admin[1]  # username
        session['admin_id'] = admin[0]  # id
        return 'success'
    return 'invalid_credentials'

def get_user_species(user_email):
    """Get species and their counts for a specific user"""
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT species, COUNT(*) as count
        FROM animals
        WHERE user_email = ?
        GROUP BY species
        ORDER BY species
    """, (user_email,))
    species = cursor.fetchall()
    conn.close()
    return species

def get_all_users():
    """Get all users from database with animal count and species info"""
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.full_name, u.email, u.mobile, u.age, u.gender,
               COUNT(a.id) as animal_count
        FROM users u
        LEFT JOIN animals a ON u.email = a.user_email
        GROUP BY u.id, u.full_name, u.email, u.mobile, u.age, u.gender
        ORDER BY u.full_name
    """)
    users = cursor.fetchall()
    
    # Convert Row objects to dicts and add species information for each user
    users_list = []
    for user in users:
        user_dict = dict(user)
        user_dict['species_list'] = get_user_species(user['email'])
        users_list.append(user_dict)
    
    conn.close()
    return users_list

def get_all_vets():
    """Get all vets from database"""
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, email, license_id, region FROM vets")
    vets = cursor.fetchall()
    conn.close()
    return vets

def get_user_statistics():
    """Get user statistics"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vets")
    total_vets = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM animals")
    total_animals = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM health_readings")
    total_readings = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_users': total_users,
        'total_vets': total_vets,
        'total_animals': total_animals,
        'total_readings': total_readings
    }

def delete_user(user_id):
    """Delete a user"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Get user email first
        cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user:
            user_email = user[0]
            # Delete related records
            cursor.execute("DELETE FROM animals WHERE user_email = ?", (user_email,))
            cursor.execute("DELETE FROM notifications WHERE user_email = ?", (user_email,))
            cursor.execute("DELETE FROM appointment_queue WHERE user_email = ?", (user_email,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        print(f"Error deleting user: {e}")
    
    return False

def delete_vet(vet_id):
    """Delete a vet"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vets WHERE id = ?", (vet_id,))
        cursor.execute("DELETE FROM vet_notifications WHERE animal_tag IN (SELECT animal_tag FROM appointment_queue)")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting vet: {e}")
    
    return False

def update_user(user_id, full_name, email, mobile, age, gender):
    """Update user information"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET full_name = ?, email = ?, mobile = ?, age = ?, gender = ?
            WHERE id = ?
        """, (full_name, email, mobile, age, gender, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating user: {e}")
        return False

def update_vet(vet_id, full_name, email, license_id, region):
    """Update vet information"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE vets 
            SET full_name = ?, email = ?, license_id = ?, region = ?
            WHERE id = ?
        """, (full_name, email, license_id, region, vet_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating vet: {e}")
        return False
