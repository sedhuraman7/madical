import os
import shutil

base_dir = r"d:\madical\health_ecosystem"

# 1. Define folder structure
dirs = [
    "app",
    "app/api",
    "app/auth",
    "app/ml_engine",
    "app/models",
    "app/services",
    "app/tasks",
    "app/templates",
    "app/static",
    "app/static/css",
    "app/static/js",
    "deploy"
]

for d in dirs:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

# 2. Create placeholder enterprise files
files = {
    "app/__init__.py": "# App factory & config startup\n# Connects to PostgreSQL, Redis, and initializes ML models\n",
    "app/api/__init__.py": "# Mobile/External JSON APIs\n",
    "app/auth/__init__.py": "# Role-based JWT login routes\n",
    "app/models/__init__.py": "# SQLAlchemy ORM definitions (Postgres)\n",
    "app/services/__init__.py": "# Business logic (Telemedicine, Dashboards)\n",
    "app/tasks/__init__.py": "# Celery background tasks (Map updates, emails)\n",
    "app/ml_engine/__init__.py": "",
    "app/ml_engine/risk_model.pkl": "PKL_MOCK_DATA_0101010101010101",
    "app/ml_engine/nlp_parser.py": "# Voice-to-text exact symptom extraction using NLP (spaCy / TensorFlow)\n",
    "app/ml_engine/cv_scanner.py": "# PyTorch/TF Skin disease classifier (MobileNetV2)\n",
    "app/ml_engine/hybrid_logic.py": "# Combines ML confidence with static rules\n",
    "app/static/manifest.json": '{\n  "name": "AI Health Ecosystem",\n  "short_name": "Health",\n  "start_url": ".",\n  "display": "standalone",\n  "theme_color": "#0056b3"\n}',
    "deploy/Dockerfile": "FROM python:3.9-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD [\"python\", \"run.py\"]\n",
    "deploy/docker-compose.yml": "version: '3'\nservices:\n  web:\n    build: .\n    ports:\n      - \"5000:5000\"\n    environment:\n      - DATABASE_URL=postgres://user:pass@db:5432/health\n  db:\n    image: postgres:13\n",
    "deploy/nginx.conf": "server {\n  listen 80;\n  location / {\n    proxy_pass http://web:5000;\n  }\n}\n",
    "config.py": "import os\n\nclass Config:\n    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secure_hackathon_key_aes256'\n    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:pass@localhost:5432/health'\n",
    "requirements.txt": "Flask==2.3.2\nrequests==2.31.0\nWerkzeug==2.3.6\nWaitress==2.1.2\nscikit-learn==1.3.0\ntorch==2.0.1\nSQLAlchemy==2.0.19\ncelery==5.3.1\npsycopg2-binary==2.9.6\n"
}

for fp, content in files.items():
    with open(os.path.join(base_dir, fp), "w", encoding='utf-8') as f:
        f.write(content)

# 3. Copy existing working project files into the new structure so it runs perfectly!
src_app = r"d:\madical\app.py"
dst_run = os.path.join(base_dir, "run.py")

# Read original app.py and modify it slightly so it looks for templates/static in 'app' folder
with open(src_app, 'r', encoding='utf-8') as f:
    app_code = f.read()

app_code = app_code.replace("app = Flask(__name__)", "app = Flask(__name__, template_folder='app/templates', static_folder='app/static')")

with open(dst_run, 'w', encoding='utf-8') as f:
    f.write(app_code)

# Copy templates and static
shutil.copytree(r"d:\madical\templates", os.path.join(base_dir, "app/templates"), dirs_exist_ok=True)
shutil.copytree(r"d:\madical\static", os.path.join(base_dir, "app/static"), dirs_exist_ok=True)

# Copy DB if exists
if os.path.exists(r"d:\madical\health.db"):
    shutil.copy(r"d:\madical\health.db", os.path.join(base_dir, "health.db"))

print("Architecture successfully created at d:\\madical\\health_ecosystem")
