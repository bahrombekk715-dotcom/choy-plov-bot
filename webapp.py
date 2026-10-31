import asyncio
import hashlib
import io
import logging
import time
import os
import re
import uuid
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

import auth
import notify
from config import ADMIN_ID, ADMIN_PASSWORD, BOT_TOKEN, DEV_MODE, SUPPORT_PHONE, SUPPORT_USERNAME, UPLOAD_DIR
from database import MAX_IMAGES, Database
from i18n import LANGS, norm_lang, web_dict

logger = logging.getLogger(__name__)
db = Database()
telegram_bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
_bg_tasks = set()


def bg(coro):
    """Telegramga xabar yuborish kabi sekin ishlar so'rovni kutdirmaydi: javob darhol qaytadi, xabar fonda ketadi."""
    task = asyncio.create_task(coro)
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app):
    await db.connect()
    yield
    await db.close()
    if telegram_bot:
        await telegram_bot.session.close()


class CachedStatic(StaticFiles):
    """Brauzer keshi: ko'p foydalanuvchida server yukini kamaytiradi."""
    def __init__(self, *a, max_age=600, **kw):
        super().__init__(*a, **kw)
        self.max_age = max_age

    async def get_response(self, path, scope):
        resp = await super().get_response(path, scope)
        if resp.status_code == 200:
            resp.headers['Cache-Control'] = f'public, max-age={self.max_age}'
        return resp


app = FastAPI(lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=700)          # JSON/JS/CSS siqiladi
app.mount("/static", CachedStatic(directory="web/static", max_age=600), name="static")
app.mount("/uploads", CachedStatic(directory=UPLOAD_DIR, max_age=31536000), name="uploads")   # fayl nomlari noyob (uuid)
templates = Jinja2Templates(directory="web/templates")

ORDER_STATUSES = ('pending', 'completed', 'delivered', 'cancelled')
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
UPLOAD_LIMIT = 5 * 1024 * 1024
IMAGE_MAGIC = {b'\xff\xd8\xff': '.jpg', b'\x89PNG\r\n\x1a\n': '.png'}


# ================================================================ autentifikatsiya
def current_tg_user(request: Request):
    """Telegram initData (yoki lokal DEV_MODE) orqali foydalanuvchi ma'lumotlari: {id, first_name, username, language_code}."""
    user = auth.validate_init_data(request.headers.get('X-Init-Data', ''))
    if user:
        return user
    dev = request.headers.get('X-Dev-User')
    if DEV_MODE and dev and dev.isdigit():
        return {'id': int(dev), 'first_name': 'Dev', 'username': None, 'language_code': 'uz'}
    return None


def current_user_id(request: Request, required=True):
    user = current_tg_user(request)
    if user:
        return user['id']
    if required:
        raise HTTPException(401, 'telegram_required')
    return None


async def ensure_user(tg_user):
    """Telefon so'ralmaydi: Telegram ma'lumotlari bilan avtomatik ro'yxatdan o'tadi."""
    return await db.ensure_user(tg_user['id'], tg_user.get('username'), tg_user.get('first_name'),
                                norm_lang(tg_user.get('language_code')))


def user_id_dep(request: Request):
    return current_user_id(request)


def admin_dep(request: Request):
    token = request.headers.get('X-Admin-Token')
    if token and auth.verify_admin_token(token):
        return True
    uid = current_user_id(request, required=False)
    if uid is None:
        raise HTTPException(401, 'login_required')
    if ADMIN_ID and uid == ADMIN_ID:
        return True
    raise HTTPException(403, 'not_admin')


async def registered_user(request: Request):
    tg_user = current_tg_user(request)
    if not tg_user:
        raise HTTPException(401, 'telegram_required')
    return await ensure_user(tg_user)


# ================================================================ sahifalar
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/admin")
async def admin_page(request: Request):
    return templates.TemplateResponse(request, "admin.html")


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/api/i18n/{lang}")
async def i18n(lang: str):
    return JSONResponse(web_dict(norm_lang(lang)), headers={'Cache-Control': 'public, max-age=300'})


