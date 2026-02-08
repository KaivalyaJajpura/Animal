"""
Generate new health readings with specific distribution:
- 60% Healthy
- 30% Warning
- 10% Critical

Old readings are kept intact; this adds new readings for all active animals.
"""

import sqlite3
import random
import numpy as np
from datetime import datetime

# Species-specific health parameters (same as simulate.py)
SPECIES_PARAMS = {
    'Horse': {
        'heart_rate': {'min': 28, 'max': 44, 'normal': 36},
        'body_temp': {'min': 37.2, 'max': 38.3, 'normal': 37.75},
        'blood_pressure': {'min': 100, 'max': 140, 'normal': 120},
    },
    'Cow': {
        'heart_rate': {'min': 48, 'max': 84, 'normal': 66},
        'body_temp': {'min': 38.0, 'max': 39.3, 'normal': 38.65},
        'blood_pressure': {'min': 110, 'max': 150, 'normal': 130},
    },
    'Buffalo': {
        'heart_rate': {'min': 48, 'max': 84, 'normal': 66},
        'body_temp': {'min': 38.0, 'max': 39.3, 'normal': 38.65},
        'blood_pressure': {'min': 110, 'max': 150, 'normal': 130},
    },
    'Goat': {
        'heart_rate': {'min': 70, 'max': 90, 'normal': 80},
        'body_temp': {'min': 38.5, 'max': 40.0, 'normal': 39.25},
        'blood_pressure': {'min': 90, 'max': 130, 'normal': 110},
    },
    'Sheep': {
        'heart_rate': {'min': 70, 'max': 80, 'normal': 75},
        'body_temp': {'min': 38.3, 'max': 39.9, 'normal': 39.1},
        'blood_pressure': {'min': 90, 'max': 130, 'normal': 110},
    },
    'Dog': {
        'heart_rate': {'min': 60, 'max': 120, 'normal': 90},
        'body_temp': {'min': 38.3, 'max': 39.2, 'normal': 38.6},
        'blood_pressure': {'min': 110, 'max': 130, 'normal': 120},
    },
    'Cat': {
        'heart_rate': {'min': 120, 'max': 180, 'normal': 150},
        'body_temp': {'min': 38.1, 'max': 39.2, 'normal': 38.9},
        'blood_pressure': {'min': 110, 'max': 130, 'normal': 120},
    }
}

DEFAULT_PARAMS = {
    'heart_rate': {'min': 60, 'max': 100, 'normal': 80},
    'body_temp': {'min': 38.0, 'max': 39.5, 'normal': 38.75},
    'blood_pressure': {'min': 100, 'max': 140, 'normal': 120},
}

MOVEMENT_SCORES = {
    'Active': 100,
    'Normal': 90,
    'Inactive': 60,
    'Lying Down': 40,
    'Low': 50
}

WEIGHTS = {
    'heart_rate': 0.30,
    'body_temp': 0.30,
    'blood_pressure': 0.20,
    'movement': 0.20
}


def get_species_params(species):
    return SPECIES_PARAMS.get(species, DEFAULT_PARAMS)


def calculate_health_index(heart_rate, body_temp, blood_pressure, movement, species):
    params = get_species_params(species)
    
    # Heart rate score
    hr_normal = params['heart_rate']['normal']
    hr_deviation = abs(heart_rate - hr_normal)
    hr_score = max(0, 100 - hr_deviation * 2)
    
    # Temperature score
    temp_normal = params['body_temp']['normal']
    temp_deviation = abs(body_temp - temp_normal)
    temp_score = max(0, 100 - temp_deviation * 25)
    
    # Blood pressure score
    bp_normal = params['blood_pressure']['normal']
    bp_deviation = abs(blood_pressure - bp_normal)
    bp_score = max(0, 100 - bp_deviation * 1.5)
    
    # Movement score
    move_score = MOVEMENT_SCORES.get(movement, 70)
    
    health_index = (
        WEIGHTS['heart_rate'] * hr_score +
        WEIGHTS['body_temp'] * temp_score +
        WEIGHTS['blood_pressure'] * bp_score +
        WEIGHTS['movement'] * move_score
    )
    
    return round(health_index, 1)


def classify_health_status(health_index):
    """
    80-100: Healthy
    50-79: Warning
    <50: Critical (Ill)
    """
    if health_index >= 80:
        return 'Healthy'
    elif health_index >= 50:
        return 'Warning'
    else:
        return 'Critical'


