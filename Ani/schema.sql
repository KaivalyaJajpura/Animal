-- Users table for farmer registration
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    mobile TEXT NOT NULL,
    password TEXT NOT NULL,
    age INTEGER,
    gender TEXT
);

-- Animals table for livestock
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
);

-- Insert sample animals
INSERT OR IGNORE INTO animals (tag, name, species, weight, age, gender, user_email)
VALUES ('C-001', 'Daisy', 'Cow', 680, 5, 'Female', 'demo@example.com');

INSERT OR IGNORE INTO animals (tag, name, species, weight, age, gender, user_email)
VALUES ('C-002', 'Luna', 'Cow', 450, 3, 'Female', 'demo@example.com');

INSERT OR IGNORE INTO animals (tag, name, species, weight, age, gender, user_email)
VALUES ('G-001', 'Billy', 'Goat', 85, 2, 'Male', 'demo@example.com');

INSERT OR IGNORE INTO animals (tag, name, species, weight, age, gender, user_email)
VALUES ('S-001', 'Woolly', 'Sheep', 65, 3, 'Male', 'demo@example.com');

-- Health Readings table for storing all health metrics
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
);

-- Notifications table for user alerts
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
);

-- Vets table with full profile
CREATE TABLE IF NOT EXISTS vets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    license_id TEXT NOT NULL UNIQUE,
    region TEXT NOT NULL,
    mobile TEXT
);

-- Appointment Queue table for vet appointments
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
);

-- Vet Notifications table for vet alerts
CREATE TABLE IF NOT EXISTS vet_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_tag TEXT,
    owner_name TEXT,
    owner_mobile TEXT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT DEFAULT 'info',
    is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_tag) REFERENCES animals(tag)
);

-- Admin table for system administrators
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    full_name TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Insert predefined vet login with full details
INSERT OR IGNORE INTO vets (full_name, email, password, license_id, region)
VALUES ('Dr. Aman Kumar', 'aman@gmail.com', '12345', 'VET-1001', 'North District - Sector 1');

INSERT OR IGNORE INTO vets (full_name, email, password, license_id, region)
VALUES ('Dr. Aditi Sharma', 'aditi@gmail.com', '12345', 'VET-1002', 'South District - Sector 2');

INSERT OR IGNORE INTO vets (full_name, email, password, license_id, region)
VALUES ('Dr. Rajesh Singh', 'rajesh@gmail.com', '12345', 'VET-1003', 'East District - Sector 3');

-- Insert admin account
INSERT OR IGNORE INTO admin (username, password, full_name)
VALUES ('Nikhil_jaroli', '8288', 'Admin');