# ================================================================ menyu (ochiq)
MENU_TTL = 10          # soniya. Bot (boshqa jarayon) o'zgartirsa ham 10 soniyada yangilanadi
_menu = {'at': 0.0, 'data': None}


def invalidate_menu():
    _menu['at'] = 0.0


async def base_menu():
    """Hamma uchun bir xil menyu: bazaga har so'rovda emas, 10 soniyada bir marta murojaat qilinadi."""
    if _menu['data'] is None or time.monotonic() - _menu['at'] > MENU_TTL:
        categories = [dict(c) for c in await db.get_categories()]
        active = {c['id'] for c in categories}
        products = [p for p in await db.attach_images(await db.get_all_products()) if p['category_id'] in active]
        await db.attach_addon_ids(products)
        _menu['data'] = {'categories': categories, 'products': products,
                         'addons': [dict(a) for a in await db.get_addons(available_only=False)]}   # o'chirilganlari "mavjud emas" deb ko'rsatiladi
        _menu['at'] = time.monotonic()
    return _menu['data']


@app.get("/api/menu")
async def menu(request: Request):
    """Kategoriyalar, mahsulotlar (galereya bilan), qo'shimchalar va sevimlilar — bitta so'rovda."""
    uid = current_user_id(request, required=False)
    return {**await base_menu(), 'favorites': await db.get_favorite_ids(uid) if uid else []}


@app.get("/api/image/{file_id}")
async def get_image(file_id: str):
    """Telegram file_id orqali rasm (eski mahsulotlar). Bir marta yuklab diskka saqlanadi — keyin Telegramga bormaydi."""
    if not re.fullmatch(r'[\w-]{10,200}', file_id):
        raise HTTPException(404, "Image not found")
    path = os.path.join(UPLOAD_DIR, 'tg_' + hashlib.sha1(file_id.encode()).hexdigest() + '.jpg')
    if not os.path.exists(path):
        if not telegram_bot:
            raise HTTPException(404, "Image not found")
        try:
            file = await telegram_bot.get_file(file_id)
            data = await telegram_bot.download_file(file.file_path)
            with open(path, 'wb') as f:
                f.write(data.read())
        except Exception:
            raise HTTPException(404, "Image not found")
    return FileResponse(path, media_type="image/jpeg", headers={'Cache-Control': 'public, max-age=86400'})


# ================================================================ foydalanuvchi
@app.get("/api/me")
async def me(request: Request):
    tg_user = current_tg_user(request)
    if tg_user is None:
        return {'telegram': False}
    user = await ensure_user(tg_user)
    is_admin = bool(ADMIN_ID and tg_user['id'] == ADMIN_ID)
    return {'telegram': True, 'registered': True, 'is_admin': is_admin, **dict(user),
            'stats': await db.get_user_stats(tg_user['id']),
            'support': {'username': SUPPORT_USERNAME, 'phone': SUPPORT_PHONE},
            'support_unread': await db.support_user_unread(tg_user['id'])}


class PhoneIn(BaseModel):
    phone: str = Field(min_length=5, max_length=30)


@app.post("/api/me/phone")
async def set_my_phone(body: PhoneIn, user=Depends(registered_user)):
    """Profildagi (saqlangan) telefon raqamni o'zgartirish."""
    await db.set_phone(user['user_id'], body.phone.strip())
    return {'phone': body.phone.strip()}


class LocationIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    address: str | None = Field(default=None, max_length=300)


@app.post("/api/me/location")
async def set_my_location(body: LocationIn, user=Depends(registered_user)):
    """Sayt har ochilganda brauzerdan kelgan lokatsiyani profilga yozadi (manzil ko'rsatish uchun)."""
    address = (body.address or '').strip() or None
    await db.set_location(user['user_id'], body.lat, body.lon, address)
    return {'lat': body.lat, 'lon': body.lon, 'location_address': address}


class LangIn(BaseModel):
    language: str


@app.post("/api/me/language")
async def set_language(body: LangIn, user=Depends(registered_user)):
    if body.language not in LANGS:
        raise HTTPException(400, 'bad_language')
    await db.set_language(user['user_id'], body.language)
    return {'language': body.language}


