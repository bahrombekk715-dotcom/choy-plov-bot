"""Telegram orqali xabarnomalar ("SMS" o'rniga): mijozga va adminga.

Bot ham (bot.py), web server ham (webapp.py) shu funksiyalardan foydalanadi.
"""
import logging

from config import ADMIN_ID
from i18n import tr
from keyboards import order_action_keyboard

logger = logging.getLogger(__name__)

STATUS_KEY = {'completed': 'n_approved', 'cancelled': 'n_cancelled'}


def fmt_money(value):
    return f"{value:,.0f}".replace(',', ' ')


async def send_to_user(bot, db, user_id, key, **kw):
    """Mijozga uning tilida xabar yuboradi. Muvaffaqiyatli bo'lsa True."""
    lang = await db.get_language(user_id)
    try:
        await bot.send_message(user_id, tr(lang, key, **kw))
        return True
    except Exception as e:
        logger.warning("Could not notify user %s: %s", user_id, e)
        return False


async def notify_status_change(bot, db, order):
    key = STATUS_KEY.get(order['status'])
    if key:
        await send_to_user(bot, db, order['user_id'], key, id=order['id'])


async def format_admin_order(db, order, title="🔔 Buyurtma"):
    """Admin uchun buyurtma matni (admin interfeysi o'zbek tilida)."""
    user = await db.get_user(order['user_id'])
    unknown = "Noma'lum"
    text = f"{title} #{order['id']}\n\n"
    text += f"👤 Mijoz: {user['first_name'] if user else unknown}\n"
    if user and user['username']:
        text += f"🆔 @{user['username']}\n"
    text += f"📱 Telefon: {order['phone_number']}\n"
    text += f"📍 Manzil: {order['address']}\n"
    text += f"📅 Vaqt: {order['created_at']}\n\n📦 Mahsulotlar:\n"
    for item in await db.get_order_items(order['id']):
        text += f"• {item['product_name']} x{item['quantity']} - {item['price']:,.0f} so'm\n"
        for addon in await db.get_order_addons(item['id']):
            text += f"  + {addon['name']}\n"
    if order['comment']:
        text += f"\n💬 Izoh: {order['comment']}\n"
    text += f"\n💰 Jami: {order['total_price']:,.0f} so'm"
    return text


async def notify_new_order(bot, db, order_id):
    """Yangi buyurtma: mijozga tasdiq xabari + adminga tugmali xabar."""
    order = await db.get_order(order_id)
    if not order:
        return
    await send_to_user(bot, db, order['user_id'], 'n_created',
                       id=order_id, total=fmt_money(order['total_price']), address=order['address'])
    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID, await format_admin_order(db, order),
                reply_markup=order_action_keyboard(order_id))
        except Exception as e:
            logger.warning("Could not notify admin: %s", e)
