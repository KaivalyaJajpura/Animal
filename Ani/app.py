from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify, Response, send_from_directory
import sqlite3
import traceback
import sys
from werkzeug.security import generate_password_hash
from login import login_user, login_vet, get_user_by_email, get_vet_by_email
from admin import login_admin, get_all_users, get_all_vets, get_user_statistics, delete_user, delete_vet, update_user, update_vet
from user import init_animals_table, add_animal, get_animals_by_user, get_all_animals, get_animal_by_tag, update_animal, assign_sample_animals_to_user, deactivate_animal, get_inactive_animals_by_user, get_all_animals_by_user
from simulate import get_current_health_data, generate_readings_history, get_species_normal_ranges, load_previous_readings_from_db
import os
from datetime import datetime, timedelta
import time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import io
import openpyxl
import csv
import threading
from werkzeug.utils import secure_filename
import base64
import json
import numpy as np
from PIL import Image

# Keras will be imported lazily when needed (avoid Python 3.13 compatibility issues)

app = Flask(__name__, template_folder='Templates', static_folder='Static')

# Environment-aware configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secure-key-change-in-production-12345')
app.config['DEBUG'] = FLASK_ENV == 'development'

# Database configuration
DB_PATH = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'users.db'))

# Global scheduler
scheduler = None

# Global Keras model and labels (loaded once at startup)
keras_model = None
keras_labels = []

def load_keras_model():
    """Load the Keras model and labels once at startup"""
    global keras_model, keras_labels
    
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Model', 'keras_model.h5')
    labels_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Model', 'labels.txt')
    
    try:
        # Use tf_keras for legacy Teachable Machine model support
        import tf_keras as keras
        
        # Load the Keras model with legacy H5 format
        keras_model = keras.models.load_model(model_path, compile=False)
        print(f"[{datetime.now()}] Keras model loaded successfully from {model_path}")
        
        # Load the labels
        with open(labels_path, 'r') as f:
            keras_labels = [line.strip().split(' ', 1)[1] if ' ' in line.strip() else line.strip() for line in f.readlines()]
        print(f"[{datetime.now()}] Labels loaded: {keras_labels}")
        
        # Warm-up prediction to optimize model for faster subsequent predictions
        dummy_input = np.zeros((1, 224, 224, 3), dtype=np.float32)
        keras_model.predict(dummy_input, verbose=0)
        print(f"[{datetime.now()}] Model warm-up complete - ready for fast predictions")
        
    except Exception as e:
        print(f"Error loading Keras model: {e}")
        keras_model = None
        keras_labels = []

def generate_health_reading_for_animal(animal_tag, species):
    """Generate and save a health reading for an animal"""
    try:
        health_data = get_current_health_data(animal_tag, species)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO health_readings (animal_tag, heart_rate, body_temp, blood_pressure, movement, health_index, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            animal_tag,
            health_data['heart_rate'],
            health_data['body_temp'],
            health_data['blood_pressure'],
            health_data['movement'],
            health_data['health_index'],
            health_data['status'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        conn.commit()
        conn.close()
        print(f"[{datetime.now()}] Generated health reading for {animal_tag}")
        return True
    except Exception as e:
        print(f"Error generating reading for {animal_tag}: {e}")
        return False

def scheduled_health_reading_job():
    """Background job that generates readings for ALL active animals every hour"""
    print(f"\n[{datetime.now()}] Running scheduled health readings job...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all active animals
        cursor.execute('SELECT tag, species FROM animals WHERE is_active = 1')
        animals = cursor.fetchall()
        conn.close()
        
        if not animals:
            print("No active animals found")
            return
        
        count = 0
        for animal in animals:
            if generate_health_reading_for_animal(animal['tag'], animal['species']):
                count += 1
        
        # Update the last reading time in a file for client-side sync
        with open('last_reading_time.txt', 'w') as f:
            f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        print(f"[{datetime.now()}] Generated readings for {count} animals")
        
    except Exception as e:
        print(f"Error in scheduled job: {e}")

def start_scheduler():
    """Start the background scheduler for health readings every 5 minutes"""
    global scheduler
    
    if scheduler is None:
        scheduler = BackgroundScheduler()
        # Run every 5 minutes
        scheduler.add_job(func=scheduled_health_reading_job, trigger='interval', minutes=5, id='health_readings_job')
        scheduler.start()
        print(f"[{datetime.now()}] Background scheduler started - readings every 5 minutes")
        
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())

def get_last_scheduled_reading_time():
    """Get the last time a scheduled reading was taken"""
    try:
        if os.path.exists('last_reading_time.txt'):
            with open('last_reading_time.txt', 'r') as f:
                return f.read().strip()
    except:
        pass
    return None

def get_next_scheduled_reading_time():
    """Calculate when the next scheduled reading will occur"""
    last_time = get_last_scheduled_reading_time()
    if last_time:
        try:
            last_dt = datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')
            next_dt = last_dt + timedelta(minutes=5)
            return next_dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    return None

def init_db():
    # Initialize users.db
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.exists(DB_PATH):
        conn1 = sqlite3.connect(DB_PATH)
        if os.path.exists(schema_path):
            with open(schema_path) as f:
                conn1.executescript(f.read())
        conn1.commit()
        conn1.close()
    else:
        # Add missing columns/tables if they don't exist
        conn1 = sqlite3.connect(DB_PATH)
        cursor1 = conn1.cursor()
        try:
            cursor1.execute("ALTER TABLE users ADD COLUMN age INTEGER")
            conn1.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            cursor1.execute("ALTER TABLE users ADD COLUMN gender TEXT")
            conn1.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add is_active column to animals table if it doesn't exist
        try:
            cursor1.execute("ALTER TABLE animals ADD COLUMN is_active INTEGER DEFAULT 1")
            conn1.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Create animals table if it doesn't exist
        cursor1.execute('''
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
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_email) REFERENCES users(email)
            )
        ''')
        
        # Create health_readings table if it doesn't exist
        cursor1.execute('''
            CREATE TABLE IF NOT EXISTS health_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_tag TEXT NOT NULL,
                heart_rate REAL NOT NULL,
                body_temp REAL NOT NULL,
                blood_pressure INTEGER NOT NULL,
                movement TEXT NOT NULL,
                health_index REAL NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_tag) REFERENCES animals(tag)
            )
        ''')
        
        # Create removed_animals_history table if it doesn't exist
        cursor1.execute('''
            CREATE TABLE IF NOT EXISTS removed_animals_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_tag TEXT NOT NULL,
                animal_name TEXT NOT NULL,
                species TEXT NOT NULL,
                user_email TEXT NOT NULL,
                removed_date TEXT DEFAULT CURRENT_TIMESTAMP,
                last_temp REAL,
                last_heart_rate REAL,
                last_health_status TEXT,
                last_health_index REAL
            )
        ''')
        
        # Create admin table if it doesn't exist
        cursor1.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                full_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert admin account if it doesn't exist
        cursor1.execute("INSERT OR IGNORE INTO admin (username, password, full_name) VALUES (?, ?, ?)",
                       ('Nikhil_jaroli', '8288', 'Admin'))
        
        # Create notifications table if it doesn't exist
        cursor1.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                animal_tag TEXT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT DEFAULT 'info',
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users(email)
            )
        ''')
        
        # Create appointment queue table if it doesn't exist
        cursor1.execute('''
            CREATE TABLE IF NOT EXISTS appointment_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_tag TEXT NOT NULL,
                user_email TEXT NOT NULL,
                owner_name TEXT,
                owner_mobile TEXT,
                health_status TEXT NOT NULL,
                health_index REAL,
                appointment_time TEXT DEFAULT CURRENT_TIMESTAMP,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                FOREIGN KEY (animal_tag) REFERENCES animals(tag),
                FOREIGN KEY (user_email) REFERENCES users(email)
            )
        ''')
        cursor1.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_appointment_pending_unique
            ON appointment_queue(animal_tag, user_email, status)
            WHERE status = 'pending'
        ''')
        conn1.commit()
        conn1.close()
    
    # Always ensure appointment_queue and vet_notifications tables exist (for existing databases)
    conn1 = sqlite3.connect(DB_PATH)
    cursor1 = conn1.cursor()
    cursor1.execute('''
        CREATE TABLE IF NOT EXISTS appointment_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_tag TEXT NOT NULL,
            user_email TEXT NOT NULL,
            owner_name TEXT,
            owner_mobile TEXT,
            health_status TEXT NOT NULL,
            health_index REAL,
            appointment_time TEXT DEFAULT CURRENT_TIMESTAMP,
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            notes TEXT
        )
    ''')
    # Prevent duplicate pending appointments per animal/user
    cursor1.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_appointment_pending_unique
        ON appointment_queue(animal_tag, user_email, status)
        WHERE status = 'pending'
    ''')
    
    # Add mobile column to vets table if it doesn't exist
    try:
        cursor1.execute("ALTER TABLE vets ADD COLUMN mobile TEXT")
        conn1.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    cursor1.execute('''
        CREATE TABLE IF NOT EXISTS vet_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_tag TEXT,
            owner_name TEXT,
            owner_mobile TEXT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create treatment_history table for storing vet treatments
    cursor1.execute('''
        CREATE TABLE IF NOT EXISTS treatment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_tag TEXT NOT NULL,
            animal_name TEXT,
            species TEXT,
            user_email TEXT NOT NULL,
            owner_name TEXT,
            owner_mobile TEXT,
            health_status TEXT,
            health_index REAL,
            treatment TEXT NOT NULL,
            notes TEXT,
            treated_date TEXT DEFAULT CURRENT_TIMESTAMP,
            vet_email TEXT,
            FOREIGN KEY (animal_tag) REFERENCES animals(tag),
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    ''')
    
    # Create confirmed_appointments table for animals confirmed to visit vet
    cursor1.execute('''
        CREATE TABLE IF NOT EXISTS confirmed_appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_tag TEXT NOT NULL,
            animal_name TEXT,
            species TEXT,
            user_email TEXT NOT NULL,
            owner_name TEXT,
            owner_mobile TEXT,
            health_status TEXT,
            health_index REAL,
            confirmed_date TEXT DEFAULT CURRENT_TIMESTAMP,
            appointment_id INTEGER,
            notes TEXT,
            vet_email TEXT,
            FOREIGN KEY (animal_tag) REFERENCES animals(tag),
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    ''')
    conn1.commit()
    conn1.close()

    # Initialize vets.db
    if not os.path.exists('vets.db'):
        conn2 = sqlite3.connect('vets.db')
        with open(schema_path) as f:
            conn2.executescript(f.read())
        conn2.commit()
        conn2.close()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        result = login_user(email, password)
        if result == 'success':
            session.permanent = True
            if is_ajax:
                return jsonify({'status': 'success', 'message': 'Successfully signing in'})
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        elif result == 'not_found':
            if is_ajax:
                return jsonify({'status': 'error', 'message': 'Account not found. Please create a new account using Sign Up.'})
            flash("Account not found. Please create a new account.", "error")
        else:
            if is_ajax:
                return jsonify({'status': 'error', 'message': 'Invalid password, try again'})
            flash("Invalid password", "error")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = generate_password_hash(request.form.get('password'))

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (full_name, email, mobile, password) VALUES (?, ?, ?, ?)",
                           (full_name, email, mobile, password))
            conn.commit()
            
            # Auto-login the user after successful signup
            session['user'] = full_name
            session['user_email'] = email
            
            return jsonify({
                'status': 'success', 
                'message': 'Account created successfully!',
                'redirect': url_for('dashboard')
            })
        except sqlite3.IntegrityError:
            return jsonify({'status': 'error', 'message': 'Email already exists'})
        finally:
            conn.close()
    return render_template('signup.html')