# ---- sevimlilar
@app.get("/api/favorites")
async def favorites(user=Depends(registered_user)):
    items = await db.attach_images(await db.get_favorites(user['user_id']))
    return items


@app.post("/api/favorites/{product_id}/toggle")
async def toggle_favorite(product_id: int, user=Depends(registered_user)):
    if not await db.get_product(product_id):
        raise HTTPException(404, 'not_found')
    return {'favorite': await db.toggle_favorite(user['user_id'], product_id)}


# ---- manzillar
class AddressIn(BaseModel):
    title: str = Field(min_length=1, max_length=40)
    address: str = Field(min_length=3, max_length=300)
    is_default: bool = False
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)


def _coords(body):
    """Lokatsiya faqat ikkala koordinata ham bo'lsa saqlanadi."""
    return (body.lat, body.lon) if body.lat is not None and body.lon is not None else (None, None)


@app.get("/api/addresses")
async def addresses(user=Depends(registered_user)):
    return [dict(a) for a in await db.get_addresses(user['user_id'])]


@app.post("/api/addresses")
async def add_address(body: AddressIn, user=Depends(registered_user)):
    lat, lon = _coords(body)
    aid = await db.save_address(user['user_id'], body.title.strip(), body.address.strip(), body.is_default, lat=lat, lon=lon)
    return {'id': aid}


@app.put("/api/addresses/{address_id}")
async def edit_address(address_id: int, body: AddressIn, user=Depends(registered_user)):
    if not await db.get_address(address_id, user['user_id']):
        raise HTTPException(404, 'not_found')
    lat, lon = _coords(body)
    await db.save_address(user['user_id'], body.title.strip(), body.address.strip(), body.is_default, address_id, lat, lon)
    return {'id': address_id}


@app.post("/api/addresses/{address_id}/default")
async def default_address(address_id: int, user=Depends(registered_user)):
    if not await db.get_address(address_id, user['user_id']):
        raise HTTPException(404, 'not_found')
    await db.make_default_address(address_id, user['user_id'])
    return {'ok': True}


@app.delete("/api/addresses/{address_id}")
async def remove_address(address_id: int, user=Depends(registered_user)):
    await db.delete_address(address_id, user['user_id'])
    return {'ok': True}


# ---- buyurtmalar
class AddonIn(BaseModel):
    id: int
    qty: int = Field(default=1, ge=1, le=20)


class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=50)
    addons: list[AddonIn] = Field(default=[], max_length=10)


class OrderIn(BaseModel):
    phone: str = Field(min_length=5, max_length=30)
    address: str = Field(default='', max_length=300)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    comment: str | None = Field(default=None, max_length=500)
    cart: list[CartItem] = Field(min_length=1, max_length=50)


@app.post("/api/order")
async def create_order(body: OrderIn, user=Depends(registered_user)):
    has_loc = body.lat is not None and body.lon is not None
    address = body.address.strip()
    if len(address) < 3 and not has_loc:
        raise HTTPException(400, 'bad_address')
    phone, addr_text = body.phone.strip(), address or "Lokatsiya yuborildi"
    try:
        _lines, calc_total = await db._price_cart([c.model_dump() for c in body.cart])
        dup = await db.find_recent_duplicate_order(user['user_id'], phone, addr_text, calc_total)
        if dup:
            return {"success": True, "order_id": dup, "total": calc_total}
    except ValueError as e:
        raise HTTPException(400, str(e))
    try:
        order_id, total = await db.create_order_from_cart(
            user['user_id'], body.phone.strip(), address or "Lokatsiya yuborildi",
            (body.comment or '').strip() or None, [c.model_dump() for c in body.cart],
            body.lat if has_loc else None, body.lon if has_loc else None)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not user['phone_number']:                                  # birinchi raqam profilga saqlanadi; boshqa raqam faqat shu buyurtma uchun
        await db.set_phone(user['user_id'], body.phone.strip())
    if telegram_bot:
        bg(notify.notify_new_order(telegram_bot, db, order_id))
    return {"success": True, "order_id": order_id, "total": total}