def generate_reading_for_status_with_constraint(species, last_health_index=None):
    """
    Generate a reading with constraints:
    - If last_health_index exists: change must be <= 10% (max difference)
    - Prevents direct jumps from Healthy (80+) to Critical (<50)
    - Ensures realistic gradual health changes
    """
    params = get_species_params(species)
    
    # Determine the target health range based on last reading
    if last_health_index is None:
        # No previous reading - generate any valid reading
        target_min, target_max = 0, 100
    else:
        # Apply constraint: max 10% difference
        target_min = max(0, last_health_index - 10)
        target_max = min(100, last_health_index + 10)
    
    # Try to generate a reading within constraints
    for attempt in range(30):
        # Randomly choose health state weighted towards current state
        if last_health_index is None:
            # No history - random distribution
            rand = random.random()
            if rand < 0.60:
                health_state = 'Healthy'
            elif rand < 0.90:
                health_state = 'Warning'
            else:
                health_state = 'Critical'
        else:
            # Biased towards staying in same category with small changes
            current_status = classify_health_status(last_health_index)
            rand = random.random()
            
            if current_status == 'Healthy':
                # Stay healthy or move to warning
                health_state = 'Healthy' if rand < 0.8 else 'Warning'
            elif current_status == 'Warning':
                # Can go healthy, stay warning, or go critical
                if rand < 0.4:
                    health_state = 'Healthy'
                elif rand < 0.8:
                    health_state = 'Warning'
                else:
                    health_state = 'Critical'
            else:  # Critical
                # Stay critical or move to warning
                health_state = 'Critical' if rand < 0.7 else 'Warning'
        
        # Generate reading based on state
        if health_state == 'Healthy':
            heart_rate = np.random.uniform(params['heart_rate']['min'], params['heart_rate']['max'])
            body_temp = np.random.uniform(params['body_temp']['min'], params['body_temp']['max'])
            bp_systolic = np.random.uniform(params['blood_pressure']['min'], params['blood_pressure']['max'])
            movement = random.choice(['Active', 'Normal'])
        elif health_state == 'Warning':
            heart_rate = params['heart_rate']['normal'] + np.random.uniform(-15, 15)
            body_temp = params['body_temp']['normal'] + np.random.uniform(-0.8, 0.8)
            bp_systolic = params['blood_pressure']['normal'] + np.random.uniform(-25, 25)
            movement = random.choice(['Normal', 'Inactive', 'Low'])
        else:  # Critical
            heart_rate = params['heart_rate']['normal'] + np.random.choice([-1, 1]) * np.random.uniform(25, 40)
            body_temp = params['body_temp']['normal'] + np.random.choice([-1, 1]) * np.random.uniform(1.5, 2.5)
            bp_systolic = params['blood_pressure']['normal'] + np.random.choice([-1, 1]) * np.random.uniform(35, 50)
            movement = random.choice(['Inactive', 'Lying Down', 'Low'])
        
        # Clamp values
        heart_rate = max(20, min(200, heart_rate))
        body_temp = max(35.0, min(43.0, body_temp))
        bp_systolic = max(60, min(200, bp_systolic))
        
        reading = {
            'heart_rate': round(heart_rate, 1),
            'body_temp': round(body_temp, 1),
            'blood_pressure': int(bp_systolic),
            'movement': movement
        }
        
        health_index = calculate_health_index(
            reading['heart_rate'],
            reading['body_temp'],
            reading['blood_pressure'],
            reading['movement'],
            species
        )
        
        # Check if within constraint
        if last_health_index is None:
            # No constraint on first reading
            return reading, health_index, classify_health_status(health_index)
        elif target_min <= health_index <= target_max:
            # Within constraint
            return reading, health_index, classify_health_status(health_index)
    
    # Fallback - if we couldn't find a reading within range, use the closest value
    if last_health_index is not None:
        # Clamp to target range
        clamped_index = max(target_min, min(target_max, health_index))
        if health_index != clamped_index:
            # We had to clamp, regenerate until we get closer
            for attempt in range(10):
                health_state = 'Healthy' if clamped_index >= 80 else ('Warning' if clamped_index >= 50 else 'Critical')
                
                if health_state == 'Healthy':
                    heart_rate = np.random.uniform(params['heart_rate']['min'], params['heart_rate']['max'])
                    body_temp = np.random.uniform(params['body_temp']['min'], params['body_temp']['max'])
                    bp_systolic = np.random.uniform(params['blood_pressure']['min'], params['blood_pressure']['max'])
                    movement = random.choice(['Active', 'Normal'])
                elif health_state == 'Warning':
                    heart_rate = params['heart_rate']['normal'] + np.random.uniform(-10, 10)
                    body_temp = params['body_temp']['normal'] + np.random.uniform(-0.5, 0.5)
                    bp_systolic = params['blood_pressure']['normal'] + np.random.uniform(-15, 15)
                    movement = random.choice(['Normal', 'Inactive'])
                else:
                    heart_rate = params['heart_rate']['normal'] + np.random.uniform(-15, 15)
                    body_temp = params['body_temp']['normal'] + np.random.uniform(-1, 1)
                    bp_systolic = params['blood_pressure']['normal'] + np.random.uniform(-25, 25)
                    movement = random.choice(['Inactive', 'Low'])
                
                heart_rate = max(20, min(200, heart_rate))
                body_temp = max(35.0, min(43.0, body_temp))
                bp_systolic = max(60, min(200, bp_systolic))
                
                reading = {
                    'heart_rate': round(heart_rate, 1),
                    'body_temp': round(body_temp, 1),
                    'blood_pressure': int(bp_systolic),
                    'movement': movement
                }
                
                health_index = calculate_health_index(
                    reading['heart_rate'],
                    reading['body_temp'],
                    reading['blood_pressure'],
                    reading['movement'],
                    species
                )
                
                if target_min <= health_index <= target_max:
                    return reading, health_index, classify_health_status(health_index)
    
    # Last resort: return what we have (should be very rare)
    return reading, health_index, classify_health_status(health_index)