@app.route('/vetlogin', methods=['GET', 'POST'])
def vetlogin():
    if 'vet' in session:
        return redirect(url_for('vetdashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        result = login_vet(email, password)
        if result == 'success':
            if is_ajax:
                return jsonify({'status': 'success', 'message': 'Successfully signing in'})
            flash("Login successful!", "success")
            return redirect(url_for('vetdashboard'))
        elif result == 'not_found':
            if is_ajax:
                return jsonify({'status': 'error', 'message': 'Account not found'})
            flash("Account not found", "error")
        else:
            if is_ajax:
                return jsonify({'status': 'error', 'message': 'Invalid password, try again'})
            flash("Invalid password", "error")
    return render_template('vetlogin.html')

# Admin Routes
@app.route('/admin_login')
def admin_login():
    if 'admin' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin_login_submit', methods=['POST'])
def admin_login_submit():
    username = request.form.get('username')
    password = request.form.get('password')
    
    result = login_admin(username, password)
    if result == 'success':
        flash("Admin login successful!", "success")
        return redirect(url_for('admin_dashboard'))
    else:
        # Return HTML with JavaScript alert for invalid credentials
        return render_template('admin_login.html', show_error=True)

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        flash("Please login as admin first", "error")
        return redirect(url_for('admin_login'))
    
    stats = get_user_statistics()
    return render_template('admin_dashboard.html', admin=session.get('admin'), stats=stats)

@app.route('/admin_user')
def admin_user():
    if 'admin' not in session:
        flash("Please login as admin first", "error")
        return redirect(url_for('admin_login'))
    
    users = get_all_users()
    
    # Get total animals treated from treatment_history
    total_animals_treated = 0
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM treatment_history')
        result = cursor.fetchone()
        if result is not None:
            total_animals_treated = result[0]
        conn.close()
        print(f"[ADMIN USER] Total animals treated: {total_animals_treated}")
    except Exception as e:
        print(f"Error fetching total animals treated: {e}")
        import traceback
        traceback.print_exc()
        total_animals_treated = 0
    
    return render_template('admin_user.html', admin=session.get('admin'), users=users, total_animals_treated=total_animals_treated)

@app.route('/admin_vet')
def admin_vet():
    if 'admin' not in session:
        flash("Please login as admin first", "error")
        return redirect(url_for('admin_login'))
    
    vets = get_all_vets()
    
    # Get statistics for each vet
    total_animals_treated = 0
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        vet_stats = {}
        for vet in vets:
            vet_email = vet['email']
            
            # Count treated animals for this vet
            cursor.execute('''
                SELECT COUNT(DISTINCT animal_tag) FROM treatment_history 
                WHERE vet_email = ?
            ''', (vet_email,))
            result = cursor.fetchone()
            treated_count = result[0] if result else 0
            
            # Count animals to visit (confirmed appointments) for this vet
            cursor.execute('''
                SELECT COUNT(*) FROM confirmed_appointments 
                WHERE vet_email = ?
            ''', (vet_email,))
            result = cursor.fetchone()
            to_visit_count = result[0] if result else 0
            
            vet_stats[vet_email] = {
                'treated': treated_count,
                'to_visit': to_visit_count
            }
        
        # Get total animals treated across all vets (count all treatment records)
        cursor.execute('SELECT COUNT(*) FROM treatment_history')
        result = cursor.fetchone()
        if result is not None:
            total_animals_treated = result[0]
        print(f"[ADMIN VET] Total animals treated: {total_animals_treated}")
        
        conn.close()
    except Exception as e:
        print(f"Error fetching vet statistics: {e}")
        import traceback
        traceback.print_exc()
        vet_stats = {}
        total_animals_treated = 0
    
    return render_template('admin_vet.html', admin=session.get('admin'), vets=vets, vet_stats=vet_stats, total_animals_treated=total_animals_treated)

@app.route('/api/admin/user/<int:user_id>', methods=['DELETE'])
def delete_admin_user(user_id):
    if 'admin' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    if delete_user(user_id):
        return jsonify({'status': 'success', 'message': 'User deleted successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to delete user'}), 500

@app.route('/api/admin/vet/<int:vet_id>', methods=['DELETE'])
def delete_admin_vet(vet_id):
    if 'admin' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    if delete_vet(vet_id):
        return jsonify({'status': 'success', 'message': 'Vet deleted successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to delete vet'}), 500

@app.route('/api/admin/user/<int:user_id>', methods=['PUT', 'POST'])
def update_admin_user(user_id):
    if 'admin' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    if update_user(user_id, data.get('full_name'), data.get('email'), 
                   data.get('mobile'), data.get('age'), data.get('gender')):
        return jsonify({'status': 'success', 'message': 'User updated successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to update user'}), 500

@app.route('/api/admin/vet/<int:vet_id>', methods=['PUT', 'POST'])
def update_admin_vet(vet_id):
    if 'admin' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    if update_vet(vet_id, data.get('full_name'), data.get('email'), 
                  data.get('license_id'), data.get('region')):
        return jsonify({'status': 'success', 'message': 'Vet updated successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to update vet'}), 500

@app.route('/api/admin/add_vet', methods=['POST'])
def add_vet():
    if 'admin' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        mobile = data.get('mobile')
        region = data.get('region')
        
        if not all([full_name, email, password, mobile, region]):
            return jsonify({'status': 'error', 'message': 'All fields are required'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if mobile column exists and add it if it doesn't
        cursor.execute("PRAGMA table_info(vets)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'mobile' not in columns:
            cursor.execute("ALTER TABLE vets ADD COLUMN mobile TEXT")
            conn.commit()
        
        # Auto-generate license ID
        cursor.execute("SELECT MAX(CAST(SUBSTR(license_id, 5) AS INTEGER)) FROM vets WHERE license_id LIKE 'VET-%'")
        result = cursor.fetchone()
        max_id = result[0] if result[0] else 0
        license_id = f"VET-{max_id + 1001}"
        
        cursor.execute("""
            INSERT INTO vets (full_name, email, password, license_id, region, mobile)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (full_name, email, password, license_id, region, mobile))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Veterinarian added successfully', 'license_id': license_id})
    except sqlite3.IntegrityError as e:
        error_msg = str(e).lower()
        if 'email' in error_msg:
            return jsonify({'status': 'error', 'message': 'Email already exists'}), 400
        return jsonify({'status': 'error', 'message': 'Error adding veterinarian'}), 400
    except Exception as e:
        print(f"Error adding vet: {e}")  # Log to console
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    session.pop('admin_id', None)
    flash("You have been logged out", "success")
    return redirect(url_for('admin_login'))

# User Dashboard Routes
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Please login first", "error")
        return redirect(url_for('login'))
    animals = get_animals_by_user(session.get('user_email'))
    return render_template('dashboard.html', user=session.get('user'), animals=animals)

@app.route('/animalinfo')
def animalinfo():
    if 'user' not in session:
        return redirect(url_for('login'))
    animals = get_animals_by_user(session.get('user_email'))
    return render_template('animalinfo.html', user=session.get('user'), animals=animals)

@app.route('/userinfo')
def userinfo():
    if 'user' not in session:
        return redirect(url_for('login'))
    # Get full user data from database
    user_data = get_user_by_email(session.get('user_email'))
    # Get only active animals for this user
    animals = get_animals_by_user(session.get('user_email'))
    return render_template('userinfo.html', user=session.get('user'), user_data=user_data, animals=animals)

@app.route('/api/update-userinfo', methods=['POST'])
def update_userinfo():
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        email = session.get('user_email')
        
        full_name = data.get('full_name')
        mobile = data.get('mobile')
        age = data.get('age')
        gender = data.get('gender')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET full_name = ?, mobile = ?, age = ?, gender = ? 
            WHERE email = ?
        """, (full_name, mobile, age, gender, email))
        
        conn.commit()
        conn.close()
        
        # Update session with new name
        session['user'] = full_name
        
        return jsonify({'status': 'success', 'message': 'User information updated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_email = session.get('user_email')
    
    # Get removed animals history from database
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all removed animals from the history table
        cursor.execute('''
            SELECT * FROM removed_animals_history
            WHERE user_email = ?
            ORDER BY removed_date DESC
        ''', (user_email,))
        
        rows = cursor.fetchall()
        conn.close()
        
        removed_history = []
        for row in rows:
            removed_history.append({
                'id': row['id'],
                'animal_tag': row['animal_tag'],
                'animal_name': row['animal_name'],
                'species': row['species'],
                'removed_date': row['removed_date'],
                'last_temp': row['last_temp'],
                'last_heart_rate': row['last_heart_rate'],
                'last_health_status': row['last_health_status'],
                'last_health_index': row['last_health_index']
            })
    except Exception as e:
        removed_history = []
        print(f"Error loading removed animals history: {e}")
    
    return render_template('history.html', user=session.get('user'), removed_history=removed_history)

@app.route('/features')
def features():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('features.html', user=session.get('user'))

@app.route('/imgdetect')
def imgdetect():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('ImgDetect.html', user=session.get('user'))

@app.route('/image-predict')
def image_predict():
    """GET route that renders ImgDetect.html for image prediction"""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('ImgDetect.html', user=session.get('user'))

@app.route('/predict-image', methods=['POST'])
def predict_image():
    """POST route that accepts an uploaded image and returns prediction"""
    global keras_model, keras_labels
    
    # Check if model is still loading in background
    if keras_model is None:
        return jsonify({'error': 'Model is still loading. Please wait a few seconds and try again.'}), 503
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    try:
        # Read and process the image using PIL (fast)
        img = Image.open(file.stream).convert('RGB')
        
        # Resize to 224x224 using BILINEAR for speed (LANCZOS is slower)
        img = img.resize((224, 224), Image.BILINEAR)
        
        # Convert to numpy array and normalize to [0, 1]
        img_array = np.array(img, dtype=np.float32) / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        # Run prediction
        predictions = keras_model.predict(img_array, verbose=0)
        
        # Add delay for better UX (simulates processing time)
        time.sleep(4)
        
        # Get the predicted class index and confidence
        predicted_index = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_index])
        
        # Get class name
        class_name = keras_labels[predicted_index] if predicted_index < len(keras_labels) else f"Class {predicted_index}"
        
        # Parse species and disease from class name (format: "Species - Disease")
        parts = class_name.split(' - ', 1)
        species = parts[0] if len(parts) > 0 else "Unknown"
        disease = parts[1] if len(parts) > 1 else class_name
        
        # Return only top prediction with species and disease separated
        return jsonify({
            'success': True,
            'className': class_name,
            'species': species,
            'disease': disease,
            'confidence': confidence,
            'predictions': [{
                'className': class_name,
                'species': species,
                'disease': disease,
                'probability': confidence
            }]  
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Static/Model/<path:filename>')
def serve_model(filename):
    """Serve model files with proper CORS headers"""
    import os
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Static', 'Model')
    response = send_from_directory(model_dir, filename)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Cache-Control'] = 'no-cache'
    if filename.endswith('.bin'):
        response.headers['Content-Type'] = 'application/octet-stream'
    elif filename.endswith('.json'):
        response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/export')
def export():
    if 'user' not in session:
        return redirect(url_for('login'))
    animals = get_animals_by_user(session.get('user_email'))
    return render_template('export.html', user=session.get('user'), animals=animals)

@app.route('/api/export-pdf', methods=['POST'])
def api_export_pdf():
    """Generate PDF health report for selected animal(s)"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        animal_tag = data.get('animal_tag')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        user_email = session.get('user_email')
        
        if not animal_tag or not date_from or not date_to:
            return jsonify({'status': 'error', 'message': 'Missing required parameters'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get animal(s) and their health readings
        if animal_tag == 'all':
            # Get all user's animals
            cursor.execute('SELECT * FROM animals WHERE user_email = ? AND (is_active = 1 OR is_active IS NULL)', (user_email,))
            animals = cursor.fetchall()
            animal_tags = [a['tag'] for a in animals]
        else:
            # Get specific animal
            cursor.execute('SELECT * FROM animals WHERE tag = ? AND user_email = ?', (animal_tag, user_email))
            animal = cursor.fetchone()
            if not animal:
                conn.close()
                return jsonify({'status': 'error', 'message': 'Animal not found'}), 404
            animals = [animal]
            animal_tags = [animal_tag]
        
        # Get health readings for the date range
        all_readings = []
        for tag in animal_tags:
            cursor.execute('''
                SELECT * FROM health_readings 
                WHERE animal_tag = ? 
                AND date(timestamp) >= date(?) 
                AND date(timestamp) <= date(?)
                ORDER BY timestamp DESC
            ''', (tag, date_from, date_to))
            readings = cursor.fetchall()
            all_readings.extend(readings)
        
        conn.close()
        
        # Generate PDF content
        pdf_content = generate_pdf_report(animals, all_readings, date_from, date_to, user_email)
        
        return Response(
            pdf_content,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=Health_Report_{animal_tag}_{date_from}_to_{date_to}.pdf',
                'Content-Transfer-Encoding': 'binary',
                'Accept-Ranges': 'none',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Content-Type-Options': 'nosniff'
            }
        )
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def generate_pdf_report(animals, readings, date_from, date_to, user_email):
    """Generate a simple PDF report using basic text formatting"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#13ec5b')
    )
    
    # Header style
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.HexColor('#111813')
    )
    
    # Normal text style
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Title
    story.append(Paragraph("🐄 Ani-Health - Livestock Health Report", title_style))
    story.append(Spacer(1, 12))
    
    # Report info
    story.append(Paragraph(f"<b>Report Period:</b> {date_from} to {date_to}", normal_style))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Paragraph(f"<b>User:</b> {user_email}", normal_style))
    story.append(Spacer(1, 20))
    
    # Animal Summary
    story.append(Paragraph("📋 Animal Summary", header_style))
    
    animal_data = [['Tag', 'Name', 'Species', 'Weight (kg)', 'Age (years)', 'Gender']]
    for animal in animals:
        animal_data.append([
            animal['tag'],
            animal['name'],
            animal['species'],
            str(animal['weight'] or 'N/A'),
            str(animal['age'] or 'N/A'),
            animal['gender'] or 'N/A'
        ])
    
    animal_table = Table(animal_data, colWidths=[60, 80, 70, 70, 70, 60])
    animal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#13ec5b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f6f8f6')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#111813')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    story.append(animal_table)
    story.append(Spacer(1, 20))
    
    # Health Readings
    story.append(Paragraph("📊 Health Readings", header_style))
    
    if readings:
        # Calculate statistics per animal
        stats_by_animal = {}
        for reading in readings:
            tag = reading['animal_tag']
            if tag not in stats_by_animal:
                stats_by_animal[tag] = {
                    'temps': [],
                    'hrs': [],
                    'indexes': [],
                    'statuses': []
                }
            stats_by_animal[tag]['temps'].append(reading['body_temp'])
            stats_by_animal[tag]['hrs'].append(reading['heart_rate'])
            stats_by_animal[tag]['indexes'].append(reading['health_index'])
            stats_by_animal[tag]['statuses'].append(reading['status'])
        
        # Statistics summary
        stats_data = [['Animal Tag', 'Avg Temp (°C)', 'Avg HR (bpm)', 'Avg Health Index', 'Most Common Status', 'Readings']]
        for tag, stats in stats_by_animal.items():
            avg_temp = round(sum(stats['temps']) / len(stats['temps']), 1) if stats['temps'] else 'N/A'
            avg_hr = round(sum(stats['hrs']) / len(stats['hrs']), 1) if stats['hrs'] else 'N/A'
            avg_index = round(sum(stats['indexes']) / len(stats['indexes']), 1) if stats['indexes'] else 'N/A'
            most_common_status = max(set(stats['statuses']), key=stats['statuses'].count) if stats['statuses'] else 'N/A'
            stats_data.append([tag, str(avg_temp), str(avg_hr), str(avg_index), most_common_status, str(len(stats['temps']))])
        
        stats_table = Table(stats_data, colWidths=[70, 70, 70, 90, 90, 60])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#111813')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Detailed readings table (last 20)
        story.append(Paragraph("📝 Recent Readings (Last 20)", header_style))
        
        readings_data = [['Timestamp', 'Tag', 'Temp', 'HR', 'BP', 'Movement', 'Index', 'Status']]
        for reading in readings[:20]:
            readings_data.append([
                reading['timestamp'][:16] if reading['timestamp'] else 'N/A',
                reading['animal_tag'],
                f"{reading['body_temp']}°C",
                f"{reading['heart_rate']} bpm",
                reading['blood_pressure'] or 'N/A',
                reading['movement'] or 'N/A',
                f"{reading['health_index']}%",
                reading['status']
            ])
        
        readings_table = Table(readings_data, colWidths=[85, 50, 50, 55, 55, 55, 45, 55])
        readings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#111813')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        story.append(readings_table)
    else:
        story.append(Paragraph("No health readings found for the selected period.", normal_style))
    
    story.append(Spacer(1, 30))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray
    )
    story.append(Paragraph("---", footer_style))
    story.append(Paragraph("This report was automatically generated by Ani-Health Livestock Monitoring System.", footer_style))
    story.append(Paragraph("For any concerns about animal health, please consult with a veterinarian.", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

@app.route('/notifications')
def notifications():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Fetch notifications from database
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM notifications 
            WHERE user_email = ? 
            ORDER BY created_at DESC 
            LIMIT 50
        ''', (session.get('user_email'),))
        
        rows = cursor.fetchall()
        conn.close()
        
        notification_list = []
        for row in rows:
            notification_list.append({
                'id': row['id'],
                'animal_tag': row['animal_tag'],
                'title': row['title'],
                'message': row['message'],
                'notification_type': row['notification_type'],
                'is_read': row['is_read'],
                'created_at': row['created_at']
            })
    except Exception as e:
        notification_list = []
        print(f"Error loading notifications: {e}")
    
    return render_template('notifications.html', user=session.get('user'), notifications=notification_list)

@app.route('/settings')
def settings():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Get user email from session
    user_email = session.get('user_email')
    
    # Fallback: if user_email not in session, try to find user by name
    if not user_email:
        user_name = session.get('user')
        if user_name:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE full_name = ?", (user_name,))
            result = cursor.fetchone()
            conn.close()
            if result:
                user_email = result[0]
                session['user_email'] = user_email  # Store for future use
    
    # Get full user data from database
    user_data = get_user_by_email(user_email)
    print(f"Settings - user_email: {user_email}, user_data: {user_data}")
    return render_template('settings.html', user=session.get('user'), user_data=user_data)

# Vet Dashboard Routes
@app.route('/vetdashboard')
def vetdashboard():
    if 'vet' not in session:
        flash("Please login first", "error")
        return redirect(url_for('vetlogin'))
    vet_data = get_vet_by_email(session.get('vet_email'))
    
    # Get dashboard stats
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Critical alerts (Ill/Critical status animals with pending appointments)
    cursor.execute('''SELECT COUNT(*) as count FROM appointment_queue 
                     WHERE status = 'pending' AND (health_status = 'Ill' OR health_status = 'Critical')''')
    critical_alerts = cursor.fetchone()['count']
    
    # Under observation (Warning status)
    cursor.execute('''SELECT COUNT(*) as count FROM appointment_queue 
                     WHERE status = 'pending' AND health_status = 'Warning' ''')
    under_observation = cursor.fetchone()['count']
    
    # Active notifications (all pending appointments)
    cursor.execute('''SELECT COUNT(*) as count FROM appointment_queue WHERE status = 'pending' ''')
    active_notifications = cursor.fetchone()['count']
    
    # Total animals treated
    cursor.execute('''SELECT COUNT(*) as count FROM appointment_queue WHERE status = 'treated' ''')
    total_treated = cursor.fetchone()['count']
    
    conn.close()
    
    stats = {
        'critical_alerts': critical_alerts,
        'under_observation': under_observation,
        'active_notifications': active_notifications,
        'total_treated': total_treated
    }
    
    return render_template('vetdashboard.html', vet=session.get('vet'), vet_data=vet_data, stats=stats)

@app.route('/vet-notifications')
def vet_notifications():
    if 'vet' not in session:
        return redirect(url_for('vetlogin'))
    vet_data = get_vet_by_email(session.get('vet_email'))
    return render_template('vet-notifications.html', vet=session.get('vet'), vet_data=vet_data)

@app.route('/vet-history')
def vet_history():
    if 'vet' not in session:
        return redirect(url_for('vetlogin'))
    vet_data = get_vet_by_email(session.get('vet_email'))
    return render_template('vet-history.html', vet=session.get('vet'), vet_data=vet_data)

@app.route('/vet-settings')
def vet_settings():
    if 'vet' not in session:
        return redirect(url_for('vetlogin'))
    # Get full vet data from database
    vet_data = get_vet_by_email(session.get('vet_email'))
    return render_template('vet-settings.html', vet=session.get('vet'), vet_data=vet_data)

# Animal API Routes
@app.route('/api/animals', methods=['GET'])
def api_get_animals():
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    animals = get_animals_by_user(session.get('user_email'))
    return jsonify({'status': 'success', 'animals': animals})

@app.route('/api/animals', methods=['POST'])
def api_add_animal():
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        name = data.get('name')
        species = data.get('species')
        weight = data.get('weight')
        age = data.get('age')
        gender = data.get('gender')
        user_email = session.get('user_email')
        
        if not name or not species:
            return jsonify({'status': 'error', 'message': 'Name and species are required'}), 400
        
        animal = add_animal(name, species, weight, age, gender, user_email)
        
        if animal:
            return jsonify({'status': 'success', 'message': 'Animal added successfully', 'animal': animal})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to add animal'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/animals/bulk/upload', methods=['POST'])
def api_bulk_upload_animals():
    """Handle bulk upload of animals from Excel/CSV file"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    file = request.files['file']
    user_email = session.get('user_email')
    success_count = 0
    errors = []
    
    try:
        # Check file type and read accordingly
        if file.filename.endswith('.csv'):
            # Handle CSV
            stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
            csv_reader = csv.DictReader(stream)
            rows = list(csv_reader)
        else:
            # Handle Excel (.xlsx, .xls)
            wb = openpyxl.load_workbook(file.stream)
            ws = wb.active
            rows = []
            headers = []
            
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i == 0:
                    headers = [str(cell).lower().strip() for cell in row if cell]
                else:
                    if any(cell is not None for cell in row):
                        row_dict = {}
                        for j, header in enumerate(headers):
                            if j < len(row):
                                row_dict[header] = row[j]
                        rows.append(row_dict)
        
        # Process each row
        for row_num, row_data in enumerate(rows, start=2):  # Start at 2 because row 1 is headers
            try:
                # Get values from row - handle different column name variations
                name = None
                species = None
                weight = None
                age = None
                gender = None
                
                for key, value in row_data.items():
                    key_lower = str(key).lower().strip()
                    if 'name' in key_lower:
                        name = value
                    elif 'species' in key_lower:
                        species = value
                    elif 'weight' in key_lower:
                        weight = value
                    elif 'age' in key_lower:
                        age = value
                    elif 'gender' in key_lower:
                        gender = value
                
                # Validate required fields
                if not name or not name or len(str(name).strip()) == 0:
                    errors.append({'row': row_num, 'message': 'Name is required'})
                    continue
                
                if not species or len(str(species).strip()) == 0:
                    errors.append({'row': row_num, 'message': 'Species is required'})
                    continue
                
                name = str(name).strip()
                species = str(species).strip()
                
                # Validate species
                valid_species = ['Cow', 'Buffalo', 'Sheep', 'Goat', 'Horse', 'Pig']
                species_match = None
                for valid_sp in valid_species:
                    if species.lower() == valid_sp.lower():
                        species_match = valid_sp
                        break
                
                if not species_match:
                    errors.append({'row': row_num, 'message': f'Invalid species: {species}. Valid options: {", ".join(valid_species)}'})
                    continue
                
                # Convert weight and age to appropriate types
                try:
                    weight = float(weight) if weight else None
                except (ValueError, TypeError):
                    weight = None
                
                try:
                    age = int(age) if age else None
                except (ValueError, TypeError):
                    age = None
                
                # Normalize gender
                if gender:
                    gender = str(gender).strip().lower()
                    if gender not in ['male', 'female', 'm', 'f']:
                        gender = None
                    elif gender == 'm':
                        gender = 'Male'
                    elif gender == 'f':
                        gender = 'Female'
                    else:
                        gender = gender.capitalize()
                else:
                    gender = 'Female'  # Default
                
                # Add the animal
                animal = add_animal(name, species_match, weight, age, gender, user_email)
                
                if animal:
                    success_count += 1
                else:
                    errors.append({'row': row_num, 'message': 'Failed to add animal to database'})
            
            except Exception as row_error:
                errors.append({'row': row_num, 'message': str(row_error)})
        
        return jsonify({
            'status': 'success' if success_count > 0 else 'error',
            'success_count': success_count,
            'errors': errors,
            'message': f'{success_count} animals added successfully'
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error processing file: {str(e)}'}), 500

@app.route('/api/animals/status', methods=['GET'])
def api_get_animals_status():
    """Get all animals with their ACTUAL stored health status from database"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        user_email = session.get('user_email')
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all active animals for the user with their LATEST stored health reading
        cursor.execute('''
            SELECT 
                a.tag, a.name, a.species, a.weight, a.age, a.gender, a.date_added,
                h.health_index, h.status as health_status, h.timestamp as last_reading_time
            FROM animals a
            LEFT JOIN (
                SELECT animal_tag, health_index, status, timestamp
                FROM health_readings h1
                WHERE timestamp = (
                    SELECT MAX(timestamp) 
                    FROM health_readings h2 
                    WHERE h2.animal_tag = h1.animal_tag
                )
            ) h ON a.tag = h.animal_tag
            WHERE a.user_email = ? AND (a.is_active = 1 OR a.is_active IS NULL)
            ORDER BY a.date_added DESC
        ''', (user_email,))
        
        rows = cursor.fetchall()
        conn.close()
        
        animals = {}
        for row in rows:
            # Use the ACTUAL stored status, default to 'Healthy' only if no readings exist
            health_index = row['health_index'] if row['health_index'] is not None else None
            health_status = row['health_status'] if row['health_status'] is not None else 'Healthy'
            
            animals[row['tag']] = {
                'name': row['name'],
                'tag': row['tag'],
                'species': row['species'],
                'status': health_status,
                'health_index': health_index if health_index is not None else '--',
                'last_reading': row['last_reading_time']
            }
        
        return jsonify({'status': 'success', 'animals': animals})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/animals/<tag>', methods=['GET'])
def api_get_animal(tag):
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    animal = get_animal_by_tag(tag)
    if animal:
        # Verify the animal belongs to the current user
        if animal['user_email'] != session.get('user_email'):
            return jsonify({'status': 'error', 'message': 'Access denied'}), 403
        return jsonify({'status': 'success', 'animal': animal})
    return jsonify({'status': 'error', 'message': 'Animal not found'}), 404

@app.route('/api/animals/<tag>', methods=['PUT'])
def api_update_animal(tag):
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    # Verify the animal belongs to the current user
    existing_animal = get_animal_by_tag(tag)
    if not existing_animal:
        return jsonify({'status': 'error', 'message': 'Animal not found'}), 404
    if existing_animal['user_email'] != session.get('user_email'):
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        name = data.get('name')
        species = data.get('species')
        weight = data.get('weight')
        age = data.get('age')
        gender = data.get('gender')
        
        animal = update_animal(tag, name, species, weight, age, gender)
        
        if animal:
            return jsonify({'status': 'success', 'message': 'Animal updated successfully', 'animal': animal})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to update animal'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/animals/<tag>/remove', methods=['POST'])
def api_remove_animal(tag):
    """Remove/deactivate an animal (move to history)"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    # Verify the animal belongs to the current user
    existing_animal = get_animal_by_tag(tag)
    if not existing_animal:
        return jsonify({'status': 'error', 'message': 'Animal not found'}), 404
    if existing_animal['user_email'] != session.get('user_email'):
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    try:
        # Get the last health reading for this animal
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT body_temp, heart_rate, status, health_index 
            FROM health_readings 
            WHERE animal_tag = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''', (tag,))
        last_reading = cursor.fetchone()
        
        # Save to removed_animals_history
        cursor.execute('''
            INSERT INTO removed_animals_history 
            (animal_tag, animal_name, species, user_email, last_temp, last_heart_rate, last_health_status, last_health_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tag,
            existing_animal['name'],
            existing_animal['species'],
            session.get('user_email'),
            last_reading['body_temp'] if last_reading else None,
            last_reading['heart_rate'] if last_reading else None,
            last_reading['status'] if last_reading else 'N/A',
            last_reading['health_index'] if last_reading else None
        ))
        conn.commit()
        conn.close()
        
        # Deactivate the animal
        success = deactivate_animal(tag)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Animal removed and moved to history'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to remove animal'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/animals/<tag>/reactivate', methods=['POST'])
def api_reactivate_animal(tag):
    """Reactivate a treated/removed animal - add back to user's selection menu"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if animal exists and belongs to this user
        cursor.execute('SELECT * FROM animals WHERE tag = ? AND user_email = ?', 
                      (tag, session.get('user_email')))
        animal = cursor.fetchone()
        
        if not animal:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Animal not found or access denied'}), 404
        
        if animal['is_active'] == 1:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Animal is already active'}), 400
        
        # Reactivate the animal
        cursor.execute('UPDATE animals SET is_active = 1 WHERE tag = ?', (tag,))
        
        # Remove from removed_animals_history table
        cursor.execute('DELETE FROM removed_animals_history WHERE animal_tag = ? AND user_email = ?', 
                      (tag, session.get('user_email')))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success', 
            'message': f'Animal {tag} has been reactivated and added back to your selection menu'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Health Simulation API Routes
@app.route('/api/health/<tag>', methods=['GET'])
def api_get_health(tag):
    """Get current health data for an animal"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    animal = get_animal_by_tag(tag)
    if not animal:
        return jsonify({'status': 'error', 'message': 'Animal not found'}), 404
    
    # Verify the animal belongs to the current user
    if animal['user_email'] != session.get('user_email'):
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    health_data = get_current_health_data(tag, animal['species'])
    return jsonify({'status': 'success', 'health': health_data})

@app.route('/api/health/<tag>/history', methods=['GET'])
def api_get_health_history(tag):
    """Get health history for an animal"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    animal = get_animal_by_tag(tag)
    if not animal:
        return jsonify({'status': 'error', 'message': 'Animal not found'}), 404
    
    # Verify the animal belongs to the current user
    if animal['user_email'] != session.get('user_email'):
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    num_readings = request.args.get('count', 10, type=int)
    readings = generate_readings_history(animal['species'], num_readings)
    return jsonify({'status': 'success', 'readings': readings, 'animal': animal})

@app.route('/api/health/ranges/<species>', methods=['GET'])
def api_get_normal_ranges(species):
    """Get normal health ranges for a species"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    ranges = get_species_normal_ranges(species)
    return jsonify({'status': 'success', 'ranges': ranges})

# Health Readings Database API Routes
@app.route('/api/health-readings/<tag>', methods=['POST'])
def api_save_health_reading(tag):
    """Save a health reading to database"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    animal = get_animal_by_tag(tag)
    if not animal:
        return jsonify({'status': 'error', 'message': 'Animal not found'}), 404
    
    # Verify the animal belongs to the current user
    if animal['user_email'] != session.get('user_email'):
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO health_readings 
            (animal_tag, heart_rate, body_temp, blood_pressure, movement, health_index, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tag,
            data['heart_rate'],
            data['body_temp'],
            data['blood_pressure'],
            data['movement'],
            data['health_index'],
            data['status'],
            data['timestamp']
        ))
        
        conn.commit()
        reading_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Reading saved', 'id': reading_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/health-readings/<tag>', methods=['GET'])
def api_get_health_readings(tag):
    """Get stored health readings for an animal"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    animal = get_animal_by_tag(tag)
    if not animal:
        return jsonify({'status': 'error', 'message': 'Animal not found'}), 404
    
    # Verify the animal belongs to the current user
    if animal['user_email'] != session.get('user_email'):
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    try:
        limit = request.args.get('limit', 10, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM health_readings 
            WHERE animal_tag = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (tag, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        readings = []
        for row in rows:
            readings.append({
                'id': row['id'],
                'animal_tag': row['animal_tag'],
                'heart_rate': row['heart_rate'],
                'body_temp': row['body_temp'],
                'blood_pressure': row['blood_pressure'],
                'movement': row['movement'],
                'health_index': row['health_index'],
                'status': row['status'],
                'timestamp': row['timestamp']
            })
        
        return jsonify({'status': 'success', 'readings': readings, 'count': len(readings)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/health-readings/all', methods=['GET'])
def api_get_all_health_readings():
    """Get stored health readings for all user's animals"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        limit = request.args.get('limit', 10, type=int)
        user_email = session.get('user_email')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all active animal tags for the user
        cursor.execute('SELECT tag FROM animals WHERE user_email = ? AND (is_active = 1 OR is_active IS NULL)', (user_email,))
        animal_tags = [row['tag'] for row in cursor.fetchall()]
        
        if not animal_tags:
            conn.close()
            return jsonify({'status': 'success', 'readings': {}, 'count': 0})
        
        # Get readings for all animals
        placeholders = ','.join('?' * len(animal_tags))
        query = f'''
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY animal_tag ORDER BY timestamp DESC) as rn
                FROM health_readings 
                WHERE animal_tag IN ({placeholders})
            ) WHERE rn <= ?
            ORDER BY animal_tag, timestamp DESC
        '''
        
        cursor.execute(query, animal_tags + [limit])
        rows = cursor.fetchall()
        conn.close()
        
        # Group readings by animal tag
        readings_by_animal = {}
        for row in rows:
            tag = row['animal_tag']
            if tag not in readings_by_animal:
                readings_by_animal[tag] = []
            
            readings_by_animal[tag].append({
                'id': row['id'],
                'animal_tag': row['animal_tag'],
                'heart_rate': row['heart_rate'],
                'body_temp': row['body_temp'],
                'blood_pressure': row['blood_pressure'],
                'movement': row['movement'],
                'health_index': row['health_index'],
                'status': row['status'],
                'timestamp': row['timestamp']
            })
        
        return jsonify({'status': 'success', 'readings': readings_by_animal, 'count': len(rows)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/next-reading-time', methods=['GET'])
def api_get_next_reading_time():
    """Get when the next scheduled reading will occur"""
    last_reading = get_last_scheduled_reading_time()
    next_reading = get_next_scheduled_reading_time()
    
    seconds_until_next = 300  # Default 5 minutes if no data
    if last_reading:
        try:
            last_dt = datetime.strptime(last_reading, '%Y-%m-%d %H:%M:%S')
            next_dt = last_dt + timedelta(minutes=5)
            seconds_until_next = max(0, int((next_dt - datetime.now()).total_seconds()))
            
            # If timer already passed, return 0 and trigger a new reading soon
            if seconds_until_next <= 0:
                seconds_until_next = 0
        except Exception as e:
            print(f"Error parsing last reading time: {e}")
            seconds_until_next = 3600
    
    return jsonify({
        'status': 'success',
        'last_reading': last_reading,
        'next_reading': next_reading,
        'seconds_until_next': seconds_until_next
    })

@app.route('/api/trigger-reading', methods=['POST'])
def api_trigger_reading():
    """Manually trigger a reading (for testing or initial setup)"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        scheduled_health_reading_job()
        return jsonify({'status': 'success', 'message': 'Readings generated'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/trend-data/<tag>', methods=['GET'])
def api_get_trend_data(tag):
    """Get trend data for the health index graph
    
    period: '1day' for hourly data (24 hours), '7days' for daily averages
    """
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    animal = get_animal_by_tag(tag)
    if not animal:
        return jsonify({'status': 'error', 'message': 'Animal not found'}), 404
    
    # Verify the animal belongs to the current user
    if animal['user_email'] != session.get('user_email'):
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    try:
        period = request.args.get('period', '1day')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        now = datetime.now()
        
        if period == '1day':
            # Get hourly data for the last 24 hours
            start_time = now - timedelta(hours=24)
            
            cursor.execute('''
                SELECT 
                    strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                    AVG(health_index) as avg_health_index,
                    AVG(body_temp) as avg_temp,
                    AVG(heart_rate) as avg_heart_rate,
                    COUNT(*) as reading_count
                FROM health_readings 
                WHERE animal_tag = ? AND timestamp >= ?
                GROUP BY strftime('%Y-%m-%d %H', timestamp)
                ORDER BY hour ASC
            ''', (tag, start_time.strftime('%Y-%m-%d %H:%M:%S')))
            
            rows = cursor.fetchall()
            
            # Create 24-hour labels
            labels = []
            data_points = []
            
            for i in range(24):
                hour_time = now - timedelta(hours=23-i)
                hour_str = hour_time.strftime('%H:00')
                hour_key = hour_time.strftime('%Y-%m-%d %H:00:00')
                labels.append(hour_str)
                
                # Find matching data
                found = False
                for row in rows:
                    if row['hour'] == hour_key:
                        data_points.append({
                            'value': round(row['avg_health_index'], 1),
                            'temp': round(row['avg_temp'], 1) if row['avg_temp'] else None,
                            'heart_rate': round(row['avg_heart_rate'], 1) if row['avg_heart_rate'] else None,
                            'count': row['reading_count']
                        })
                        found = True
                        break
                
                if not found:
                    data_points.append({'value': None, 'temp': None, 'heart_rate': None, 'count': 0})
        
        else:  # 7days - daily averages
            start_time = now - timedelta(days=7)
            
            cursor.execute('''
                SELECT 
                    date(timestamp) as day,
                    AVG(health_index) as avg_health_index,
                    AVG(body_temp) as avg_temp,
                    AVG(heart_rate) as avg_heart_rate,
                    COUNT(*) as reading_count
                FROM health_readings 
                WHERE animal_tag = ? AND timestamp >= ?
                GROUP BY date(timestamp)
                ORDER BY day ASC
            ''', (tag, start_time.strftime('%Y-%m-%d %H:%M:%S')))
            
            rows = cursor.fetchall()
            
            # Create 7-day labels
            labels = []
            data_points = []
            day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            
            for i in range(7):
                day_time = now - timedelta(days=6-i)
                day_str = day_names[day_time.weekday()]
                day_key = day_time.strftime('%Y-%m-%d')
                labels.append(day_str)
                
                # Find matching data
                found = False
                for row in rows:
                    if row['day'] == day_key:
                        data_points.append({
                            'value': round(row['avg_health_index'], 1),
                            'temp': round(row['avg_temp'], 1) if row['avg_temp'] else None,
                            'heart_rate': round(row['avg_heart_rate'], 1) if row['avg_heart_rate'] else None,
                            'count': row['reading_count']
                        })
                        found = True
                        break
                
                if not found:
                    data_points.append({'value': None, 'temp': None, 'heart_rate': None, 'count': 0})
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'period': period,
            'labels': labels,
            'data': data_points,
            'animal_tag': tag
        })
        
    except Exception as e:
        print(f"Error getting trend data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Notifications API Routes
@app.route('/api/notifications', methods=['GET'])
def api_get_notifications():
    """Get all notifications for current user"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM notifications 
            WHERE user_email = ? 
            ORDER BY created_at DESC 
            LIMIT 50
        ''', (session.get('user_email'),))
        
        rows = cursor.fetchall()
        conn.close()
        
        notifications = []
        for row in rows:
            notifications.append({
                'id': row['id'],
                'animal_tag': row['animal_tag'],
                'title': row['title'],
                'message': row['message'],
                'notification_type': row['notification_type'],
                'is_read': row['is_read'],
                'created_at': row['created_at']
            })
        
        return jsonify({'status': 'success', 'notifications': notifications})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/notifications/unread', methods=['GET'])
def api_get_unread_notifications():
    """Get unread notifications for current user"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM notifications 
            WHERE user_email = ? AND is_read = 0
            ORDER BY created_at DESC
        ''', (session.get('user_email'),))
        
        rows = cursor.fetchall()
        conn.close()
        
        notifications = []
        for row in rows:
            notifications.append({
                'id': row['id'],
                'animal_tag': row['animal_tag'],
                'title': row['title'],
                'message': row['message'],
                'notification_type': row['notification_type'],
                'is_read': row['is_read'],
                'created_at': row['created_at']
            })
        
        return jsonify({'status': 'success', 'notifications': notifications, 'count': len(notifications)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/notifications', methods=['POST'])
def api_create_notification():
    """Create a new notification"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications 
            (user_email, animal_tag, title, message, notification_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session.get('user_email'),
            data.get('animal_tag'),
            data['title'],
            data['message'],
            data.get('notification_type', 'info')
        ))
        
        conn.commit()
        notification_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Notification created', 'id': notification_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def api_mark_notification_read(notification_id):
    """Mark a notification as read"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications 
            SET is_read = 1 
            WHERE id = ? AND user_email = ?
        ''', (notification_id, session.get('user_email')))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Notification marked as read'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/notifications/mark-all-read', methods=['POST'])
def api_mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications 
            SET is_read = 1 
            WHERE user_email = ?
        ''', (session.get('user_email'),))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'All notifications marked as read'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Vet Notifications API
@app.route('/api/vet/notifications', methods=['GET'])
def api_get_vet_notifications():
    """Get all notifications for vets"""
    if 'vet' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated as vet'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM vet_notifications 
            ORDER BY created_at DESC 
            LIMIT 50
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        notifications = []
        for row in rows:
            notifications.append({
                'id': row['id'],
                'animal_tag': row['animal_tag'],
                'owner_name': row['owner_name'],
                'owner_mobile': row['owner_mobile'],
                'title': row['title'],
                'message': row['message'],
                'notification_type': row['notification_type'],
                'is_read': row['is_read'],
                'created_at': row['created_at']
            })
        
        return jsonify({'status': 'success', 'notifications': notifications})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/vet/notifications/unread', methods=['GET'])
def api_get_vet_unread_notifications():
    """Get unread notifications count and list for vets"""
    if 'vet' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated as vet'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM vet_notifications 
            WHERE is_read = 0
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        notifications = []
        for row in rows:
            notifications.append({
                'id': row['id'],
                'animal_tag': row['animal_tag'],
                'owner_name': row['owner_name'],
                'owner_mobile': row['owner_mobile'],
                'title': row['title'],
                'message': row['message'],
                'notification_type': row['notification_type'],
                'is_read': row['is_read'],
                'created_at': row['created_at']
            })
        
        return jsonify({'status': 'success', 'notifications': notifications, 'count': len(notifications)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/vet/notifications/<int:notification_id>/read', methods=['POST'])
def api_mark_vet_notification_read(notification_id):
    """Mark a vet notification as read"""
    if 'vet' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated as vet'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE vet_notifications 
            SET is_read = 1 
            WHERE id = ?
        ''', (notification_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Notification marked as read'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/vet/notifications/mark-all-read', methods=['POST'])
def api_mark_all_vet_notifications_read():
    """Mark all vet notifications as read"""
    if 'vet' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated as vet'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE vet_notifications SET is_read = 1')
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'All notifications marked as read'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/appointments', methods=['POST'])
def api_book_appointment():
    """Book an appointment for an animal with a vet"""
    print("=" * 50)
    print("BOOKING APPOINTMENT - START")
    print("=" * 50)
    
    if 'user' not in session:
        print("ERROR: User not in session")
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    user_email = session.get('user_email')
    print(f"User email from session: {user_email}")
    
    conn = None
    try:
        data = request.get_json()
        animal_tag = data.get('animal_tag')
        health_status = data.get('health_status', 'Unknown')
        health_index = data.get('health_index', 0)
        
        print(f"Request data: animal_tag={animal_tag}, health_status={health_status}, health_index={health_index}")
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if appointment already exists
        cursor.execute('''
            SELECT id FROM appointment_queue 
            WHERE animal_tag = ? AND user_email = ? AND status = 'pending'
        ''', (animal_tag, user_email))
        
        existing = cursor.fetchone()
        if existing:
            print(f"ERROR: Appointment already exists with id={existing['id']}")
            conn.close()
            return jsonify({'status': 'error', 'message': 'An appointment is already pending for this animal'}), 400
        
        # Get animal info
        cursor.execute('SELECT * FROM animals WHERE tag = ? AND user_email = ?', (animal_tag, user_email))
        animal = cursor.fetchone()
        
        if not animal:
            print(f"ERROR: Animal not found for tag={animal_tag}, user={user_email}")
            conn.close()
            return jsonify({'status': 'error', 'message': 'Animal not found'}), 404
        
        print(f"Animal found: {animal['name']} ({animal['species']})")
        
        # Get user info
        cursor.execute('SELECT full_name, mobile FROM users WHERE email = ?', (user_email,))
        user = cursor.fetchone()
        
        owner_name = user['full_name'] if user else 'Unknown'
        owner_mobile = user['mobile'] if user else 'N/A'
        print(f"Owner: {owner_name}, Mobile: {owner_mobile}")
        
        # Determine priority
        priority_map = {'Ill': 3, 'Critical': 3, 'Warning': 2, 'Healthy': 1}
        priority = priority_map.get(health_status, 1)
        appointment_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # INSERT 1: Appointment
        print("Inserting appointment...")
        cursor.execute('''
            INSERT INTO appointment_queue 
            (animal_tag, user_email, owner_name, owner_mobile, health_status, health_index, priority, status, appointment_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        ''', (animal_tag, user_email, owner_name, owner_mobile, health_status, health_index, priority, appointment_time))
        appointment_id = cursor.lastrowid
        print(f"Appointment inserted with id={appointment_id}")
        
        # INSERT 2: User notification
        user_notification_title = f"Appointment Booked - {animal['species']} #{animal_tag}"
        user_notification_message = f"Your appointment for {animal['name']} ({animal['species']} #{animal_tag}) has been successfully booked. Current health status: {health_status}. A veterinarian will review your request soon."
        
        print("Inserting user notification...")
        cursor.execute('''
            INSERT INTO notifications (user_email, animal_tag, title, message, notification_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_email, animal_tag, user_notification_title, user_notification_message, 'appointment'))
        print(f"User notification inserted")
        
        # INSERT 3: Vet notification
        vet_notification_title = f"New Appointment Request - {animal['species']} #{animal_tag}"
        vet_notification_message = f"New appointment request from {owner_name} ({owner_mobile}) for {animal['name']} ({animal['species']} #{animal_tag}). Health Status: {health_status}, Health Index: {health_index}%. Please review in the Patient Queue."
        notification_type = 'critical' if health_status in ['Ill', 'Critical'] else 'warning' if health_status == 'Warning' else 'info'
        
        print("Inserting vet notification...")
        cursor.execute('''
            INSERT INTO vet_notifications (animal_tag, owner_name, owner_mobile, title, message, notification_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (animal_tag, owner_name, owner_mobile, vet_notification_title, vet_notification_message, notification_type))
        print(f"Vet notification inserted")
        
        # COMMIT all changes
        print("Committing transaction...")
        conn.commit()
        print("Transaction committed successfully!")
        conn.close()
        
        print("=" * 50)
        print("BOOKING APPOINTMENT - SUCCESS")
        print("=" * 50)
        
        return jsonify({
            'status': 'success', 
            'message': 'Appointment booked successfully',
            'appointment_id': appointment_id,
            'notification': {
                'title': user_notification_title,
                'message': user_notification_message
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Exception: {error_msg}")
        if conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        
        # Check if it's a unique constraint violation (duplicate appointment)
        if 'UNIQUE constraint failed' in error_msg or 'unique constraint' in error_msg.lower():
            return jsonify({'status': 'error', 'message': 'An appointment is already pending for this animal'}), 400
        
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': error_msg}), 500

@app.route('/api/appointments', methods=['GET'])
def api_get_appointments():
    """Get all pending appointments (vet dashboard)"""
    if 'vet' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated as vet'}), 401
    
    try:
        sort_by = request.args.get('sort_by', 'priority')  # 'priority' or 'health_index'
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if sort_by == 'health_index':
            # Sort by health index ascending (most critical first)
            cursor.execute('''
                SELECT a.*, an.name, an.species 
                FROM appointment_queue a
                LEFT JOIN animals an ON a.animal_tag = an.tag AND a.user_email = an.user_email
                WHERE a.status = 'pending'
                ORDER BY a.health_index ASC, a.appointment_time ASC
            ''')
        else:
            # Default: sort by priority (critical first) then by time
            cursor.execute('''
                SELECT a.*, an.name, an.species 
                FROM appointment_queue a
                LEFT JOIN animals an ON a.animal_tag = an.tag AND a.user_email = an.user_email
                WHERE a.status = 'pending'
                ORDER BY a.priority DESC, a.appointment_time ASC
            ''')
        
        appointments = cursor.fetchall()
        conn.close()
        
        appointments_list = [{
            'id': row['id'],
            'animal_tag': row['animal_tag'],
            'animal_name': row['name'],
            'animal_species': row['species'],
            'owner_name': row['owner_name'],
            'owner_mobile': row['owner_mobile'],
            'health_status': row['health_status'],
            'health_index': row['health_index'],
            'appointment_time': row['appointment_time'],
            'priority': row['priority']
        } for row in appointments]
        
        return jsonify({'status': 'success', 'appointments': appointments_list})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/appointments/check/<animal_tag>', methods=['GET'])
def api_check_appointment(animal_tag):
    """Check if an animal already has a pending appointment"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, appointment_time, health_status, health_index 
            FROM appointment_queue 
            WHERE animal_tag = ? AND user_email = ? AND status = 'pending'
            ORDER BY appointment_time DESC
            LIMIT 1
        ''', (animal_tag, session.get('user_email')))
        
        appointment = cursor.fetchone()
        conn.close()
        
        if appointment:
            return jsonify({
                'status': 'success',
                'has_appointment': True,
                'appointment': {
                    'id': appointment['id'],
                    'appointment_time': appointment['appointment_time'],
                    'health_status': appointment['health_status'],
                    'health_index': appointment['health_index']
                }
            })
        else:
            return jsonify({
                'status': 'success',
                'has_appointment': False
            })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/appointments/<int:appointment_id>/confirm', methods=['POST'])
def api_confirm_appointment(appointment_id):
    """Confirm an appointment - move it to confirmed appointments for visit"""
    if 'vet' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated as vet'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get appointment details first
        cursor.execute('''
            SELECT aq.*, a.name as animal_name, a.species 
            FROM appointment_queue aq
            LEFT JOIN animals a ON aq.animal_tag = a.tag
            WHERE aq.id = ?
        ''', (appointment_id,))
        appointment = cursor.fetchone()
        
        if not appointment:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Appointment not found'}), 404
        
        # Move to confirmed_appointments table
        cursor.execute('''
            INSERT INTO confirmed_appointments 
            (animal_tag, animal_name, species, user_email, owner_name, owner_mobile, 
             health_status, health_index, appointment_id, vet_email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            appointment['animal_tag'],
            appointment['animal_name'],
            appointment['species'],
            appointment['user_email'],
            appointment['owner_name'],
            appointment['owner_mobile'],
            appointment['health_status'],
            appointment['health_index'],
            appointment_id,
            session.get('vet_email')
        ))
        
        # Add notification to user about appointment confirmation
        cursor.execute('''
            INSERT INTO notifications (user_email, animal_tag, title, message, notification_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            appointment['user_email'],
            appointment['animal_tag'],
            f"Appointment Confirmed - {appointment['animal_name']}",
            f"Your animal {appointment['animal_name']} (#{appointment['animal_tag']}) appointment has been confirmed by the vet. Please bring your animal for treatment.",
            'info'
        ))
        
        # Mark appointment as confirmed (not treated yet)
        cursor.execute('''
            UPDATE appointment_queue 
            SET status = 'confirmed'
            WHERE id = ?
        ''', (appointment_id,))
        
        # Don't deactivate animal yet - just confirmed for visit
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Appointment confirmed and moved to visit queue'})
    except Exception as e:
        print(f"Error in confirm appointment: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500

@app.route('/api/vet/stats', methods=['GET'])
def api_get_vet_stats():
    """Get vet dashboard stats"""
    if 'vet' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated as vet'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Critical alerts (Ill/Critical status animals with pending appointments)
        cursor.execute('''SELECT COUNT(*) as count FROM appointment_queue 
                         WHERE status = 'pending' AND (health_status = 'Ill' OR health_status = 'Critical')''')
        critical_alerts = cursor.fetchone()['count']
        
        # Under observation (Warning status)
        cursor.execute('''SELECT COUNT(*) as count FROM appointment_queue 
                         WHERE status = 'pending' AND health_status = 'Warning' ''')
        under_observation = cursor.fetchone()['count']
        
        # Active notifications (all pending appointments)
        cursor.execute('''SELECT COUNT(*) as count FROM appointment_queue WHERE status = 'pending' ''')
        active_notifications = cursor.fetchone()['count']
        
        # Total animals treated
        cursor.execute('''SELECT COUNT(*) as count FROM appointment_queue WHERE status = 'treated' ''')
        total_treated = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'critical_alerts': critical_alerts,
                'under_observation': under_observation,
                'active_notifications': active_notifications,
                'total_treated': total_treated
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/vet/treatment-history', methods=['GET'])
def api_get_vet_treatment_history():
    """Get treatment history for vet history page"""
    if 'vet' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated as vet'}), 401
    
    vet_email = session.get('vet_email')
    print(f"[DEBUG] Getting treatment history for vet: {vet_email}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get treatment history records only for the logged-in vet
        cursor.execute('''
            SELECT * FROM treatment_history 
            WHERE vet_email = ?
            ORDER BY treated_date DESC
        ''', (vet_email,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'id': row['id'],
                'animal_tag': row['animal_tag'],
                'animal_name': row['animal_name'],
                'species': row['species'],
                'user_email': row['user_email'],
                'owner_name': row['owner_name'],
                'owner_mobile': row['owner_mobile'],
                'health_status': row['health_status'],
                'health_index': row['health_index'],
                'treatment': row['treatment'],
                'notes': row['notes'],
                'treated_date': row['treated_date']
            })
        
        return jsonify({'status': 'success', 'history': history})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/user/treatment-history', methods=['GET'])
def api_get_user_treatment_history():
    """Get treatment history for user's animals"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get treatment history for this user's animals
        cursor.execute('''
            SELECT * FROM treatment_history 
            WHERE user_email = ?
            ORDER BY treated_date DESC
        ''', (session.get('user_email'),))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            # Get vet_name column safely
            vet_name = None
            try:
                vet_name = row['vet_name']
            except:
                pass
            
            history.append({
                'id': row['id'],
                'animal_tag': row['animal_tag'],
                'animal_name': row['animal_name'],
                'species': row['species'],
                'health_status': row['health_status'],
                'health_index': row['health_index'],
                'treatment': row['treatment'],
                'notes': row['notes'],
                'treated_date': row['treated_date'],
                'vet_name': vet_name
            })
        
        return jsonify({'status': 'success', 'history': history})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/vet/confirmed-appointments', methods=['GET'])
def api_get_confirmed_appointments():
    """Get confirmed appointments (animals to visit)"""
    if 'vet' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated as vet'}), 401
    
    vet_email = session.get('vet_email')
    print(f"[DEBUG] Getting confirmed appointments for vet: {vet_email}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get confirmed appointments only for the logged-in vet
        cursor.execute('''
            SELECT * FROM confirmed_appointments 
            WHERE vet_email = ?
            ORDER BY confirmed_date DESC
        ''', (vet_email,))
        
        rows = cursor.fetchall()
        conn.close()
        
        confirmed = []
        for row in rows:
            confirmed.append({
                'id': row['id'],
                'animal_tag': row['animal_tag'],
                'animal_name': row['animal_name'],
                'species': row['species'],
                'user_email': row['user_email'],
                'owner_name': row['owner_name'],
                'owner_mobile': row['owner_mobile'],
                'health_status': row['health_status'],
                'health_index': row['health_index'],
                'confirmed_date': row['confirmed_date'],
                'notes': row['notes']
            })
        
        return jsonify({'status': 'success', 'confirmed': confirmed})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/vet/confirmed-appointments/<int:confirmed_id>/mark-treated', methods=['POST'])
def api_mark_confirmed_treated(confirmed_id):
    """Mark a confirmed appointment as treated"""
    if 'vet' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated as vet'}), 401
    
    try:
        # Get treatment data from request
        data = request.get_json() or {}
        treatment = data.get('treatment', 'General Treatment')
        notes = data.get('notes', '')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get confirmed appointment details and verify vet owns it
        cursor.execute('''
            SELECT * FROM confirmed_appointments WHERE id = ? AND vet_email = ?
        ''', (confirmed_id, session.get('vet_email')))
        confirmed = cursor.fetchone()
        
        if not confirmed:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Confirmed appointment not found or you do not have access to it'}), 404
        
        # Save to treatment_history
        cursor.execute('''
            INSERT INTO treatment_history 
            (animal_tag, animal_name, species, user_email, owner_name, owner_mobile, 
             health_status, health_index, treatment, notes, vet_email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            confirmed['animal_tag'],
            confirmed['animal_name'],
            confirmed['species'],
            confirmed['user_email'],
            confirmed['owner_name'],
            confirmed['owner_mobile'],
            confirmed['health_status'],
            confirmed['health_index'],
            treatment,
            notes,
            session.get('vet_email')
        ))
        
        # Add notification to user about treatment
        cursor.execute('''
            INSERT INTO notifications (user_email, animal_tag, title, message, notification_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            confirmed['user_email'],
            confirmed['animal_tag'],
            f"Treatment Completed - {confirmed['animal_name']}",
            f"Your animal {confirmed['animal_name']} (#{confirmed['animal_tag']}) has been treated by the vet. Treatment: {treatment}. {'Notes: ' + notes if notes else ''}",
            'info'
        ))
        
        # Remove any critical/warning notifications for this animal from user
        cursor.execute('''
            DELETE FROM notifications 
            WHERE user_email = ? AND animal_tag = ? AND notification_type IN ('critical', 'warning')
        ''', (confirmed['user_email'], confirmed['animal_tag']))
        
        # Get the last health reading for history record
        cursor.execute('''
            SELECT body_temp, heart_rate, status, health_index 
            FROM health_readings 
            WHERE animal_tag = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''', (confirmed['animal_tag'],))
        last_reading = cursor.fetchone()
        
        # Save to removed_animals_history
        cursor.execute('''
            INSERT INTO removed_animals_history 
            (animal_tag, animal_name, species, user_email, last_temp, last_heart_rate, last_health_status, last_health_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            confirmed['animal_tag'],
            confirmed['animal_name'],
            confirmed['species'],
            confirmed['user_email'],
            last_reading['body_temp'] if last_reading else None,
            last_reading['heart_rate'] if last_reading else None,
            last_reading['status'] if last_reading else confirmed['health_status'],
            last_reading['health_index'] if last_reading else confirmed['health_index']
        ))
        
        # Deactivate the animal
        cursor.execute('''
            UPDATE animals 
            SET is_active = 0
            WHERE tag = ?
        ''', (confirmed['animal_tag'],))
        
        # Remove from confirmed_appointments
        cursor.execute('''
            DELETE FROM confirmed_appointments WHERE id = ?
        ''', (confirmed_id,))
        
        # Update the original appointment status to 'treated'
        if confirmed['appointment_id']:
            cursor.execute('''
                UPDATE appointment_queue 
                SET status = 'treated', notes = ?
                WHERE id = ?
            ''', (treatment, confirmed['appointment_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Treatment saved and animal marked as treated'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/check-consecutive-readings/<tag>', methods=['GET'])
def api_check_consecutive_readings(tag):
    """Check if last 3 readings have the same status for an animal"""
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get last 3 readings for this animal
        cursor.execute('''
            SELECT status, health_index, body_temp, heart_rate FROM health_readings 
            WHERE animal_tag = ? 
            ORDER BY timestamp DESC 
            LIMIT 3
        ''', (tag,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if len(rows) < 3:
            return jsonify({'status': 'success', 'has_consecutive': False, 'reason': 'Not enough readings'})
        
        # Check if all 3 have the same status
        statuses = [row['status'] for row in rows]
        
        if statuses[0] == statuses[1] == statuses[2]:
            # All 3 readings have same status - check if it's concerning
            common_status = statuses[0]
            avg_health_index = sum(row['health_index'] for row in rows) / 3
            avg_temp = sum(row['body_temp'] for row in rows) / 3
            avg_hr = sum(row['heart_rate'] for row in rows) / 3
            
            return jsonify({
                'status': 'success',
                'has_consecutive': True,
                'consecutive_status': common_status,
                'avg_health_index': round(avg_health_index, 1),
                'avg_temp': round(avg_temp, 1),
                'avg_heart_rate': round(avg_hr)
            })
        
        return jsonify({'status': 'success', 'has_consecutive': False})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Logout Routes
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

@app.route('/vet-logout')
def vet_logout():
    session.pop('vet', None)
    flash("Logged out successfully", "success")
    return redirect(url_for('vetlogin'))

def cleanup_orphan_readings():
    """Remove health readings for animals that no longer exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Delete readings for animals that don't exist in animals table
        cursor.execute('''
            DELETE FROM health_readings 
            WHERE animal_tag NOT IN (SELECT tag FROM animals WHERE is_active = 1)
        ''')
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            print(f"Cleaned up {deleted} orphan health readings")
    except Exception as e:
        print(f"Error cleaning up orphan readings: {e}")

if __name__ == '__main__':
    init_db()
    init_animals_table()
    
    # Clean up any orphan readings from deleted animals
    cleanup_orphan_readings()
    
    # Load previous readings from database for gradual health changes
    load_previous_readings_from_db()
    
    # Load Keras model in background thread for faster first prediction
    print(f"[{datetime.now()}] Starting background model loading...")
    model_thread = threading.Thread(target=load_keras_model, daemon=True)
    model_thread.start()
    
    # Start the background scheduler for automatic readings every 5 minutes
    start_scheduler()
    
    # Run initial reading if no readings exist yet
    last_reading = get_last_scheduled_reading_time()
    if not last_reading:
        print("No previous readings found - generating initial readings...")
        scheduled_health_reading_job()
    
    app.run(debug=True, use_reloader=False)  # use_reloader=False to prevent scheduler running twice
