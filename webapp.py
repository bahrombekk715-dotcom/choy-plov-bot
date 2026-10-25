from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import asyncio
import io
from database import Database
from config import BOT_TOKEN
from aiogram import Bot

app = FastAPI()
db = Database()
telegram_bot = Bot(token=BOT_TOKEN)

# Static fayllar va templatelar
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.close()
    await telegram_bot.session.close()

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/categories")
async def get_categories():
    categories = await db.get_categories()
    return [dict(cat) for cat in categories]

@app.get("/api/products/{category_id}")
async def get_products(category_id: int):
    products = await db.get_products_by_category(category_id)
    return [dict(prod) for prod in products]

@app.get("/api/product/{product_id}")
async def get_product(product_id: int):
    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(product)

@app.get("/api/image/{file_id}")
async def get_image(file_id: str):
    """Telegram File ID orqali rasmni olish"""
    try:
        file = await telegram_bot.get_file(file_id)
        file_bytes = await telegram_bot.download_file(file.file_path)

        return StreamingResponse(
            io.BytesIO(file_bytes.read()),
            media_type="image/jpeg"
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Image not found: {str(e)}")

@app.post("/api/order")
async def create_order(request: Request):
    data = await request.json()

    # Telegram Web App dan kelgan ma'lumotlarni tekshirish
    init_data = data.get('initData')
    if not init_data:
        raise HTTPException(status_code=400, detail="Invalid request")

    # Buyurtmani yaratish
    user_id = data.get('user_id')
    phone = data.get('phone')
    address = data.get('address')
    cart = data.get('cart', [])
    comment = data.get('comment')

    if not all([user_id, phone, address, cart]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Umumiy summani hisoblash
    total = 0
    for item in cart:
        product = await db.get_product(item['product_id'])
        if product:
            item_total = product['price'] * item['quantity']

            # Qo'shimchalar narxini qo'shish
            if item.get('addons'):
                addon_prices = {'meat': 15000, 'egg': 5000, 'qazi': 20000}
                for addon in item['addons']:
                    item_total += addon_prices.get(addon, 0) * item['quantity']

            total += item_total

    # Buyurtmani saqlash
    order_id = await db.create_order(user_id, phone, address, total, comment)

    # Buyurtma mahsulotlarini saqlash
    for item in cart:
        product = await db.get_product(item['product_id'])
        if product:
            item_price = product['price'] * item['quantity']

            if item.get('addons'):
                addon_prices = {'meat': 15000, 'egg': 5000, 'qazi': 20000}
                for addon in item['addons']:
                    item_price += addon_prices.get(addon, 0) * item['quantity']

            order_item_id = await db.add_order_item(
                order_id,
                item['product_id'],
                item['quantity'],
                item_price
            )

            # Qo'shimchalarni saqlash
            if item.get('addons'):
                addon_id_map = {'meat': 1, 'egg': 2, 'qazi': 3}
                for addon in item['addons']:
                    if addon in addon_id_map:
                        await db.add_order_addon(order_item_id, addon_id_map[addon])

    return {"success": True, "order_id": order_id, "total": total}

@app.get("/api/orders/{user_id}")
async def get_user_orders(user_id: int):
    orders = await db.get_user_orders(user_id)
    result = []

    for order in orders:
        items = await db.get_order_items(order['id'])
        order_dict = dict(order)
        order_dict['items'] = [dict(item) for item in items]
        result.append(order_dict)

    return result

@app.get("/api/user/{user_id}")
async def get_user(user_id: int):
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