def generate_readings_with_distribution():
    """
    Generate new readings for all active animals with distribution:
    60% Healthy, 30% Warning, 10% Critical
    
    Constraints:
    - Health index change from previous reading must be < 8
    - Cannot jump directly from Healthy (≥80) to Critical (<50)
    """
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all active animals
    cursor.execute('SELECT tag, species FROM animals WHERE is_active = 1 OR is_active IS NULL')
    animals = cursor.fetchall()
    
    if not animals:
        print("No active animals found!")
        conn.close()
        return
    
    print(f"Found {len(animals)} active animals")
    
    # Get last reading for each animal
    last_readings = {}
    cursor.execute('''
        SELECT animal_tag, health_index, status
        FROM health_readings
        WHERE (animal_tag, timestamp) IN (
            SELECT animal_tag, MAX(timestamp)
            FROM health_readings
            GROUP BY animal_tag
        )
    ''')
    for row in cursor.fetchall():
        last_readings[row['animal_tag']] = {
            'health_index': row['health_index'],
            'status': row['status']
        }
    
    print(f"\nGenerating new readings with constraints:")
    print(f"  - Health index change MAX 10% from previous reading")
    print(f"  - Gradual transitions through Warning state when changing statuses")
    print("-" * 60)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    results = {'Healthy': [], 'Warning': [], 'Critical': []}
    
    for i, animal in enumerate(animals):
        tag = animal['tag']
        species = animal['species']
        
        # Get last reading info
        last_reading_info = last_readings.get(tag)
        last_health_index = last_reading_info['health_index'] if last_reading_info else None
        
        # Generate reading with constraints
        reading, health_index, actual_status = generate_reading_for_status_with_constraint(
            species, last_health_index
        )
        
        # Validate the constraint was respected
        if last_health_index is not None:
            health_change = abs(health_index - last_health_index)
            if health_change > 10.01:  # Allow tiny floating point tolerance
                # Clamp to constraint if violated
                if health_index > last_health_index:
                    health_index = min(health_index, last_health_index + 10)
                else:
                    health_index = max(health_index, last_health_index - 10)
                actual_status = classify_health_status(health_index)
        
        # Insert reading into database
        cursor.execute('''
            INSERT INTO health_readings (animal_tag, heart_rate, body_temp, blood_pressure, movement, health_index, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tag,
            reading['heart_rate'],
            reading['body_temp'],
            reading['blood_pressure'],
            reading['movement'],
            health_index,
            actual_status,
            timestamp
        ))
        
        results[actual_status].append(tag)
        change_info = ""
        if last_health_index is not None:
            change = health_index - last_health_index
            change_info = f" (prev: {last_health_index}%, change: {change:+.1f}%)"
        print(f"  {tag} ({species}): {actual_status} (Health Index: {health_index}%){change_info}")
    
    conn.commit()
    conn.close()
    
    print("-" * 60)
    print(f"\n✓ Generated {len(animals)} new readings!")
    print(f"   Healthy:  {len(results['Healthy'])} animals")
    print(f"   Warning:  {len(results['Warning'])} animals")
    print(f"   Critical: {len(results['Critical'])} animals")


if __name__ == '__main__':
    print("=" * 60)
    print("Generating new health readings with distribution:")
    print("  60% Healthy | 30% Warning | 10% Critical")
    print("=" * 60)
    generate_readings_with_distribution()
