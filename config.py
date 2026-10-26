import os
import secrets
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0) or 0)
WEB_APP_URL = os.getenv('WEB_APP_URL', 'http://localhost:8000').rstrip('/')

# Web admin panelga telegramsiz (brauzerdan) kirish paroli. Bo'sh bo'lsa faqat ADMIN_ID orqali kiriladi.
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')

# Admin tokenlarini imzolash kaliti. Berilmasa BOT_TOKEN dan olinadi (restartda ham o'zgarmaydi).
SECRET_KEY = os.getenv('SECRET_KEY') or BOT_TOKEN or secrets.token_hex(16)

# Baza va yuklangan rasmlar data/ papkada (Docker'da shu papka volume qilinadi, qayta ishga tushganda yo'qolmaydi)
DB_PATH = os.getenv('DB_PATH', 'data/bot.db')
UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'data/uploads')
for _p in (os.path.dirname(DB_PATH), UPLOAD_DIR):
    if _p:
        os.makedirs(_p, exist_ok=True)

# Faqat lokal sinash uchun: ?dev_user=ID bilan Telegramsiz kirish (production'da o'chiq turishi kerak)
DEV_MODE = os.getenv('DEV_MODE', '') == '1'
