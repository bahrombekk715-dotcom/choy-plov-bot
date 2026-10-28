"""Telegram orqali xabarnomalar ("SMS" o'rniga): mijozga va adminga.

Bot ham (bot.py), web server ham (webapp.py) shu funksiyalardan foydalanadi.
"""
import logging

from config import ADMIN_ID
from i18n import tr
from keyboards import order_keyboard

logger = logging.getLogger(__name__)

STATUS_KEY = {'completed': 'n_approved', 'delivered': 'n_delivered', 'cancelled': 'n_cancelled'}
STATUS_UZ = {'pending': 'Kutilmoqda', 'completed': 'Tasdiqlandi', 'delivered': 'Yetkazib berildi', 'cancelled': 'Bekor qilindi'}


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


async def notify_admin_text(bot, text):
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, text)
        except Exception as e:
            logger.warning("Could not notify admin: %s", e)


def map_link(order):
    """Yandex Maps havolasi: lokatsiya bo'lsa nuqta, bo'lmasa manzil matni bo'yicha qidiruv."""
    from urllib.parse import quote
    if order['lat'] is not None and order['lon'] is not None:
        return f"https://yandex.com/maps/?pt={order['lon']},{order['lat']}&z=17&l=map"
    return f"https://yandex.com/maps/?text={quote(order['address'] or '')}"


STATUS_MARK = {'pending': '⏳', 'completed': '✅', 'delivered': '🚚', 'cancelled': '❌'}


async def format_admin_order(db, order, title="🔔 Yangi buyurtma"):
    """Admin uchun buyurtma matni (admin interfeysi o'zbek tilida)."""
    user = await db.get_user(order['user_id'])
    text = f"{title} #{order['id']}\n\n"
    text += f"👤 Mijoz: {user['first_name'] if user and user['first_name'] else 'Noma`lum'}\n"
    if user and user['username']:
        text += f"🆔 @{user['username']}\n"
    text += f"📱 Telefon: {order['phone_number']}\n"
    text += f"📍 Manzil: {order['address']}\n"
    text += f"🗺 Yandex xarita: {map_link(order)}\n"
    text += f"📅 Vaqt: {order['created_at']}\n\n🍽 Buyurtma:\n"
    for item in await db.get_order_items(order['id']):
        text += f"• {item['product_name']} x{item['quantity']} — {item['price']:,.0f} so'm\n"
        for addon in await db.get_order_addons(item['id']):
            text += f"   ➕ {addon['name']} {addon['unit'] or ''} x{addon['qty']}\n"
    if order['comment']:
        text += f"\n💬 Izoh: {order['comment']}\n"
    text += f"\n💰 Jami: {order['total_price']:,.0f} so'm"
    if order['status'] != 'pending':
        text += f"\n\n{STATUS_MARK.get(order['status'], '')} Holat: {STATUS_UZ.get(order['status'], order['status'])}"
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
            msg = await bot.send_message(
                ADMIN_ID, await format_admin_order(db, order),
                reply_markup=order_keyboard(order_id))
            await db.set_admin_msg(order_id, msg.message_id)
        except Exception as e:
            logger.warning("Could not notify admin: %s", e)


async def refresh_admin_message(bot, db, order, message_id=None):
    """Holat qayerdan o'zgargan bo'lishidan qat'i nazar (sayt yoki bot), adminning bot chatidagi
    buyurtma xabari yangi holat va mos tugma bilan yangilanadi."""
    message_id = message_id or order['admin_msg_id']
    if not (ADMIN_ID and message_id):
        return
    try:
        await bot.edit_message_text(
            await format_admin_order(db, order), chat_id=ADMIN_ID, message_id=message_id,
            reply_markup=order_keyboard(order['id'], order['status']))
    except Exception as e:      # "message is not modified" va h.k. — jiddiy emas
        logger.info("Admin message not refreshed: %s", e)