@app.get("/api/orders")
async def my_orders(status: str | None = None, date_from: str | None = None, date_to: str | None = None,
                    user=Depends(registered_user)):
    if status and status not in ORDER_STATUSES:
        raise HTTPException(400, 'bad_status')
    for d in (date_from, date_to):
        if d and not DATE_RE.match(d):
            raise HTTPException(400, 'bad_date')
    orders = await db.get_user_orders(user['user_id'], status or None, date_from or None, date_to or None)
    return [await db.order_with_items(o) for o in orders]


@app.post("/api/orders/{order_id}/cancel")
async def cancel_my_order(order_id: int, user=Depends(registered_user)):
    """Mijoz tasdiqlanmagan buyurtmasini bekor qiladi."""
    if not await db.cancel_user_order(order_id, user['user_id']):
        raise HTTPException(400, 'not_pending')
    if telegram_bot:
        async def _after_cancel():
            order = await db.get_order(order_id)
            await notify.refresh_admin_message(telegram_bot, db, order)
            await notify.notify_admin_text(telegram_bot, f"❌ Mijoz buyurtma #{order_id} ni bekor qildi.")
        bg(_after_cancel())
    return {'ok': True}


# ---- qo'llab-quvvatlash (mijoz <-> admin chat)
class SupportIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


@app.get("/api/support")
async def support_messages(after: int = 0, user=Depends(registered_user)):
    return {'messages': await db.support_user_messages(user['user_id'], max(after, 0))}


@app.get("/api/support/unread")
async def support_unread(user=Depends(registered_user)):
    return {'count': await db.support_user_unread(user['user_id'])}


@app.post("/api/support")
async def support_send(body: SupportIn, user=Depends(registered_user)):
    text = body.text.strip()
    if not text:
        raise HTTPException(400, 'empty')
    if await db.support_recent_user_count(user['user_id']) >= 20:
        raise HTTPException(429, 'too_many')
    msg = await db.support_add(user['user_id'], 'user', text)
    return msg


# ================================================================ admin API
class LoginIn(BaseModel):
    password: str


@app.post("/api/admin/login")
async def admin_login(body: LoginIn):
    import hmac
    if not ADMIN_PASSWORD or not hmac.compare_digest(body.password.encode(), ADMIN_PASSWORD.encode()):
        raise HTTPException(401, 'bad_password')
    return {'token': auth.make_admin_token()}


@app.get("/api/admin/session")
async def admin_session(_=Depends(admin_dep)):
    return {'ok': True}


@app.get("/api/admin/stats")
async def admin_stats(days: int = 14, _=Depends(admin_dep)):
    return await db.admin_stats(days)


@app.get("/api/admin/orders")
async def admin_orders(page: int = 1, status: str | None = None, search: str | None = None, _=Depends(admin_dep)):
    if status and status not in ORDER_STATUSES:
        raise HTTPException(400, 'bad_status')
    return await db.admin_orders(status, (search or '').strip() or None, page)


class OrderItemsIn(BaseModel):
    cart: list[CartItem] = Field(min_length=1, max_length=50)


@app.put("/api/admin/orders/{order_id}/items")
async def admin_edit_order_items(order_id: int, body: OrderItemsIn, _=Depends(admin_dep)):
    """Tasdiqlashdan oldin buyurtmaga mahsulot qo'shish/olib tashlash/sonini o'zgartirish."""
    try:
        total = await db.replace_order_items(order_id, [c.model_dump() for c in body.cart])
    except ValueError as e:
        raise HTTPException(400, str(e))
    if telegram_bot:
        order = await db.get_order(order_id)

        async def _after_edit():
            await notify.send_to_user(telegram_bot, db, order['user_id'], 'n_edited', id=order_id, total=notify.fmt_money(total))
            await notify.refresh_admin_message(telegram_bot, db, order)
        bg(_after_edit())
    return {'ok': True, 'total': total}


class StatusIn(BaseModel):
    status: str


