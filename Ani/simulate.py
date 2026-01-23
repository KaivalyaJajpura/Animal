import numpy as np
from sklearn.cluster import KMeans
from datetime import datetime, timedelta
import random

# Species-specific health parameters
SPECIES_PARAMS = {
    'Horse': {
        'heart_rate': {'min': 28, 'max': 44, 'normal': 36, 'multiplier': 3},
        'body_temp': {'min': 37.2, 'max': 38.3, 'normal': 37.75, 'multiplier': 25},
        'blood_pressure': {'min': 100, 'max': 140, 'normal': 120, 'multiplier': 18},
        'movement_expected': 'Active'
    },
    'Cow': {
        'heart_rate': {'min': 48, 'max': 84, 'normal': 66, 'multiplier': 2},
        'body_temp': {'min': 38.0, 'max': 39.3, 'normal': 38.65, 'multiplier': 20},
        'blood_pressure': {'min': 110, 'max': 150, 'normal': 130, 'multiplier': 15},
        'movement_expected': 'Normal'
    },
    'Buffalo': {
        'heart_rate': {'min': 48, 'max': 84, 'normal': 66, 'multiplier': 2},
        'body_temp': {'min': 38.0, 'max': 39.3, 'normal': 38.65, 'multiplier': 20},
        'blood_pressure': {'min': 110, 'max': 150, 'normal': 130, 'multiplier': 15},
        'movement_expected': 'Normal'
    },
    'Goat': {
        'heart_rate': {'min': 70, 'max': 90, 'normal': 80, 'multiplier': 2.5},
        'body_temp': {'min': 38.5, 'max': 40.0, 'normal': 39.25, 'multiplier': 22},
        'blood_pressure': {'min': 90, 'max': 130, 'normal': 110, 'multiplier': 15},
        'movement_expected': 'Active'
    },
    'Sheep': {
        'heart_rate': {'min': 70, 'max': 80, 'normal': 75, 'multiplier': 2},
        'body_temp': {'min': 38.3, 'max': 39.9, 'normal': 39.1, 'multiplier': 18},
        'blood_pressure': {'min': 90, 'max': 130, 'normal': 110, 'multiplier': 15},
        'movement_expected': 'Normal'
    }
}

# Default params for unknown species
DEFAULT_PARAMS = {
    'heart_rate': {'min': 60, 'max': 100, 'normal': 80, 'multiplier': 2},
    'body_temp': {'min': 38.0, 'max': 39.5, 'normal': 38.75, 'multiplier': 20},
    'blood_pressure': {'min': 100, 'max': 140, 'normal': 120, 'multiplier': 15},
    'movement_expected': 'Normal'
}

# Movement scores
MOVEMENT_SCORES = {
    'Active': 100,
    'Normal': 90,
    'Inactive': 60,
    'Lying Down': 40,
    'Low': 50
}

# Health weights
WEIGHTS = {
    'heart_rate': 0.30,
    'body_temp': 0.30,
    'blood_pressure': 0.20,
    'movement': 0.20
}


def get_species_params(species):
    """Get species-specific parameters"""
    return SPECIES_PARAMS.get(species, DEFAULT_PARAMS)


