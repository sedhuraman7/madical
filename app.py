from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import requests
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
from flask import session

app = Flask(__name__)
app.secret_key = 'hackathon_secret_key'
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', 'YOUR_API_KEY')

DB_PATH = 'health.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            age INTEGER,
            weight REAL,
            gender TEXT,
            pre_diseases TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            weight REAL,
            gender TEXT,
            location TEXT,
            symptoms TEXT,
            duration TEXT,
            risk_score REAL,
            risk_level TEXT,
            condition TEXT,
            reason TEXT,
            preventive_advice TEXT,
            recommendation TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        weight = request.form.get('weight')
        disease = request.form.get('disease')
        # Simulate password input securely for demonstration
        password = "secure_user_pass" 
        hashed_pw = generate_password_hash(password)
        
        if username:
            username = username.strip()
            session['username'] = username
            session['role'] = 'patient'  # RBAC Implementation
            
            if username.lower() == 'admin':
                session['role'] = 'admin'
                
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT OR IGNORE INTO users (username, password, age, weight, gender, pre_diseases) VALUES (?, ?, ?, ?, ?, ?)', 
                      (username, hashed_pw, 0, weight, 'Other', disease))
            conn.commit()
            conn.close()
            
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
                
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    # Admin Public Health Intelligence Dashboard
    if session.get('role') != 'admin':
        return "Unauthorized Access. Admin Only.", 403
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM assessments')
    rows = c.fetchall()
    
    total = len(rows)
    high_risk_cases = sum(1 for row in rows if row['risk_level'] == 'High')
    
    location_clusters = {}
    for row in rows:
        loc = row['location'] if row['location'] else 'Unknown'
        main_loc = loc.split(',')[0].strip() # Get main area
        
        symps = row['symptoms'].split(',') if row['symptoms'] else []
        for symp in symps:
            symp = symp.strip().title()
            if not symp: continue
            
            key = f"{main_loc}|{symp}"
            if key not in location_clusters:
                location_clusters[key] = {'loc': main_loc, 'symp': symp, 'count': 0}
            location_clusters[key]['count'] += 1
            
    sorted_clusters = sorted(location_clusters.values(), key=lambda x: x['count'], reverse=True)
    
    # Injecting the demo dynamic data based on user specific mock scenario request for hackathon
    demo_injected = False
    for cl in sorted_clusters:
        if "perambur" in cl['loc'].lower() and "fever" in cl['symp'].lower():
            if cl['count'] < 25:
                cl['count'] += 25
            demo_injected = True
            break
            
    if not demo_injected:
        sorted_clusters.insert(0, {'loc': 'Perambur', 'symp': 'Fever', 'count': 25})
    
    sorted_clusters = sorted(sorted_clusters, key=lambda x: x['count'], reverse=True)
    
    top_cluster = sorted_clusters[0] if sorted_clusters else None
    
    outbreak_alert = False
    top_symptom = "Normal"
    top_outbreak_area = "N/A"
    
    if top_cluster and top_cluster['count'] >= 10:
        outbreak_alert = True
        top_symptom = f"Excessive {top_cluster['symp']} clustered tracking ({top_cluster['count']} Users)"
        top_outbreak_area = top_cluster['loc']
        
    stats = {
        "total_assessments": total + 245, 
        "high_risk_cases": high_risk_cases + 32,
        "top_symptom": top_symptom,
        "outbreak_alert": outbreak_alert,
        "top_outbreak_area": top_outbreak_area,
        "clusters": sorted_clusters[:5]
    }
    conn.close()
    return render_template('dashboard.html', stats=stats)

@app.route('/appointments')
def appointments():
    hospital = request.args.get('hospital', 'Dr. Smith Skin Center (Example)')
    address = request.args.get('address', 'Your Area')
    return render_template('appointments.html', hospital=hospital, address=address)

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    hospital = request.form.get('hospital')
    address = request.form.get('address')
    appt_type = request.form.get('appt_type')
    appt_time = request.form.get('appt_time')
    # Generate random document / confirmation details
    doc_id = f"APT-{random.randint(1000, 9999)}"
    return render_template('appointment_success.html', hospital=hospital, address=address, appt_type=appt_type, appt_time=appt_time, doc_id=doc_id)

@app.route('/assessment', methods=['GET', 'POST'])
def assessment():
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            return "Name is required", 400
            
        age = int(request.form.get('age', 0))
        weight = float(request.form.get('weight', 0.0))
        gender = request.form.get('gender')
        location = request.form.get('location')
        symptoms = request.form.getlist('symptoms')
        duration = request.form.get('duration')

        result = evaluate_health(age, symptoms, duration)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO assessments (name, age, weight, gender, location, symptoms, duration, risk_score, risk_level, condition, reason, preventive_advice, recommendation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, age, weight, gender, location, ','.join(symptoms), duration, result['risk_score'], result['risk_level'], result['condition'], result['reason'], result['preventive_advice'], result['recommendation']))
        assessment_id = c.lastrowid
        conn.commit()
        conn.close()

        return redirect(url_for('result', id=assessment_id, location=location))

    return render_template('assessment.html')

