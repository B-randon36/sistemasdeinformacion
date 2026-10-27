import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_NAME = os.getenv("PROJECT_NAME", "Balanced Scorecard - AGRO PERUVIAN FOODS S.A.C.")
API_V1_STR = os.getenv("API_V1_STR", "/api/v1")
SECRET_KEY = os.getenv("SECRET_KEY", "agroperuvian_secret_token_bsc_2026")
PORT = int(os.getenv("PORT", "8001"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agroperuvian_bsc.db")

ODOO_URL = os.getenv("ODOO_URL", "http://odoo:8069")
ODOO_DB = os.getenv("ODOO_DB", "agroperuvian_db")
ODOO_USER = os.getenv("ODOO_USER", "admin@agroperuvian.pe")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin_odoo_secure_2026")

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/bsc-kpi-sync")