@app.post("/api/admin/orders/{order_id}/status")
async def admin_set_status(order_id: int, body: StatusIn, _=Depends(admin_dep)):
    if body.status not in ORDER_STATUSES:
        raise HTTPException(400, 'bad_status')
    order = await db.get_order(order_id)
    if not order:
        raise HTTPException(404, 'not_found')
    changed = order['status'] != body.status
    await db.update_order_status(order_id, body.status)
    if changed and telegram_bot:
        order = await db.get_order(order_id)
        async def _after_status():
            await notify.notify_status_change(telegram_bot, db, order)          # mijozga xabar
            await notify.refresh_admin_message(telegram_bot, db, order)         # adminning bot chatidagi xabar ham yangilanadi
        bg(_after_status())
    return {'ok': True}


# ---- admin: qo'llab-quvvatlash
@app.get("/api/admin/support/unread")
async def admin_support_unread(_=Depends(admin_dep)):
    return {'count': await db.support_admin_unread_total()}


@app.get("/api/admin/support")
async def admin_support_threads(page: int = 1, search: str = '', unread: int = 0, _=Depends(admin_dep)):
    r = await db.support_threads(search.strip() or None, bool(unread), page)
    return {**r, 'unread_total': await db.support_admin_unread_total()}


@app.get("/api/admin/support/{user_id}")
async def admin_support_thread(user_id: int, after: int = 0, _=Depends(admin_dep)):
    messages = await db.support_thread(user_id, max(after, 0))
    out = {'messages': messages}
    if after <= 0:                      # mijoz kartochkasi faqat suhbat ochilganda kerak
        card = await db.support_user_card(user_id)
        if not card:
            raise HTTPException(404, 'not_found')
        out['user'] = card
    return out


@app.post("/api/admin/support/{user_id}")
async def admin_support_reply(user_id: int, body: SupportIn, _=Depends(admin_dep)):
    text = body.text.strip()
    if not text:
        raise HTTPException(400, 'empty')
    if not await db.get_user(user_id):
        raise HTTPException(404, 'not_found')
    msg = await db.support_add(user_id, 'admin', text)
    return msg


@app.get("/api/admin/users")
async def admin_users(page: int = 1, search: str = '', _=Depends(admin_dep)):
    return await db.admin_users(search.strip() or None, page)


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)


@app.get("/api/admin/categories")
async def admin_categories(_=Depends(admin_dep)):
    return [dict(c) for c in await db.get_categories_with_counts()]


@app.post("/api/admin/categories")
async def admin_add_category(body: CategoryIn, _=Depends(admin_dep)):
    invalidate_menu()
    return {'id': await db.add_category(body.name.strip())}


@app.put("/api/admin/categories/{cid}")
async def admin_rename_category(cid: int, body: CategoryIn, _=Depends(admin_dep)):
    invalidate_menu()
    await db.update_category(cid, body.name.strip())
    return {'ok': True}


@app.delete("/api/admin/categories/{cid}")
async def admin_delete_category(cid: int, _=Depends(admin_dep)):
    invalidate_menu()
    await db.delete_category(cid)
    return {'ok': True}


class AddonAdminIn(BaseModel):
    product_ids: list[int] = []          # qaysi mahsulotlarga qo'shiladi
    name: str = Field(min_length=1, max_length=60)
    unit: str | None = Field(default=None, max_length=20)
    price: float = Field(ge=0, lt=100_000_000)


@app.get("/api/admin/addons")
async def admin_addons(_=Depends(admin_dep)):
    out = []
    for a in await db.get_addons(available_only=False):
        out.append({**dict(a), 'product_ids': await db.get_addon_product_ids(a['id'])})
    return out


@app.post("/api/admin/addons/{aid}/toggle")
async def admin_toggle_addon(aid: int, _=Depends(admin_dep)):
    invalidate_menu()
    return {'is_available': await db.toggle_addon_availability(aid)}


@app.post("/api/admin/addons")
async def admin_add_addon(body: AddonAdminIn, _=Depends(admin_dep)):
    invalidate_menu()
    aid = await db.add_addon(body.name.strip(), body.price, (body.unit or '').strip() or None)
    await db.set_addon_products(aid, body.product_ids)
    return {'id': aid}