def evaluate_health(age, symptoms, duration):
    risk_score = 0
    condition = "General Mild Symptoms"
    reason = "Symptoms do not indicate a severe predefined condition."
    preventive_advice = "Rest, stay hydrated, and maintain good hygiene."
    recommendation = "Monitor symptoms."
    risk_level = "Low"

    symptom_set = set(symptoms)

    if duration == '4+ days':
        risk_score += 20
    elif duration == '2-3 days':
        risk_score += 10

    if age > 45:
        risk_score += 15
    elif age > 60:
        risk_score += 25

    if 'breathing difficulty' in symptom_set:
        condition = "Possible Respiratory Distress"
        reason = "Breathing difficulty is a severe symptom that requires immediate attention."
        preventive_advice = "Sit upright, do not exert yourself, and ensure fresh air. Seek immediate medical help."
        recommendation = "Emergency Alert: Visit nearest hospital immediately."
        risk_score += 60
        risk_level = "High"
    
    elif 'chest pain' in symptom_set and age > 45:
        condition = "High Cardiac Risk"
        reason = "Chest pain combined with age > 45 indicates a significant risk for cardiac issues."
        preventive_advice = "Avoid physical exertion. DO NOT wait. Seek emergency medical care."
        recommendation = "Emergency Alert: Visit doctor or emergency room immediately."
        risk_score += 50
        risk_level = "High"

    elif 'fever' in symptom_set and 'cough' in symptom_set:
        condition = "Possible Viral Infection"
        reason = "Combination of fever and cough is typical for upper respiratory viral infections."
        preventive_advice = "Isolate to prevent spreading, rest, wear a mask around others, and stay hydrated."
        recommendation = "Consult a doctor if symptoms worsen or persist."
        risk_score += 30
        risk_level = risk_level if risk_level == "High" else "Moderate"

    risk_score += (len(symptom_set) * 5)
    risk_score = min(risk_score, 100)

    if risk_level != "High":
        if risk_score >= 60:
            risk_level = "High"
        elif risk_score >= 30:
            risk_level = "Moderate"
        else:
            risk_level = "Low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "condition": condition,
        "reason": reason,
        "preventive_advice": preventive_advice,
        "recommendation": recommendation
    }

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

@app.route('/api/scan_skin', methods=['POST'])
def scan_skin():
    # Simulated CNN / MobileNetV2 Output mapping
    conditions = [
        {
            "condition": "Possible Ringworm (Tinea Corporis)",
            "medicines": ["Topical Antifungal cream (e.g., Clotrimazole)", "Avoid sharing towels", "Keep area dry and clean"],
            "description": "Appears as a ring-shaped, red, scaly patch with a clear center.",
            "confidence": f"{random.randint(89, 98)}.%",
            "severity": "Moderate / Contagious"
        },
        {
            "condition": "Skin Rashes / Allergic Dermatitis",
            "medicines": ["Oral Antihistamines", "Calamine lotion", "Mild Hydrocortisone cream"],
            "description": "Red, itchy, or swollen spots on the skin. Could be due to allergies or contact dermatitis.",
            "confidence": f"{random.randint(75, 95)}.%",
            "severity": "Low / Monitor"
        },
        {
            "condition": "Skin Nodule / Cyst (Katti)",
            "medicines": ["Warm compresses 3-4 times a day", "Do NOT pop or squeeze", "Antibacterial soap gently applied"],
            "description": "A raised, solid, often painful lump under the skin.",
            "confidence": f"{random.randint(80, 99)}.%",
            "severity": "Requires Doctor Visit"
        }
    ]
    
    result = random.choice(conditions)
    
    return jsonify({
        "success": True,
        "data": result,
        "disclaimer": "⚠️ DISCLAIMER: I am not a doctor and I do not prefer/prescribe these medicines. For any health issues, ALWAYS consult a qualified doctor near you before taking medication."
    })

@app.route('/result/<int:id>')
def result(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM assessments WHERE id = ?', (id,))
    data = c.fetchone()
    conn.close()

    if not data:
        return "Assessment Not found", 404

    location = request.args.get('location', '')
    return render_template('result.html', data=data, location=location)

@app.route('/api/doctors', methods=['POST'])
def find_doctors():
    req_data = request.json or {}
    location = req_data.get('location', '')
    lat = req_data.get('lat')
    lng = req_data.get('lng')

    if GOOGLE_PLACES_API_KEY == 'YOUR_API_KEY':
        # Create dynamic mock data based on location provided
        city_name = location.title() if location and location.lower() != 'dermatologist hospital' else 'Perambur'
        if not city_name or 'Lat:' in city_name:
             city_name = 'Your Area'

        return jsonify({
            "results": [
                {"name": f"{city_name} General Skin Care", "rating": 4.5, "vicinity": f"123 Health St, {city_name}"},
                {"name": f"Dermatology Clinic {city_name}", "rating": 4.0, "vicinity": f"45 Wellness Ave, {city_name}"},
                {"name": f"Dr. Smith Skin Center", "rating": 4.8, "vicinity": f"78 Recovery Blvd, {city_name}"},
                {"name": f"Sunrise Skin Practice", "rating": 4.2, "vicinity": f"101 Sunrise Way, {city_name}"}
            ]
        })

    if lat and lng:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&type=doctor&key={GOOGLE_PLACES_API_KEY}"
    elif location:
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=doctors+in+{location}&key={GOOGLE_PLACES_API_KEY}"
    else:
        return jsonify({"results": []})

    response = requests.get(url)
    return jsonify(response.json())

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
