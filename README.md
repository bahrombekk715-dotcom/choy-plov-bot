# 🍽 Choy Plov - Telegram Web App Bot

Telegram orqali ovqat buyurtma qilish boti - to'liq Web App integratsiyasi bilan.

## ✨ Xususiyatlar

### 👥 Foydalanuvchilar uchun:
- 📱 Telegram orqali telefon raqam bilan ro'yxatdan o'tish
- 🌐 **Ko'p tillilik** - O'zbek, Rus va Ingliz tillari (3 ta til)
- 🌐 **To'liq Web App** - Go'zal va zamonaviy interfeys
- 🍽 Kategoriyalar va mahsulotlardan buyurtma berish
- 🛒 Savat (Shopping Cart) funksiyasi
- ➕ Qo'shimcha ingredientlar tanlash (go'sht, tuxum, qazi)
- 📦 Buyurtmalar tarixi
- 👤 Profil ko'rish
- 💰 Real-time narx hisoblash

### 👨‍💼 Admin uchun:
- 📋 Yangi buyurtmalarni ko'rish va tasdiqlash/bekor qilish
- ➕ Mahsulot va kategoriya qo'shish
- ✏️ Mahsulotlarni tahrirlash
- 🔴 Mahsulotlarni to'xtatish/yoqish (availability)
- 🗑 Mahsulotlarni o'chirish
- 📊 Bugungi savdo statistikasi
- 💵 Faqat naqd to'lov

## 🏗 Arxitektura

```
┌─────────────────┐
│  Telegram Bot   │ ← Foydalanuvchi bilan interfeys
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
┌───▼───┐  ┌───▼────┐
│  Bot  │  │Web App │ ← FastAPI + HTML/CSS/JS
└───┬───┘  └───┬────┘
    │          │
    └────┬─────┘
         │
    ┌────▼────┐
    │Database │ ← SQLite
    └─────────┘
```

## 📁 Fayl strukturasi

```
choy-plov-bot/
├── bot.py                    # Telegram bot logikasi
├── webapp.py                 # FastAPI web server
├── main.py                   # Bot va Web serverni birga ishga tushirish
├── database.py               # SQLite database
├── keyboards.py              # Telegram klaviaturalar
├── config.py                 # Konfiguratsiya
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker image
├── docker-compose.yml        # Docker compose
├── .env.example              # Environment variables namunasi
├── README.md                 # Dokumentatsiya
└── web/
    ├── templates/
    │   └── index.html        # Web App HTML
    └── static/
        ├── css/
        │   └── style.css     # Stillar
        └── js/
            └── app.js        # Frontend logikasi
```

## 🚀 O'rnatish va ishga tushirish

### 1️⃣ Lokal ishga tushirish

```bash
# Repositoryni klonlash
git clone https://github.com/bahrombekk715-dotcom/choy-plov-bot.git
cd choy-plov-bot

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows

# Dependencies o'rnatish
pip install -r requirements.txt

# .env faylini yaratish
cp .env.example .env
nano .env  # yoki boshqa editor
```

`.env` faylini to'ldiring:
```env
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_ID=your_telegram_id
WEB_APP_URL=http://localhost:8000
```

```bash
# Botni ishga tushirish
python main.py
```

### 2️⃣ Docker bilan ishga tushirish

```bash
# .env faylini yaratish va to'ldirish
cp .env.example .env
nano .env

# Docker container build va run
docker-compose up -d

# Loglarni ko'rish
docker-compose logs -f

# To'xtatish
docker-compose down
```

## 🌐 Render.com ga deploy qilish

### Qadamma-qadam qo'llanma:

#### 1. GitHub repository tayyor
✅ Repository allaqachon yaratilgan: https://github.com/bahrombekk715-dotcom/choy-plov-bot

#### 2. Render.com da Web Service yaratish

1. **Render.com** ga kiring: https://render.com
2. **"New +"** → **"Web Service"** tanlang
3. GitHub reponi ulang: `choy-plov-bot`
4. Sozlamalarni kiriting:

```
Name: choy-plov-bot
Region: Frankfurt (EU Central) yoki Singapore
Branch: main
Runtime: Docker
Instance Type: Free (yoki Starter)
```

5. **Environment Variables** qo'shing:

```
BOT_TOKEN = <BotFather dan olgan token>
ADMIN_ID = <Sizning Telegram ID>
WEB_APP_URL = https://choy-plov-bot.onrender.com
```

⚠️ **Muhim:** `WEB_APP_URL` ni Render bergan URL bilan almashtiring!

6. **Create Web Service** tugmasini bosing

#### 3. Bot Token olish