def generate_health_data_with_clustering(species, num_samples=100):
    """
    Use KMeans clustering to generate realistic health data clusters
    Creates 3 clusters: Healthy, Warning, Ill
    """
    params = get_species_params(species)
    
    # Generate base data points for clustering
    np.random.seed(random.randint(1, 1000))
    
    # Create data for 3 health states
    # Cluster 0: Healthy (within normal range)
    healthy_data = np.array([
        [
            np.random.uniform(params['heart_rate']['min'], params['heart_rate']['max']),
            np.random.uniform(params['body_temp']['min'], params['body_temp']['max']),
            np.random.uniform(params['blood_pressure']['min'], params['blood_pressure']['max']),
            random.choice([100, 90])  # Active or Normal movement
        ]
        for _ in range(num_samples // 2)
    ])
    
    # Cluster 1: Warning (slightly off normal)
    warning_data = np.array([
        [
            params['heart_rate']['normal'] + np.random.uniform(-15, 15),
            params['body_temp']['normal'] + np.random.uniform(-0.8, 0.8),
            params['blood_pressure']['normal'] + np.random.uniform(-20, 20),
            random.choice([60, 50, 90])  # Inactive, Low, or Normal
        ]
        for _ in range(num_samples // 3)
    ])
    
    # Cluster 2: Ill (significantly abnormal)
    ill_data = np.array([
        [
            params['heart_rate']['normal'] + np.random.uniform(-25, 25),
            params['body_temp']['normal'] + np.random.uniform(-2, 2),
            params['blood_pressure']['normal'] + np.random.uniform(-35, 35),
            random.choice([40, 50, 60])  # Lying Down, Low, or Inactive
        ]
        for _ in range(num_samples // 6)
    ])
    
    # Combine all data
    all_data = np.vstack([healthy_data, warning_data, ill_data])
    
    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    kmeans.fit(all_data)
    
    return kmeans, all_data


def simulate_reading(species, health_state='random'):
    """
    Simulate a single reading for an animal based on species
    health_state: 'healthy', 'warning', 'ill', or 'random'
    """
    params = get_species_params(species)
    
    if health_state == 'random':
        # 70% healthy, 20% warning, 10% ill
        rand = random.random()
        if rand < 0.70:
            health_state = 'healthy'
        elif rand < 0.90:
            health_state = 'warning'
        else:
            health_state = 'ill'
    
    if health_state == 'healthy':
        heart_rate = np.random.uniform(params['heart_rate']['min'], params['heart_rate']['max'])
        body_temp = np.random.uniform(params['body_temp']['min'], params['body_temp']['max'])
        bp_systolic = np.random.uniform(params['blood_pressure']['min'], params['blood_pressure']['max'])
        movement = random.choice(['Active', 'Normal'])
    elif health_state == 'warning':
        heart_rate = params['heart_rate']['normal'] + np.random.uniform(-12, 12)
        body_temp = params['body_temp']['normal'] + np.random.uniform(-0.6, 0.6)
        bp_systolic = params['blood_pressure']['normal'] + np.random.uniform(-18, 18)
        movement = random.choice(['Normal', 'Inactive', 'Low'])
    else:  # ill
        heart_rate = params['heart_rate']['normal'] + np.random.uniform(-20, 20)
        body_temp = params['body_temp']['normal'] + np.random.uniform(-1.5, 1.5)
        bp_systolic = params['blood_pressure']['normal'] + np.random.uniform(-30, 30)
        movement = random.choice(['Inactive', 'Lying Down', 'Low'])
    
    # Ensure values are within realistic bounds
    heart_rate = max(20, min(150, heart_rate))
    body_temp = max(35.0, min(42.0, body_temp))
    bp_systolic = max(70, min(180, bp_systolic))
    
    return {
        'heart_rate': round(heart_rate, 1),
        'body_temp': round(body_temp, 1),
        'blood_pressure': int(bp_systolic),
        'movement': movement
    }


def calculate_heart_rate_score(heart_rate, species):
    """Calculate heart rate score based on species-specific normal range"""
    params = get_species_params(species)
    normal = params['heart_rate']['normal']
    multiplier = params['heart_rate']['multiplier']
    
    deviation = abs(heart_rate - normal)
    score = max(0, 100 - deviation * multiplier)
    return round(score, 1)


def calculate_temp_score(body_temp, species):
    """Calculate body temperature score based on species-specific normal range"""
    params = get_species_params(species)
    normal = params['body_temp']['normal']
    multiplier = params['body_temp']['multiplier']
    
    deviation = abs(body_temp - normal)
    score = max(0, 100 - deviation * multiplier)
    return round(score, 1)


def calculate_bp_score(blood_pressure, species):
    """Calculate blood pressure score based on species-specific normal range"""
    params = get_species_params(species)
    normal = params['blood_pressure']['normal']
    multiplier = params['blood_pressure']['multiplier']
    
    deviation = abs(blood_pressure - normal)
    score = max(0, 100 - deviation * multiplier)
    return round(score, 1)


def calculate_movement_score(movement):
    """Calculate movement score"""
    return MOVEMENT_SCORES.get(movement, 70)


def calculate_health_index(heart_rate, body_temp, blood_pressure, movement, species):
    """
    Calculate overall health index using weighted formula
    Health_Index = 0.30 × HR_score + 0.30 × Temp_score + 0.20 × BP_score + 0.20 × Move_score
    """
    hr_score = calculate_heart_rate_score(heart_rate, species)
    temp_score = calculate_temp_score(body_temp, species)
    bp_score = calculate_bp_score(blood_pressure, species)
    move_score = calculate_movement_score(movement)
    
    health_index = (
        WEIGHTS['heart_rate'] * hr_score +
        WEIGHTS['body_temp'] * temp_score +
        WEIGHTS['blood_pressure'] * bp_score +
        WEIGHTS['movement'] * move_score
    )
    
    return round(health_index, 1)


def classify_health_status(health_index):
    """
    Classify health status based on health index
    80-100: Healthy
    50-79: Warning
    <50: Ill
    """
    if health_index >= 80:
        return 'Healthy'
    elif health_index >= 50:
        return 'Warning'
    else:
        return 'Ill'


def get_status_color(status):
    """Get color code for status"""
    colors = {
        'Healthy': 'green',
        'Warning': 'yellow',
        'Ill': 'red'
    }
    return colors.get(status, 'gray')


# Store for tracking consecutive readings (for alert logic)
consecutive_readings = {}

# Store for tracking previous readings (for gradual changes)
previous_readings = {}


def check_consecutive_alerts(animal_tag, status):
    """
    Check for consecutive abnormal readings
    Returns alert level: None, 'Alert', or 'Critical'
    """
    global consecutive_readings
    
    if animal_tag not in consecutive_readings:
        consecutive_readings[animal_tag] = []
    
    # Add current status
    consecutive_readings[animal_tag].append(status)
    
    # Keep only last 3 readings
    if len(consecutive_readings[animal_tag]) > 3:
        consecutive_readings[animal_tag] = consecutive_readings[animal_tag][-3:]
    
    readings = consecutive_readings[animal_tag]
    
    # Need at least 3 readings for alert
    if len(readings) < 3:
        return None
    
    # Check for 3 consecutive warnings
    if all(r == 'Warning' for r in readings[-3:]):
        return 'Alert'
    
    # Check for 3 consecutive ill
    if all(r == 'Ill' for r in readings[-3:]):
        return 'Critical'
    
    return None


def is_outlier_reading(new_reading, prev_reading, species):
    """
    Check if a new reading is an outlier compared to previous reading
    Returns True if the change is too drastic
    """
    if prev_reading is None:
        return False
    
    params = get_species_params(species)
    
    # Maximum allowed changes per 5-minute interval
    max_hr_change = 15  # bpm
    max_temp_change = 0.5  # °C
    max_bp_change = 20  # mmHg
    
    hr_change = abs(new_reading['heart_rate'] - prev_reading['heart_rate'])
    temp_change = abs(new_reading['body_temp'] - prev_reading['body_temp'])
    bp_change = abs(new_reading['blood_pressure'] - prev_reading['blood_pressure'])
    
    # Check for drastic changes
    if hr_change > max_hr_change or temp_change > max_temp_change or bp_change > max_bp_change:
        return True
    
    return False


def generate_gradual_reading(species, prev_reading=None):
    """
    Generate a reading that changes gradually from the previous reading
    If prev_reading is None, generates a random reading
    """
    params = get_species_params(species)
    
    if prev_reading is None:
        # First reading - generate normally
        return simulate_reading(species)
    
    # Maximum gradual changes per 5-minute interval
    max_hr_change = 8  # bpm
    max_temp_change = 0.3  # °C
    max_bp_change = 10  # mmHg
    
    # Generate small changes from previous reading
    hr_delta = np.random.uniform(-max_hr_change, max_hr_change)
    temp_delta = np.random.uniform(-max_temp_change, max_temp_change)
    bp_delta = np.random.uniform(-max_bp_change, max_bp_change)
    
    # Apply changes
    new_hr = prev_reading['heart_rate'] + hr_delta
    new_temp = prev_reading['body_temp'] + temp_delta
    new_bp = prev_reading['blood_pressure'] + bp_delta
    
    # Add a small random drift towards normal or abnormal
    # 70% chance to drift toward normal, 30% chance to stay/worsen
    if random.random() < 0.7:
        # Drift toward normal
        normal_hr = params['heart_rate']['normal']
        normal_temp = params['body_temp']['normal']
        normal_bp = params['blood_pressure']['normal']
        
        if new_hr > normal_hr:
            new_hr -= random.uniform(0, 2)
        elif new_hr < normal_hr:
            new_hr += random.uniform(0, 2)
            
        if new_temp > normal_temp:
            new_temp -= random.uniform(0, 0.1)
        elif new_temp < normal_temp:
            new_temp += random.uniform(0, 0.1)
            
        if new_bp > normal_bp:
            new_bp -= random.uniform(0, 3)
        elif new_bp < normal_bp:
            new_bp += random.uniform(0, 3)
    
    # Ensure values are within realistic bounds
    new_hr = max(params['heart_rate']['min'] - 10, min(params['heart_rate']['max'] + 10, new_hr))
    new_temp = max(params['body_temp']['min'] - 0.5, min(params['body_temp']['max'] + 0.5, new_temp))
    new_bp = max(params['blood_pressure']['min'] - 15, min(params['blood_pressure']['max'] + 15, new_bp))
    
    # Movement tends to stay similar
    if random.random() < 0.8:
        movement = prev_reading['movement']
    else:
        movements = ['Active', 'Normal', 'Inactive', 'Low']
        current_idx = movements.index(prev_reading['movement']) if prev_reading['movement'] in movements else 1
        # Move at most 1 step
        new_idx = max(0, min(len(movements) - 1, current_idx + random.choice([-1, 0, 0, 1])))
        movement = movements[new_idx]
    
    return {
        'heart_rate': round(new_hr, 1),
        'body_temp': round(new_temp, 1),
        'blood_pressure': int(new_bp),
        'movement': movement
    }


def generate_readings_history(species, num_readings=10):
    """Generate a history of readings for display in table"""
    readings = []
    current_time = datetime.now()
    
    for i in range(num_readings):
        # Generate reading
        reading_data = simulate_reading(species)
        
        # Calculate health index
        health_index = calculate_health_index(
            reading_data['heart_rate'],
            reading_data['body_temp'],
            reading_data['blood_pressure'],
            reading_data['movement'],
            species
        )
        
        # Classify status
        status = classify_health_status(health_index)
        
        # Calculate time (going backwards)
        reading_time = current_time - timedelta(hours=i)
        
        readings.append({
            'time': reading_time.strftime('%I:%M %p'),
            'timestamp': reading_time.isoformat(),
            'temperature': f"{reading_data['body_temp']}°C",
            'heart_rate': f"{reading_data['heart_rate']} bpm",
            'blood_pressure': f"{reading_data['blood_pressure']}/80",
            'movement': reading_data['movement'],
            'health_index': f"{health_index}%",
            'health_index_value': health_index,
            'status': status,
            'status_color': get_status_color(status)
        })
    
    return readings


def get_current_health_data(animal_tag, species):
    """Get current health data for an animal with gradual changes"""
    global previous_readings
    
    # Get previous reading for this animal
    prev_reading = previous_readings.get(animal_tag)
    
    # Generate new reading based on previous (gradual change)
    reading = generate_gradual_reading(species, prev_reading)
    
    # Check if this reading is an outlier (too different from previous)
    if prev_reading and is_outlier_reading(reading, prev_reading, species):
        # This is an outlier - mark it and regenerate a more gradual reading
        print(f"[{animal_tag}] Outlier detected, regenerating gradual reading...")
        reading = generate_gradual_reading(species, prev_reading)
    
    # Store this reading as the previous for next time
    previous_readings[animal_tag] = reading
    
    health_index = calculate_health_index(
        reading['heart_rate'],
        reading['body_temp'],
        reading['blood_pressure'],
        reading['movement'],
        species
    )
    
    status = classify_health_status(health_index)
    alert = check_consecutive_alerts(animal_tag, status)
    
    return {
        'animal_tag': animal_tag,
        'species': species,
        'heart_rate': reading['heart_rate'],
        'body_temp': reading['body_temp'],
        'blood_pressure': reading['blood_pressure'],
        'movement': reading['movement'],
        'health_index': health_index,
        'status': status,
        'status_color': get_status_color(status),
        'alert': alert,
        'timestamp': datetime.now().isoformat()
    }


def load_previous_readings_from_db():
    """Load the most recent readings from database to initialize previous_readings"""
    global previous_readings
    import sqlite3
    
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Get the latest reading for each animal
        cursor.execute('''
            SELECT animal_tag, heart_rate, body_temp, blood_pressure, movement 
            FROM health_readings 
            WHERE (animal_tag, timestamp) IN (
                SELECT animal_tag, MAX(timestamp) 
                FROM health_readings 
                GROUP BY animal_tag
            )
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            previous_readings[row[0]] = {
                'heart_rate': row[1],
                'body_temp': row[2],
                'blood_pressure': row[3],
                'movement': row[4]
            }
        
        print(f"Loaded previous readings for {len(previous_readings)} animals")
    except Exception as e:
        print(f"Could not load previous readings: {e}")


def get_species_normal_ranges(species):
    """Get normal ranges for a species for display"""
    params = get_species_params(species)
    return {
        'heart_rate': f"{params['heart_rate']['min']}-{params['heart_rate']['max']} bpm",
        'body_temp': f"{params['body_temp']['min']}-{params['body_temp']['max']} °C",
        'blood_pressure': f"{params['blood_pressure']['min']}-{params['blood_pressure']['max']} mmHg"
    }
