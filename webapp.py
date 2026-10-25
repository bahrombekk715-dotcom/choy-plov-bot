import io
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Bot
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

import auth
import notify
from config import ADMIN_ID, ADMIN_PASSWORD, BOT_TOKEN, DEV_MODE, UPLOAD_DIR
from database import MAX_IMAGES, Database
from i18n import LANGS, norm_lang, web_dict

logger = logging.getLogger(__name__)
db = Database()
telegram_bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app):
    await db.connect()
    yield
    await db.close()
    if telegram_bot:
        await telegram_bot.session.close()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="web/static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory="web/templates")

ORDER_STATUSES = ('pending', 'completed', 'cancelled')
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
UPLOAD_LIMIT = 5 * 1024 * 1024
IMAGE_MAGIC = {b'\xff\xd8\xff': '.jpg', b'\x89PNG\r\n\x1a\n': '.png'}


# ================================================================ autentifikatsiya
def current_user_id(request: Request, required=True):
    """Telegram initData (yoki lokal DEV_MODE) orqali foydalanuvchi ID sini aniqlaydi."""
    user = auth.validate_init_data(request.headers.get('X-Init-Data', ''))
    if user:
        return user['id']
    dev = request.headers.get('X-Dev-User')
    if DEV_MODE and dev and dev.isdigit():
        return int(dev)
    if required:
        raise HTTPException(401, 'telegram_required')
    return None


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


async def registered_user(uid: int = Depends(user_id_dep)):
    user = await db.get_user(uid)
    if not user:
        raise HTTPException(403, 'not_registered')
    return user


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
    return web_dict(norm_lang(lang))


# ================================================================ menyu (ochiq)
@app.get("/api/menu")
async def menu(request: Request):
    """Kategoriyalar, mavjud mahsulotlar (galereya bilan), qo'shimchalar va sevimlilar — bitta so'rovda."""
    categories = [dict(c) for c in await db.get_categories()]
    products = await db.attach_images(await db.get_all_products())
    active = {c['id'] for c in categories}
    products = [p for p in products if p['category_id'] in active]
    uid = current_user_id(request, required=False)
    return {
        'categories': categories,
        'products': products,
        'addons': [dict(a) for a in await db.get_addons()],
        'favorites': await db.get_favorite_ids(uid) if uid else [],
    }


@app.get("/api/image/{file_id}")
async def get_image(file_id: str):
    """Telegram file_id orqali rasm (eski mahsulotlar uchun)."""
    if not telegram_bot:
        raise HTTPException(404, "Image not found")
    try:
        file = await telegram_bot.get_file(file_id)
        data = await telegram_bot.download_file(file.file_path)
        return StreamingResponse(io.BytesIO(data.read()), media_type="image/jpeg",
                                 headers={'Cache-Control': 'public, max-age=86400'})
    except Exception:
        raise HTTPException(404, "Image not found")


# ================================================================ foydalanuvchi
@app.get("/api/me")
async def me(request: Request):
    uid = current_user_id(request, required=False)
    if uid is None:
        return {'telegram': False}
    user = await db.get_user(uid)
    is_admin = bool(ADMIN_ID and uid == ADMIN_ID)
    if not user:
        return {'telegram': True, 'registered': False, 'is_admin': is_admin, 'user_id': uid}
    return {'telegram': True, 'registered': True, 'is_admin': is_admin, **dict(user),
            'stats': await db.get_user_stats(uid)}


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


@app.get("/api/addresses")
async def addresses(user=Depends(registered_user)):
    return [dict(a) for a in await db.get_addresses(user['user_id'])]


@app.post("/api/addresses")
async def add_address(body: AddressIn, user=Depends(registered_user)):
    aid = await db.save_address(user['user_id'], body.title.strip(), body.address.strip(), body.is_default)
    return {'id': aid}


@app.put("/api/addresses/{address_id}")
async def edit_address(address_id: int, body: AddressIn, user=Depends(registered_user)):
    if not await db.get_address(address_id, user['user_id']):
        raise HTTPException(404, 'not_found')
    await db.save_address(user['user_id'], body.title.strip(), body.address.strip(), body.is_default, address_id)
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
class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=50)
    addons: list[int] = []


class OrderIn(BaseModel):
    phone: str = Field(min_length=5, max_length=30)
    address: str = Field(min_length=3, max_length=300)
    comment: str | None = Field(default=None, max_length=500)
    cart: list[CartItem] = Field(min_length=1, max_length=50)


@app.post("/api/order")
async def create_order(body: OrderIn, user=Depends(registered_user)):
    try:
        order_id, total = await db.create_order_from_cart(
            user['user_id'], body.phone.strip(), body.address.strip(),
            (body.comment or '').strip() or None, [c.model_dump() for c in body.cart])
    except ValueError as e:
        raise HTTPException(400, str(e))
    if telegram_bot:
        await notify.notify_new_order(telegram_bot, db, order_id)
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
        await notify.notify_status_change(telegram_bot, db, await db.get_order(order_id))
    return {'ok': True}


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
    return {'id': await db.add_category(body.name.strip())}


@app.put("/api/admin/categories/{cid}")
async def admin_rename_category(cid: int, body: CategoryIn, _=Depends(admin_dep)):
    await db.update_category(cid, body.name.strip())
    return {'ok': True}


@app.delete("/api/admin/categories/{cid}")
async def admin_delete_category(cid: int, _=Depends(admin_dep)):
    await db.delete_category(cid)
    return {'ok': True}


class ProductIn(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=120)
    price: float = Field(gt=0, lt=100_000_000)
    description: str | None = Field(default=None, max_length=1000)


@app.get("/api/admin/products")
async def admin_products(_=Depends(admin_dep)):
    return await db.attach_images(await db.get_all_products())


async def _check_category(cid):
    if not await db.get_category(cid):
        raise HTTPException(400, 'bad_category')


@app.post("/api/admin/products")
async def admin_add_product(body: ProductIn, _=Depends(admin_dep)):
    await _check_category(body.category_id)
    return {'id': await db.add_product(body.category_id, body.name.strip(), body.price, body.description)}


@app.put("/api/admin/products/{pid}")
async def admin_edit_product(pid: int, body: ProductIn, _=Depends(admin_dep)):
    if not await db.get_product(pid):
        raise HTTPException(404, 'not_found')
    await _check_category(body.category_id)
    await db.update_product(pid, body.name.strip(), body.price, body.description, body.category_id)
    return {'ok': True}


@app.post("/api/admin/products/{pid}/toggle")
async def admin_toggle_product(pid: int, _=Depends(admin_dep)):
    if not await db.get_product(pid):
        raise HTTPException(404, 'not_found')
    await db.toggle_product_availability(pid)
    return {'is_available': bool((await db.get_product(pid))['is_available'])}


@app.delete("/api/admin/products/{pid}")
async def admin_delete_product(pid: int, _=Depends(admin_dep)):
    await db.delete_product(pid)
    return {'ok': True}


@app.post("/api/admin/products/{pid}/images")
async def admin_upload_image(pid: int, file: UploadFile = File(...), _=Depends(admin_dep)):
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