1. Telegram da [@BotFather](https://t.me/botfather) ga boring
2. `/newbot` yuboring
3. Bot nomini kiriting: `Choy Plov`
4. Username kiriting: `choy_plov_uz_bot` (yoki boshqa unikal nom)
5. Tokenni Render.com ga qo'shing

#### 4. Admin ID topish

1. [@userinfobot](https://t.me/userinfobot) ga `/start` yuboring
2. ID raqamingizni ko'rsatadi
3. Uni Render.com ga qo'shing

#### 5. Web App URL sozlash

Deploy tugagandan keyin:

1. Render.com sizga URL beradi: `https://choy-plov-bot.onrender.com`
2. Bu URLni `bot.py` faylida `WEB_APP_URL` ga qo'ying
3. Git push qiling:

```bash
# bot.py da WEB_APP_URL ni yangilang
git add bot.py
git commit -m "Update Web App URL for production"
git push origin main
```

4. Render avtomatik qayta deploy qiladi

#### 6. Testlash

1. Telegram botingizga `/start` yuboring
2. Telefon raqamni ulashing
3. "🍽 Menyu" tugmasini bosing
4. Web App ochiladi va buyurtma bera olasiz!

## 🔧 Texnologiyalar

- **Backend:**
  - Python 3.11
  - aiogram 3.x - Telegram Bot Framework
  - FastAPI - Web API Framework
  - aiosqlite - Async SQLite database
  - uvicorn - ASGI server

- **Frontend:**
  - HTML5 / CSS3 / JavaScript
  - Telegram Web App API
  - Responsive design

- **DevOps:**
  - Docker / Docker Compose
  - Git / GitHub
  - Render.com

## 📱 Foydalanish

### Foydalanuvchi sifatida:

1. Botga `/start` yuboring
2. 📱 Telefon raqamingizni ulashing
3. 🍽 **"Menyu"** tugmasini bosing (Web App ochiladi)
4. Kategoriyani tanlang
5. Mahsulot tanlang va miqdorni belgilang
6. ➕ Qo'shimcha ingredientlar qo'shing (ixtiyoriy)
7. 🛒 Savatchaga qo'shing
8. ✅ Buyurtmani rasmiylashtiring
9. 📍 Manzil va telefon raqamingizni kiriting
10. Tasdiqlang!

### Admin sifatida:

1. Botga `/start` yuboring (avtomatik admin panel ochiladi)
2. 📋 Yangi buyurtmalarni ko'ring
3. ✅ Tasdiqlang yoki ❌ Bekor qiling
4. ➕ Yangi mahsulot qo'shing
5. 📊 Bugungi statistikani ko'ring
6. 🔴 Mahsulotlarni stop/start qiling

## 🔐 Xavfsizlik

- Admin faqat `ADMIN_ID` orqali aniqlanadi
- Barcha buyurtmalar database da saqlanadi
- Telegram Web App `initData` orqali autentifikatsiya
- HTTPS orqali xavfsiz aloqa

## 🐛 Debugging

### Loglarni ko'rish:

**Lokal:**
```bash
python main.py
# yoki
docker-compose logs -f
```

**Render.com:**
- Dashboard → Logs bo'limiga o'ting

### Umumiy muammolar:

1. **Web App ochilmaydi:**
   - `WEB_APP_URL` to'g'ri sozlanganmi tekshiring
   - Render deploy tugaganmi va ishlab turibmi tekshiring

2. **Admin panel ko'rinmaydi:**
   - `ADMIN_ID` to'g'ri kiritilganmi tekshiring
   - Botni qayta ishga tushiring

3. **Buyurtmalar saqlanmaydi:**
   - Database bilan bog'lanishni tekshiring
   - Loglarni ko'ring

## 📈 Kelajakdagi yangilanishlar

- [ ] Online to'lov integratsiyasi (Click, Payme, Uzum)
- [ ] Geolokatsiya orqali manzil tanlash
- [ ] Mahsulot rasmlari
- [ ] Chegirmalar va promo kodlar
- [ ] Yetkazib beruvchi tizimi
- [ ] SMS xabarnomalar
- [ ] Multi-til qo'llab-quvvatlash (O'zbek, Rus, Ingliz)

## 🤝 Hissa qo'shish

Pull requestlar qabul qilinadi! Katta o'zgarishlar uchun avval issue oching.

## 📄 Litsenziya

MIT License

## 📞 Aloqa

Savollar yoki takliflar bo'lsa, GitHub Issues orqali murojaat qiling.

---

**Made with ❤️ by Bahrom**

🔗 GitHub: https://github.com/bahrombekk715-dotcom/choy-plov-bot
