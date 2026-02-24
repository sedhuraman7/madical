from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import requests
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
from flask import session
import smtplib
from email.message import EmailMessage

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
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
            pre_diseases TEXT,
            phone TEXT,
            email TEXT
        )
    ''')
    try:
        c.execute('ALTER TABLE users ADD COLUMN phone TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE users ADD COLUMN email TEXT')
    except sqlite3.OperationalError:
        pass
    
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
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')
        weight = request.form.get('weight', '0')
        disease = request.form.get('disease', '')
        entered_otp = request.form.get('otp', '')
        
        # OTP Validation
        if entered_otp != str(session.get('current_otp', '1234')):
            return "Invalid OTP. Please try again.", 401
            
        password = "secure_user_pass" 
        hashed_pw = generate_password_hash(password)
        
        if username:
            username = username.strip()
            session['username'] = username
            session['role'] = 'patient'
            
            # Using UPDATE if EXISTS else INSERT logic
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute('''
                    INSERT INTO users (username, password, age, weight, gender, pre_diseases, phone, email) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET phone=?, email=?
                ''', (username, hashed_pw, 0, weight, 'Other', disease, phone, email, phone, email))
            except Exception:
                # Fallback if ON CONFLICT fails (SQLite version issues)
                c.execute('INSERT OR IGNORE INTO users (username, password, age, weight, gender, pre_diseases, phone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                      (username, hashed_pw, 0, weight, 'Other', disease, phone, email))
            conn.commit()
            conn.close()
            
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    req_data = request.json or {}
    phone = req_data.get('phone', '')
    email = req_data.get('email', '')
    
    if not phone or not email:
        return jsonify({"success": False, "message": "Phone and Email required"})
    
    # Generate 4 digit OTP
    otp = str(random.randint(1000, 9999))
    session['current_otp'] = otp
    
    # Sender Configuration (Using user credentials)
    SENDER_EMAIL = os.environ.get('MAIL_USER', 'sedhu1577@gmail.com')
    SENDER_PASS = os.environ.get('MAIL_PASS', 'eftkhehxsubmcnfx')
    
    try:
        # Create Email 
        msg = EmailMessage()

        msg['Subject'] = 'Your Health Ecosystem OTP'
        msg['From'] = f"AI Health Assistant <{SENDER_EMAIL}>"
        msg['To'] = email
        msg.set_content(f"Hello,\n\nYour OTP for registering on the AI Health Assessment portal is: {otp}\n\nPlease do not share this code with anyone.\n\nStay safe,\nAI Health Assistant Dashboard")

        # Send Email securely using Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASS)
            smtp.send_message(msg)
            
        print(f"OTP {otp} successfully sent to {email}")
    except Exception as e:
        print(f"SMTP Error: {e}")
        # Even if email fails, simulated SMS fallback
        return jsonify({"success": True, "message": f"Could not send Email, but simulated SMS generated. OTP is: {otp}", "otp": otp})

    return jsonify({"success": True, "message": f"Real OTP sent to {email}! Simulated SMS sent to {phone}. OTP is: {otp}", "otp": otp})

@app.route('/api/broadcast_alert', methods=['POST'])
def broadcast_alert():
    req_data = request.json or {}
    area = req_data.get('area', 'All')
    subject = req_data.get('subject', 'Emergency Health Alert')
    
    # Fetch user emails from DB for that area (or all)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE email IS NOT NULL AND email != ""')
    users = c.fetchall()
    conn.close()
    
    # Sender Configuration
    SENDER_EMAIL = os.environ.get('MAIL_USER', 'sedhu1577@gmail.com')
    SENDER_PASS = os.environ.get('MAIL_PASS', 'eftkhehxsubmcnfx')
    
    email_count = 0
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASS)
            
            for u in users:
                user_email = u[0]
                msg = EmailMessage()
                msg['Subject'] = f'🚨 OUTBREAK ALERT: {area}'
                msg['From'] = f"AI Health Assistant <{SENDER_EMAIL}>"
                msg['To'] = user_email
                msg.set_content(f"Emergency Health Alert!\n\nAn outbreak cluster has been detected in {area}.\n\nPlease take necessary precautions immediately and use our AI Chatbot to check your risk levels.\n\nStay Safe,\nPublic Health Intelligence Dashboard")
                
                smtp.send_message(msg)
                email_count += 1
                
        print(f"Successfully sent outbreak emails to {email_count} users.")
    except Exception as e:
        print(f"Broadcast SMTP Error: {e}")

    # For demo purposes, we'll pretend we sent to many SMS as well.
    sms_count = random.randint(12, 45) if area != 'All' else random.randint(150, 300)
    
    return jsonify({
        "success": True, 
        "message": f"Successfully broadcasted SMS to {sms_count} users, and Emails to {email_count} users in {area}!"
    })

@app.route('/admin/dashboard')
def admin_dashboard():
    # Public Health Intelligence Dashboard (Made fully public for Demo purposes)
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM assessments')
    all_rows = c.fetchall()
    
    # Gather unique areas for the filter dropdown
    all_areas = set()
    for row in all_rows:
        if row['location']:
            all_areas.add(row['location'].split(',')[0].strip())
    all_areas.add('Perambur') # Explicitly add our demo area
    all_areas = sorted(list(all_areas))
    
    selected_area = request.args.get('area', 'All')
    
    if selected_area != 'All':
        rows = [r for r in all_rows if r['location'] and r['location'].split(',')[0].strip() == selected_area]
    else:
        rows = all_rows
    
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
    if selected_area in ('All', 'Perambur'):
        demo_injected = False
        for cl in sorted_clusters:
            if "perambur" in cl['loc'].lower() and "fever" in cl['symp'].lower():
                if cl['count'] < 25:
                    cl['count'] += 25
                demo_injected = True
                break
                
        if not demo_injected:
            sorted_clusters.insert(0, {'loc': 'Perambur', 'symp': 'Fever', 'count': 25})
            
        total += 245
        high_risk_cases += 32
    
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
        "total_assessments": total, 
        "high_risk_cases": high_risk_cases,
        "top_symptom": top_symptom,
        "outbreak_alert": outbreak_alert,
        "top_outbreak_area": top_outbreak_area,
        "clusters": sorted_clusters[:5],
        "all_areas": all_areas,
        "selected_area": selected_area
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

@app.route('/check_phone', methods=['POST'])
def check_phone():
    req_data = request.json or {}
    phone = req_data.get('phone', '')
    if not phone:
        return jsonify({"exists": False})
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Check if column phone exists
    try:
        c.execute('SELECT 1 FROM users WHERE phone = ?', (phone,))
        if c.fetchone():
            conn.close()
            return jsonify({"exists": True})
    except sqlite3.OperationalError:
        pass # fallback if DB doesn't have phone column 
        
    conn.close()
    return jsonify({"exists": False})

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

# Strict phrase mapping to prevent false triggers
SYMPTOM_MAP = {
    "nenju vali": "chest_pain", "chest pain": "chest_pain", "heart": "chest_pain",
    "moochu": "breathing_issue", "breath": "breathing_issue", "moochu thinaral": "breathing_issue",
    "kai vali": "body_pain", "kall vali": "body_pain", "kaal vali": "body_pain", "leg pain": "body_pain", "hand pain": "body_pain", "udal vali": "body_pain",
    "fever": "fever", "kaichal": "fever", "kaachal": "fever", "kulir": "fever",
    "irumal": "cough", "cough": "cough", "thondai": "throat", "throat": "throat",
    "sali": "phlegm", "cold": "phlegm", "jaladosham": "phlegm",
    "thala vali": "headache", "thalavali": "headache", "head pain": "headache", "headache": "headache",
    "mayakkam": "unconsciousness", "faint": "unconsciousness", "unconscious": "unconsciousness",
    "ratham": "severe_bleeding", "bleeding": "severe_bleeding", "blood": "severe_bleeding"
}

def analyze_risk(symptoms, severity):
    risk_score = 0
    high_risk_symptoms = ["chest_pain", "breathing_issue", "unconsciousness", "severe_bleeding"]
    
    for s in symptoms:
        if s in high_risk_symptoms:
            risk_score += 10
        elif s == "fever":
            risk_score += 3
        else:
            risk_score += 1

    if severity == "severe":
        risk_score += 5
    elif severity == "moderate":
        risk_score += 2
        
    if risk_score >= 10: return "High"
    elif risk_score >= 5: return "Moderate"
    else: return "Low"

def generate_safe_response(state):
    risk = analyze_risk(state["symptoms"], state["severity"])
    lang = state.get("language", "tanglish")
    symptoms_joined = ", ".join(state["symptoms"]).replace("_", " ").title()

    if risk == "High":
        exp_en = f"The presence of {symptoms_joined} combined with your reported severity indicates a potentially serious medical situation."
        exp_ta = f"Neenga sonna {symptoms_joined} mattum ungal severity level-ai paarkumbothu, idhu konjam serious-ana prechanaiyaga therikirathu."
        action_en = "<li>Do NOT ignore these symptoms.</li><li>Avoid any physical exertion.</li><li>Contact emergency services or go to the nearest hospital immediately.</li>"
        action_ta = "<li>Indha arikurigalai (symptoms) ignore panna vendam.</li><li>Udalai varuthikolla vendam.</li><li>Udane emergency services allathu arugil ulla hospital-ku cellavum.</li>"
        doc_en = "<b>IMMEDIATELY.</b> Do not drive yourself. Have someone take you or call an ambulance."
        doc_ta = "<b>UDANE PAARKAVUM.</b> Neengal vandi otta vendam. Ambulance allathu veru yaraavathu udhavi moolam cellavum."
    elif risk == "Moderate":
        exp_en = f"Your symptoms ({symptoms_joined}) suggest a moderate issue that requires careful monitoring."
        exp_ta = f"Ungal arikurigal ({symptoms_joined}) konjam kavanikkapada vendiya prechanaiyaga therikirathu."
        action_en = "<li>Get plenty of rest and stay hydrated.</li><li>Monitor your temperature if you have a fever.</li><li>Take over-the-counter medication if you already know it's safe for you.</li>"
        action_ta = "<li>Nalla rest edunga, niraiya thanneer kudinga.</li><li>Fever irundhal temperature check pannunga.</li><li>Unkalukku set aagum basic medicines mattum use pannunga.</li>"
        doc_en = "Within the next 24-48 hours if symptoms do not improve, or immediately if they suddenly worsen."
        doc_ta = "Adutha 24-48 hours kullar sariyaagalana kandippa doctor-ai paarkavum."
    else:
        exp_en = f"Based on your inputs ({symptoms_joined}), this appears to be a mild and common condition."
        exp_ta = f"Neenga sonnathai vachu paarkumbothu ({symptoms_joined}), idhu oru saadharana (mild) prechanaiyaga therikirathu."
        action_en = "<li>Rest and relax at home.</li><li>Drink warm fluids to soothe your throat / body.</li><li>Maintain good hygiene.</li>"
        action_ta = "<li>Veetliye nalla rest edunga.</li><li>Warm water / fluids eduthukkonga.</li><li>Suthamaga irukkavum.</li>"
        doc_en = "If symptoms persist beyond 3-5 days or if you suddenly develop high fever or severe pain."
        doc_ta = "3-5 naatkaluku melayum prechanai irundhal allathu theedeerena theeviramanaal doctor-ai paarkavum."

    exp = exp_en if lang == "english" else exp_ta
    action = action_en if lang == "english" else action_ta
    doc = doc_en if lang == "english" else doc_ta

    color = "red" if risk == "High" else "#f59e0b" if risk == "Moderate" else "#10b981"

    formatted_reply = f"""
    <div>
        <h4 style="color:{color}; margin-bottom:10px;">Risk Level: {risk}</h4>
        <b>Explanation:</b><br>
        <p style="margin-bottom:10px;">{exp}</p>
        
        <b>What You Can Do:</b>
        <ul style="margin-bottom:10px; margin-left: 15px;">
            {action}
        </ul>
        
        <b>When To See Doctor:</b><br>
        <p style="margin-bottom:15px; color:#ef4444;">{doc}</p>
        
        <hr style="border-color: rgba(0,0,0,0.1); margin-bottom: 10px;">
        <i style="font-size: 0.8rem; color: #6b7280;">Disclaimer: This is AI-based health awareness guidance, not a medical diagnosis. Please consult a qualified doctor for actual medical advice.</i>
    </div>
    """
    return formatted_reply

@app.route('/api/chat', methods=['POST'])
def ai_chat():
    req = request.json
    if not req or 'message' not in req:
        return jsonify({"reply": "Enna problem nu sollunga? / How can I help you?"})
        
    msg = req['message'].lower()
    
    # Initialize Conversation Brain (Context Memory)
    if "chat_state" not in session or any(w in msg.split() for w in ["hi", "hello", "reset", "clear", "vanakkam", "restart"]):
        session["chat_state"] = {
            "symptoms": [], 
            "duration": None, 
            "severity": None,
            "stage": "collecting_symptoms", 
            "emergency_confirm": False, 
            "emergency_trigger_symps": [],
            "language": "tanglish"
        }
        if any(w in msg.split() for w in ["hi", "hello", "vanakkam"]):
            return jsonify({"reply": "Hello / Vanakkam! I am your AI Chat Doctor. I am here to help you understand your health better.<br><br>Ungalukku yethavadhu health problem irukka? / What seems to be the main problem?"})
        
    state = session["chat_state"]
    
    # Dynamic Language Detection
    eng_keywords = ["have", "am", "is", "pain", "my", "head", "body", "yes", "no", "not", "fever", "cough", "days", "cold", "throat", "severe", "mild", "moderate"]
    tan_keywords = ["iruku", "illa", "vali", "aama", "enna", "oru", "mattum", "kaichal", "thalavali", "udambu", "naal", "rendu", "moonu", "romba", "konjam", "theevirama"]
    
    eng_count = sum(1 for w in eng_keywords if w in msg.split())
    tan_count = sum(1 for w in tan_keywords if w in msg.split())
    if eng_count > tan_count:
        state["language"] = "english"
    elif tan_count > eng_count:
        state["language"] = "tanglish"
        
    lang = state.get("language", "tanglish")
    
    # --- STAGE: EMERGENCY CONFIRMATION ---
    if state["emergency_confirm"]:
        if any(w in msg.split() for w in ["aama", "yes", "true", "iruku", "yeah"]):
            state["stage"] = "end"
            session.modified = True
            reply_ta = f"🚨 ALARM: Neenga sonna ({', '.join(state['emergency_trigger_symps']).replace('_', ' ')}) confirm aagivittathu. PLEASE DO NOT DRIVE YOURSELF. Udane arugil ulla hospital allathu ambulance-ai thodarbu kollavum!"
            reply_en = f"🚨 ALARM: ({', '.join(state['emergency_trigger_symps']).replace('_', ' ')}) confirmed. PLEASE DO NOT DRIVE YOURSELF. Call an ambulance or go to the ER immediately!"
            return jsonify({"reply": reply_en if lang == "english" else reply_ta})
        else:
            state["emergency_confirm"] = False
            state["emergency_trigger_symps"] = [] # Clear the false triggers
            session.modified = True
            reply = "Phew, that's a relief! Let's continue. What exactly is the problem?" if lang == "english" else "Phew, that's a relief! Sari, ippo ungalukku sariyaga enna panuthu thodarnthu sollunga."
            return jsonify({"reply": reply})
    
    # --- NLP Symptom Extraction ---
    new_symptoms = []
    # Avoid substring matching issues by checking words where possible
    msg_words = msg.split()
    for key, value in SYMPTOM_MAP.items():
        if key in msg and value not in state["symptoms"]:
            state["symptoms"].append(value)
            new_symptoms.append(value)
            
    # --- Emergency Interception (Context Check) ---
    high_risk_triggers = ["chest_pain", "breathing_issue", "unconsciousness", "severe_bleeding"]
    detected_emergencies = [s for s in new_symptoms if s in high_risk_triggers]
    if detected_emergencies:
        state["emergency_confirm"] = True
        state["emergency_trigger_symps"] = detected_emergencies
        # Remove them temporarily from main symptoms list until confirmed
        for s in detected_emergencies:
            state["symptoms"].remove(s)
        session.modified = True
        reply_en = f"⚠️ Wait, to be absolutely safe: Are you confirming that you have severe {', '.join(detected_emergencies).replace('_', ' ')}? (Please answer clearly: Yes or No)"
        reply_ta = f"⚠️ Oru nimidam, ungalukku theeviramana {', '.join(detected_emergencies).replace('_', ' ')} irukkirathai confirm seigireergala? (Aama / Illai yendru thelivaga sollavum)"
        return jsonify({"reply": reply_en if lang == "english" else reply_ta})
        
    # --- Conversation Flow State Machine ---
    
    # Extract Duration loosely anytime a number is typed
    for num_word, val in {"1": 1, "oru": 1, "onnu": 1, "one": 1, "2": 2, "two": 2, "rendu": 2, "3": 3, "moonu": 3, "three": 3, "4":4, "naalu":4, "5":5, "anju":5}.items():
        if num_word in msg_words:  
            state["duration"] = val
            break
            
    # Extract Severity loosely anytime
    if any(w in msg_words for w in ["severe", "romba", "bad", "heavy", "theevirama"]):
        state["severity"] = "severe"
    elif any(w in msg_words for w in ["moderate", "medium", "normal", "mediokari"]):
        state["severity"] = "moderate"
    elif any(w in msg_words for w in ["mild", "konjam", "light", "little"]):
        state["severity"] = "mild"

    reply = ""

    if state["stage"] == "collecting_symptoms":
        if not state["symptoms"]:
            reply = "I didn't quite understand. Could you please describe your main symptom clearly? (e.g. fever, headache, stomach pain)" if lang == "english" else "Sariyaga puriyavillai. Ungal prechanaiyai thelivaga sollavum. (e.g. fever, thalavali)"
        else:
            state["stage"] = "collecting_duration"
            
    if state["stage"] == "collecting_duration":
        if not state["duration"]:
            s_str = ', '.join(state['symptoms']).replace('_', ' ').title()
            reply = f"Thank you. I understand you have {s_str}. How many days has it been since this started?" if lang == "english" else f"Okay, ungalukku {s_str} irukkirathu. Idhu evvalavu naatkalaaga (How many days) irukku?"
        else:
            state["stage"] = "collecting_severity"
            
    if state["stage"] == "collecting_severity":
        if not state["severity"]:
            reply = "Got it. How severe is this feeling right now? Please say Mild, Moderate, or Severe." if lang == "english" else "Purigirathu. Idhu eppadi thuuramaaga intha vali/prechanai irukku? (Konjam, Normal, allathu Romba theeviramava? / Mild, Moderate, Severe?)"
        else:
            state["stage"] = "collecting_related"
            
    if state["stage"] == "collecting_related":
        # If we just arrived here, ask once. If they reply, we process the extracted symptoms and move to advising.
        if "asked_related" not in state:
            state["asked_related"] = True
            reply = "Almost done! Do you have any other related problems along with this? (e.g., headache with fever)? If no, just say 'No'." if lang == "english" else "Kadaisi kelvi! Idhu koodave vera edhavadhu related prechanaigal irukka? Illai yendral 'No/Illai' yendru sollavum."
        else:
            # We already asked, so whatever they typed was processed for symptoms. Time to give advice.
            state["stage"] = "advising"
            
    if state["stage"] == "advising":
        reply = generate_safe_response(state)
        # Reset simple status to allow them to ask again without refreshing
        state["stage"] = "collecting_symptoms"
        state["symptoms"] = []
        state["duration"] = None
        state["severity"] = None
        state["emergency_confirm"] = False
        if "asked_related" in state: del state["asked_related"]
            
    # Special catch-all if they just say raw yes/no out of context
    if reply == "" and any(w in msg.split() for w in ["yes", "no", "aama", "illa", "illai"]):
        if lang == "english":
             reply = "Could you please elaborate a bit more on your symptoms?"
        else:
             reply = "Vera details konjam thelivaga solla mudiyuma?"
             
    session["chat_state"] = state
    return jsonify({"reply": reply})


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
    app.run(debug=True, port=5001)
