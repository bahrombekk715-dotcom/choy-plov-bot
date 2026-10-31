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

# PostgreSQL ulanish manzili: postgresql://foydalanuvchi:parol@host:5432/baza_nomi
# (Render/Neon/Supabase kabi xizmatlar bergan DATABASE_URL ni shundayligicha qo'ying)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://choyplov:choyplov@localhost:5432/choyplov')

# "Bugun" va kunlik hisobotlar hisoblanadigan vaqt zonasi (standart: O'zbekiston)
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Tashkent')

# Eski SQLite bazadan ko'chirish skripti uchun (migrate_sqlite_to_postgres.py)
SQLITE_PATH = os.getenv('SQLITE_PATH', 'data/bot.db')

# Yuklangan rasmlar data/ papkada (Docker'da shu papka volume qilinadi, qayta ishga tushganda yo'qolmaydi)
UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'data/uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Faqat lokal sinash uchun: ?dev_user=ID bilan Telegramsiz kirish (production'da o'chiq turishi kerak)
DEV_MODE = os.getenv('DEV_MODE', '') == '1'

# Mijozlar uchun "Qo'llab-quvvatlash" (profil sahifasida ko'rinadi). Ikkalasi ixtiyoriy.
SUPPORT_USERNAME = os.getenv('SUPPORT_USERNAME', '').strip().lstrip('@')   # Telegram username, @siz
SUPPORT_PHONE = os.getenv('SUPPORT_PHONE', '').strip()                      # masalan +998901234567
