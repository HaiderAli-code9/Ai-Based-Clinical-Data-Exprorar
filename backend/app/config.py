# backend/app/config.py
import os
from dotenv import load_dotenv

# === Determine paths ===
current_dir = os.path.dirname(os.path.abspath(__file__))   # backend/app
backend_root = os.path.dirname(current_dir)                # backend/
project_root = os.path.dirname(backend_root)               # project root (if needed)

# Try multiple .env locations (in order of priority)
env_paths = [
    os.path.join(backend_root, ".env"),      # backend/.env
    os.path.join(project_root, ".env"),      # project-root/.env
    os.path.join(current_dir, ".env"),       # backend/app/.env
]

loaded = False
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        loaded = True
        print(f"[config] Loaded .env from: {env_path}")
        break

if not loaded:
    print("[config] WARNING: No .env file found. Trying default load_dotenv()")
    load_dotenv()

# === Database file is inside backend/dataset_sql_database/ ===
DB_PATH = os.path.join(backend_root, "dataset_sql_database", "mimic_iv_demo.db")
DB_URI = f"sqlite:///{DB_PATH.replace(os.sep, '/')}"

# === Google Gemini API Key (NOT AgentRouter) ===
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Debug prints ---
print(f"[config] DB_PATH: {DB_PATH}")
print(f"[config] DB exists: {os.path.exists(DB_PATH)}")
print(f"[config] GOOGLE_API_KEY: {GOOGLE_API_KEY[:10] if GOOGLE_API_KEY else '❌ NOT FOUND'}")

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"Database not found at {DB_PATH}. Please check the path.")