@app.put("/api/admin/addons/{aid}")
async def admin_edit_addon(aid: int, body: AddonAdminIn, _=Depends(admin_dep)):
    invalidate_menu()
    await db.update_addon(aid, body.name.strip(), body.price, (body.unit or '').strip() or None)
    await db.set_addon_products(aid, body.product_ids)
    return {'ok': True}


@app.delete("/api/admin/addons/{aid}")
async def admin_delete_addon(aid: int, _=Depends(admin_dep)):
    invalidate_menu()
    await db.delete_addon(aid)
    return {'ok': True}


class ProductIn(BaseModel):
    addon_ids: list[int] = []            # shu mahsulotga qo'shiladigan qo'shimchalar
    category_id: int
    name: str = Field(min_length=1, max_length=120)
    price: float = Field(gt=0, lt=100_000_000)
    description: str | None = Field(default=None, max_length=1000)


@app.get("/api/admin/products")
async def admin_products(_=Depends(admin_dep)):
    products = await db.attach_images(await db.get_all_products())
    return await db.attach_addon_ids(products)


async def _check_category(cid):
    if not await db.get_category(cid):
        raise HTTPException(400, 'bad_category')


@app.post("/api/admin/products")
async def admin_add_product(body: ProductIn, _=Depends(admin_dep)):
    invalidate_menu()
    await _check_category(body.category_id)
    pid = await db.add_product(body.category_id, body.name.strip(), body.price, body.description)
    await db.set_product_addons(pid, body.addon_ids)
    return {'id': pid}


@app.put("/api/admin/products/{pid}")
async def admin_edit_product(pid: int, body: ProductIn, _=Depends(admin_dep)):
    invalidate_menu()
    if not await db.get_product(pid):
        raise HTTPException(404, 'not_found')
    await _check_category(body.category_id)
    await db.update_product(pid, body.name.strip(), body.price, body.description, body.category_id)
    await db.set_product_addons(pid, body.addon_ids)
    return {'ok': True}


@app.post("/api/admin/products/{pid}/toggle")
async def admin_toggle_product(pid: int, _=Depends(admin_dep)):
    invalidate_menu()
    if not await db.get_product(pid):
        raise HTTPException(404, 'not_found')
    await db.toggle_product_availability(pid)
    return {'is_available': bool((await db.get_product(pid))['is_available'])}


@app.delete("/api/admin/products/{pid}")
async def admin_delete_product(pid: int, _=Depends(admin_dep)):
    invalidate_menu()
    await db.delete_product(pid)
    return {'ok': True}


@app.post("/api/admin/products/{pid}/images")
async def admin_upload_image(pid: int, file: UploadFile = File(...), _=Depends(admin_dep)):
    invalidate_menu()
    if not await db.get_product(pid):
        raise HTTPException(404, 'not_found')
    if await db.count_product_images(pid) >= MAX_IMAGES:
        raise HTTPException(400, f'Maksimum {MAX_IMAGES} ta rasm')
    data = await file.read(UPLOAD_LIMIT + 1)
    if len(data) > UPLOAD_LIMIT:
        raise HTTPException(400, 'Rasm 5MB dan katta')
    ext = next((e for magic, e in IMAGE_MAGIC.items() if data.startswith(magic)), None)
    if not ext and data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        ext = '.webp'
    if not ext:                      # kengaytma emas, fayl mazmuni tekshiriladi
        raise HTTPException(400, 'Faqat JPG, PNG yoki WEBP')
    name = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, name), 'wb') as f:
        f.write(data)
    image_id = await db.add_product_image(pid, f"/uploads/{name}")
    return {'id': image_id, 'url': f"/uploads/{name}"}


@app.delete("/api/admin/images/{image_id}")
async def admin_delete_image(image_id: int, _=Depends(admin_dep)):
    invalidate_menu()
    img = await db.get_image(image_id)
    if not img:
        raise HTTPException(404, 'not_found')
    await db.delete_image(image_id)
    if img['url'].startswith('/uploads/'):
        try:
            os.remove(os.path.join(UPLOAD_DIR, os.path.basename(img['url'])))
        except OSError:
            pass
    return {'ok': True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv('PORT', 8000)))
