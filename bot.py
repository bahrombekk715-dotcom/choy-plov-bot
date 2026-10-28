import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, MenuButtonWebApp, Message, ReplyKeyboardRemove, WebAppInfo

import notify
from config import ADMIN_ID, BOT_TOKEN, WEB_APP_URL
from database import Database
from i18n import norm_lang, tr
from keyboards import order_keyboard, webapp_keyboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

ADMIN_URL = f"{WEB_APP_URL}/admin"


async def set_menu_button(chat_id, lang='uz', admin=False):
    """Chat pastidagi menyu tugmasi: adminda "Admin panel", foydalanuvchida "Menyu"."""
    try:
        if admin:
            btn = MenuButtonWebApp(text="Admin panel", web_app=WebAppInfo(url=ADMIN_URL))
        else:
            btn = MenuButtonWebApp(text=tr(lang, 'btn_menu'), web_app=WebAppInfo(url=WEB_APP_URL))
        await bot.set_chat_menu_button(chat_id=chat_id, menu_button=btn)
    except Exception as e:
        logger.warning("Menu button not set for %s: %s", chat_id, e)


async def clear_old_keyboard(message: Message):
    """Eski versiyadagi pastki tugmalar (Menyu, Profil...) qolib ketgan bo'lsa olib tashlaydi."""
    try:
        m = await message.answer(".", reply_markup=ReplyKeyboardRemove())
        await m.delete()
    except Exception:
        pass


async def open_site(message: Message):
    """Botda boshqa hech narsa yo'q: hamma narsa saytda."""
    uid = message.from_user.id
    is_admin = uid == ADMIN_ID
    is_new = not await db.get_user(uid)
    await db.add_user(uid, '', message.from_user.username, message.from_user.first_name,
                      norm_lang(message.from_user.language_code) if is_new else None)
    lang = await db.get_language(uid)
    await set_menu_button(uid, lang, admin=is_admin)
    await clear_old_keyboard(message)
    if is_admin:
        await message.answer("👨‍💼 Assalomu alaykum, Admin!\n\n🔔 Yangi buyurtmalar shu chatga keladi.\n🖥 Admin panel pastdagi tugmada.",
                             reply_markup=webapp_keyboard(ADMIN_URL, 'uz', 'btn_admin_web'))
    else:
        await message.answer(tr(lang, 'welcome_back', name=message.from_user.first_name),
                             reply_markup=webapp_keyboard(WEB_APP_URL, lang, 'btn_open_menu'))


@router.message(Command("start"))
async def cmd_start(message: Message):
    await open_site(message)


# Eski tugmalar yoki ixtiyoriy matn: yana saytga yo'naltiramiz
@router.message(F.chat.type == "private")
async def any_message(message: Message):
    await open_site(message)


# ==================== ADMIN: buyurtma xabarlari ====================

async def change_status(callback: CallbackQuery, status, toast):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    order_id = int(callback.data.rsplit("_", 1)[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("Topilmadi", show_alert=True)
        return
    allowed = {'completed': ('pending',), 'cancelled': ('pending',), 'delivered': ('completed',)}
    if order['status'] not in allowed[status]:
        await notify.refresh_admin_message(bot, db, order, callback.message.message_id)   # eskirgan xabarni yangilab qo'yamiz
        await callback.answer("Holat allaqachon o'zgargan")
        return
    await db.update_order_status(order_id, status)
    order = await db.get_order(order_id)
    await notify.notify_status_change(bot, db, order)
    await notify.refresh_admin_message(bot, db, order, callback.message.message_id)
    await callback.answer(toast)


@router.callback_query(F.data.startswith("approve_order_"))
async def approve_order(callback: CallbackQuery):
    await change_status(callback, "completed", "✅ Buyurtma tasdiqlandi")


@router.callback_query(F.data.startswith("reject_order_"))
async def reject_order(callback: CallbackQuery):
    await change_status(callback, "cancelled", "❌ Buyurtma bekor qilindi")


@router.callback_query(F.data.startswith("delivered_order_"))
async def delivered_order(callback: CallbackQuery):
    await change_status(callback, "delivered", "🚚 Yetkazib berildi")


# ==================== MAIN ====================

async def on_startup():
    await db.connect()
    try:   # hamma uchun standart tugma: "Menyu"
        await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="Menyu", web_app=WebAppInfo(url=WEB_APP_URL)))
    except Exception as e:
        logger.warning("Default menu button not set: %s", e)
    logger.info("Bot ishga tushdi!")


async def on_shutdown():
    await db.close()
    logger.info("Bot to'xtatildi!")


async def main():
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
