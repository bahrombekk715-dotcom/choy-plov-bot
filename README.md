# 🍽 Choy Plov - Telegram Web App Bot

Telegram orqali ovqat buyurtma qilish boti - to'liq Web App integratsiyasi bilan.

## ✨ Xususiyatlar

### 👥 Foydalanuvchilar uchun (Web App):
- 🌙 Tungi tema (qora-ko'k), responsive dizayn, SVG ikonlar (Telegram stikerlarsiz)
- 🍽 Kategoriyalar va mahsulotlar, **galereya** (har mahsulotga 3-5 ta rasm, aylantirish va mini-rasmlar)
- 🛒 Savat (qo'shimchalar bilan), narxlar serverda qayta hisoblanadi
- ❤️ **Sevimli mahsulotlar**
- 📦 **Buyurtmalar tarixi**: holat va sana bo'yicha filtr, "Qayta buyurtma"
- 👤 **Profil**: statistika, til tanlash
- 📍 **Saqlangan manzillar**: qo'shish, tahrirlash, asosiyni belgilash, buyurtma paytida tanlash
- 🌐 **3 til**: O'zbekcha, Русский, English (bot va sayt)
- 🔔 Telegram orqali xabarnomalar ("SMS" o'rniga): buyurtma qabul qilindi, tasdiqlandi, bekor qilindi — mijozning o'z tilida

### 👨‍💼 Admin uchun:
- 🖥 **Web admin panel** (`/admin`): Dashboard (kunlik tushum/buyurtma grafigi, holatlar, eng ko'p sotilganlar),
  foydalanuvchilar ro'yxati, buyurtmalarni boshqarish (qidiruv, filtr, holatni o'zgartirish), mahsulot va kategoriya boshqaruvi, rasm yuklash
- 🤖 Bot orqali: yangi buyurtmalarni tasdiqlash/bekor qilish, mahsulot qo'shish, stop/start, bugungi statistika
- 🔑 Kirish: Telegram orqali (`ADMIN_ID`) yoki brauzerdan parol bilan (`ADMIN_PASSWORD`)
- 💵 Faqat naqd to'lov

> ⚠️ **Ma'lumotlar PostgreSQL da, rasmlar esa `data/uploads` papkada saqlanadi.** Render.com'da fayl tizimi har deployda tozalanadi:
> rasmlar yo'qolmasligi uchun Render **Disk** (Mount path: `/app/data`) ulang yoki Docker'da `./data` volume'dan foydalaning.
> Baza uchun Render PostgreSQL (yoki Neon/Supabase) oching va uning `DATABASE_URL` manzilini environment'ga qo'ying.

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
    │Database │ ← PostgreSQL
    └─────────┘
```

## 📁 Fayl strukturasi

```
choy-plov-bot/
├── main.py            # Bot va web serverni birga ishga tushirish
├── bot.py             # Telegram bot (3 til, admin buyurtma tugmalari)
├── webapp.py          # FastAPI: sayt, foydalanuvchi API, admin API, rasm yuklash
├── database.py        # PostgreSQL (asyncpg): sxema, so'rovlar, statistika
├── i18n.py            # Barcha matnlar: uz / ru / en (bot + sayt)
├── notify.py          # Telegram xabarnomalar (mijoz va admin)
├── auth.py            # Telegram initData tekshiruvi, admin tokenlari
├── migrate_sqlite_to_postgres.py  # eski bot.db dan PostgreSQL ga bir martalik ko'chirish
├── keyboards.py, config.py, requirements.txt, Dockerfile, docker-compose.yml, .env.example
├── data/              # uploads/ (rasmlar) — avtomatik yaratiladi
└── web/
    ├── templates/     # index.html (sayt), admin.html (admin panel)
    └── static/        # css/ (style, admin), js/ (common, app, admin), img/icons.svg
```

## 🐘 PostgreSQL

Baza sifatida PostgreSQL 13+ ishlatiladi. Jadvallar bot birinchi marta ishga tushganda o'zi yaratiladi.

- **Docker**: `docker-compose.yml` ichida `db` (postgres:16) xizmati bor. `.env` ga `POSTGRES_PASSWORD=...` yozing, `docker compose up -d --build` — boshqa sozlash shart emas.
- **Boshqa joyda** (lokal, Render, Neon, Supabase): bo'sh baza oching va `.env` ga `DATABASE_URL=postgresql://user:parol@host:5432/baza` yozing.
- **Vaqt zonasi**: "bugun" va kunlik grafiklar `TIMEZONE` (standart `Asia/Tashkent`) bo'yicha hisoblanadi.

### Eski SQLite (`data/bot.db`) dan ma'lumotlarni ko'chirish

```bash
docker compose stop bot                       # ko'chirish paytida yangi buyurtma kelmasin
docker compose up -d db
docker compose run --rm bot python migrate_sqlite_to_postgres.py data/bot.db
docker compose up -d bot
```

Skript har jadvaldagi qatorlar sonini ikkala bazada ko'rsatadi. SQLite fayl o'zgarmaydi, shuning uchun xohlasangiz orqaga qaytish mumkin.
Docker'siz: `python migrate_sqlite_to_postgres.py data/bot.db` (avval `DATABASE_URL` ni sozlang).

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
ADMIN_PASSWORD=ixtiyoriy_parol   # brauzerdan /admin ga kirish uchun
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
  - asyncpg - Async PostgreSQL driver
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
- [ ] Chegirmalar va promo kodlar
- [ ] Yetkazib beruvchi tizimi

## 🤝 Hissa qo'shish

Pull requestlar qabul qilinadi! Katta o'zgarishlar uchun avval issue oching.

## 📄 Litsenziya

MIT License

## 📞 Aloqa

Savollar yoki takliflar bo'lsa, GitHub Issues orqali murojaat qiling.

---

**Made with ❤️ by Bahrom**

🔗 GitHub: https://github.com/bahrombekk715-dotcom/choy-plov-bot


## 💬 Qo'llab-quvvatlash (chat)

- Mijoz: Profil → *Murojaat yozish*. Xabarlar bazadagi `support_messages` jadvaliga yoziladi.
- Admin: `/admin` → *Murojaatlar*. Har bir mijozning telefoni, buyurtmalari, manzillari ko'rinadi, javob shu yerdan yoziladi.
- Admin javob yozsa, mijozga Telegramdan ham xabar boradi. Mijoz yozsa, adminga Telegramda qisqa xabar keladi.
- Telegramga xabar yuborish fonda bajariladi, shuning uchun sayt va bot sekinlashmaydi.
