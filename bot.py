import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, MenuButtonWebApp

from config import BOT_TOKEN, ADMIN_ID, WEB_APP_URL
from database import Database
from i18n import tr, variants, norm_lang, LANGS
from keyboards import (
    order_action_keyboard,
    phone_keyboard, main_menu_keyboard, admin_menu_keyboard, webapp_keyboard, lang_keyboard,
    back_to_admin_keyboard, cancel_keyboard
)
import notify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

class AddProductState(StatesGroup):
    waiting_for_category = State()
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_description = State()
    waiting_for_image = State()

class AddCategoryState(StatesGroup):
    waiting_for_name = State()

class EditProductState(StatesGroup):
    waiting_for_product = State()
    waiting_for_field = State()
    waiting_for_value = State()

class AddImageState(StatesGroup):
    waiting_for_product_id = State()
    waiting_for_image = State()

# ==================== FOYDALANUVCHI KOMMANDALARI ====================

LANG_LABEL = {'uz': "O'zbekcha", 'ru': 'Русский', 'en': 'English'}
STATUS_EMOJI = {'pending': '⏳', 'completed': '✅', 'cancelled': '❌'}


async def lang_of(user_id):
    return await db.get_language(user_id)


async def set_menu_button(chat_id, lang='uz', admin=False):
    """Chat pastidagi menyu tugmasi: adminda "Admin panel" (/admin), foydalanuvchida "Menyu" (sayt)."""
    try:
        if admin:
            btn = MenuButtonWebApp(text="Admin panel", web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin"))
        else:
            btn = MenuButtonWebApp(text=tr(lang, 'btn_menu').lstrip('🍽 '), web_app=WebAppInfo(url=WEB_APP_URL))
        await bot.set_chat_menu_button(chat_id=chat_id, menu_button=btn)
    except Exception as e:
        logger.warning("Menu button not set for %s: %s", chat_id, e)


@router.message(Command("start"))
async def cmd_start(message: Message):
    uid = message.from_user.id
    user = await db.get_user(uid)

    if uid == ADMIN_ID:
        await set_menu_button(uid, admin=True)
        await message.answer(
            "👨‍💼 Assalomu alaykum, Admin!\n\n"
            "Admin panelidan foydalaning:",
            reply_markup=admin_menu_keyboard()
        )
        await message.answer(
            "🖥 Web admin panel (dashboard, foydalanuvchilar, buyurtmalar, mahsulotlar):",
            reply_markup=webapp_keyboard(f"{WEB_APP_URL}/admin", 'uz', 'btn_admin_web')
        )
    elif user:
        lang = user['language'] or 'uz'
        await set_menu_button(uid, lang)
        await message.answer(
            tr(lang, 'welcome_back', name=message.from_user.first_name),
            reply_markup=webapp_keyboard(WEB_APP_URL, lang)
        )
        await message.answer(tr(lang, 'use_buttons'), reply_markup=main_menu_keyboard(lang))
    else:
        lang = norm_lang(message.from_user.language_code)
        await set_menu_button(uid, lang)
        await message.answer(tr(lang, 'welcome_new'), reply_markup=phone_keyboard(lang))


@router.message(F.contact)
async def process_contact(message: Message):
    # Faqat o'z raqamini yuborishi mumkin (boshqa odamning kontaktini emas)
    if message.contact.user_id != message.from_user.id:
        return
    existing = await db.get_user(message.from_user.id)
    lang = existing['language'] if existing else norm_lang(message.from_user.language_code)
    await db.add_user(
        message.from_user.id,
        message.contact.phone_number,
        message.from_user.username,
        message.from_user.first_name,
        lang
    )
    await set_menu_button(message.from_user.id, lang, admin=message.from_user.id == ADMIN_ID)
    await message.answer(tr(lang, 'phone_saved'), reply_markup=webapp_keyboard(WEB_APP_URL, lang))
    await message.answer(tr(lang, 'use_buttons'), reply_markup=main_menu_keyboard(lang))


async def registered_lang(message: Message):
    """Ro'yxatdan o'tgan foydalanuvchi tilini qaytaradi, aks holda ro'yxatdan o'tishni so'raydi."""
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer(tr(norm_lang(message.from_user.language_code), 'need_register'))
        return None
    return user['language'] or 'uz'


@router.message(F.text.in_(variants('btn_menu')))
async def show_menu(message: Message):
    lang = await lang_of(message.from_user.id)
    await message.answer(tr(lang, 'open_menu_text'), reply_markup=webapp_keyboard(WEB_APP_URL, lang, 'btn_open_menu'))


@router.message(F.text.in_(variants('btn_lang')))
async def choose_language(message: Message):
    if await registered_lang(message) is None:
        return
    await message.answer(tr(await lang_of(message.from_user.id), 'choose_lang'), reply_markup=lang_keyboard())


@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split("_", 1)[1]
    if lang not in LANGS or not await db.get_user(callback.from_user.id):
        await callback.answer()
        return
    await db.set_language(callback.from_user.id, lang)
    await set_menu_button(callback.from_user.id, lang, admin=callback.from_user.id == ADMIN_ID)
    await callback.message.edit_text(tr(lang, 'lang_saved'))
    await callback.message.answer(tr(lang, 'use_buttons'), reply_markup=main_menu_keyboard(lang))
    await callback.answer()


@router.message(F.text.in_(variants('btn_orders')))
async def my_orders(message: Message):
    lang = await registered_lang(message)
    if lang is None:
        return
    orders = await db.get_user_orders(message.from_user.id)

    if not orders:
        await message.answer(tr(lang, 'no_orders'))
        return

    await message.answer(tr(lang, 'orders_title', n=len(orders)))
    cur = tr(lang, 'currency')

    for order in orders[:10]:  # Oxirgi 10 ta
        text = f"{STATUS_EMOJI.get(order['status'], '❓')} {tr(lang, 'order_no', id=order['id'])}\n\n"
        text += f"{tr(lang, 'lbl_time')}: {order['created_at']}\n"
        text += f"{tr(lang, 'lbl_sum')}: {notify.fmt_money(order['total_price'])} {cur}\n"
        text += f"{tr(lang, 'lbl_address')}: {order['address']}\n"
        text += f"{tr(lang, 'lbl_status')}: {tr(lang, 'st_' + order['status'])}"

        items = await db.get_order_items(order['id'])
        if items:
            text += f"\n\n{tr(lang, 'lbl_products')}:"
            for item in items:
                text += f"\n• {item['product_name']} x{item['quantity']}"
                addons = await db.get_order_addons(item['id'])
                if addons:
                    text += f" (+{', '.join(a['name'] for a in addons)})"

        await message.answer(text)


@router.message(F.text.in_(variants('btn_profile')))
async def show_profile(message: Message):
    lang = await registered_lang(message)
    if lang is None:
        return
    user = await db.get_user(message.from_user.id)
    stats = await db.get_user_stats(message.from_user.id)

    text = f"{tr(lang, 'profile_title')}\n\n"
    text += f"{tr(lang, 'lbl_name')}: {user['first_name']}\n"
    if user['username']:
        text += f"🆔 Username: @{user['username']}\n"
    text += f"{tr(lang, 'lbl_phone')}: {user['phone_number']}\n"
    text += f"{tr(lang, 'lbl_total_orders')}: {stats['orders']}\n"
    text += f"{tr(lang, 'lbl_done_orders')}: {stats['completed']}\n"
    text += f"{tr(lang, 'lbl_language')}: {LANG_LABEL[lang]}\n"
    text += f"{tr(lang, 'lbl_registered')}: {user['created_at']}"

    await message.answer(text)


# ==================== ADMIN KOMMANDALARI ====================

@router.message(F.text == "📋 Yangi buyurtmalar")
async def show_pending_orders(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    orders = await db.get_pending_orders()

    if not orders:
        await message.answer("📭 Yangi buyurtmalar yo'q.")
        return

    await message.answer(f"📋 Yangi buyurtmalar ({len(orders)} ta):")

    for order in orders:
        await message.answer(
            await notify.format_admin_order(db, order),
            reply_markup=order_action_keyboard(order['id'])
        )


async def set_order_status(callback: CallbackQuery, status, mark, toast):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    order_id = int(callback.data.rsplit("_", 1)[1])
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return
    if order['status'] == status:
        await callback.answer(toast)
        return
    await db.update_order_status(order_id, status)
    await notify.notify_status_change(bot, db, await db.get_order(order_id))
    await callback.message.edit_text(callback.message.text + f"\n\n{mark}")
    await callback.answer(toast)


@router.callback_query(F.data.startswith("approve_order_"))
async def approve_order(callback: CallbackQuery):
    await set_order_status(callback, "completed", "✅ Tasdiqlandi!", "✅ Buyurtma tasdiqlandi!")


@router.callback_query(F.data.startswith("reject_order_"))
async def reject_order(callback: CallbackQuery):
    await set_order_status(callback, "cancelled", "❌ Bekor qilindi!", "❌ Buyurtma bekor qilindi!")


@router.message(F.text == "📊 Bugungi statistika")
async def show_today_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    stats = await db.get_today_stats()

    text = "📊 Bugungi statistika:\n\n"
    text += f"📦 Buyurtmalar soni: {stats['total_orders'] or 0}\n"
    text += f"💰 Umumiy savdo: {stats['total_revenue'] or 0:,.0f} so'm\n"
    text += f"✅ Tasdiqlangan: {stats['completed_revenue'] or 0:,.0f} so'm"

    # Kutilayotgan buyurtmalar
    pending = await db.get_pending_orders()
    text += f"\n⏳ Kutilayotgan: {len(pending)} ta"

    await message.answer(text)

@router.message(F.text == "📂 Kategoriya qo'shish")
async def add_category_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "📝 Kategoriya nomini kiriting:",
        reply_markup=back_to_admin_keyboard()
    )
    await state.set_state(AddCategoryState.waiting_for_name)

@router.message(AddCategoryState.waiting_for_name)
async def add_category_name(message: Message, state: FSMContext):
    if message.text == "🔙 Admin paneliga qaytish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu_keyboard())
        return

    await db.add_category(message.text)
    await message.answer(
        f"✅ '{message.text}' kategoriyasi qo'shildi!",
        reply_markup=admin_menu_keyboard()
    )
    await state.clear()

@router.message(F.text == "➕ Mahsulot qo'shish")
async def add_product_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    categories = await db.get_categories(active_only=False)

    if not categories:
        await message.answer("❌ Avval kategoriya qo'shing!")
        return

    text = "📂 Kategoriyani tanlang:\n\n"
    for cat in categories:
        text += f"/{cat['id']} - {cat['name']}\n"

    await message.answer(text, reply_markup=back_to_admin_keyboard())
    await state.set_state(AddProductState.waiting_for_category)

@router.message(AddProductState.waiting_for_category)
async def add_product_category(message: Message, state: FSMContext):
    if message.text == "🔙 Admin paneliga qaytish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu_keyboard())
        return

    try:
        category_id = int(message.text.replace('/', ''))
        category = await db.get_category(category_id)

        if not category:
            await message.answer("❌ Kategoriya topilmadi! Qaytadan kiriting:")
            return

        await state.update_data(category_id=category_id)
        await message.answer("📝 Mahsulot nomini kiriting:")
        await state.set_state(AddProductState.waiting_for_name)
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Kategoriya raqamini kiriting:")

@router.message(AddProductState.waiting_for_name)
async def add_product_name(message: Message, state: FSMContext):
    if message.text == "🔙 Admin paneliga qaytish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu_keyboard())
        return

    await state.update_data(name=message.text)
    await message.answer("💰 Narxini kiriting (faqat raqam):")
    await state.set_state(AddProductState.waiting_for_price)

@router.message(AddProductState.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    if message.text == "🔙 Admin paneliga qaytish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu_keyboard())
        return

    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer("📝 Tavsifini kiriting (yoki 'Yo'q' deb yozing):")
        await state.set_state(AddProductState.waiting_for_description)
    except ValueError:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting:")

@router.message(AddProductState.waiting_for_description)
async def add_product_description(message: Message, state: FSMContext):
    if message.text == "🔙 Admin paneliga qaytish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu_keyboard())
        return

    description = None if message.text.lower() in ['yoq', 'yo\'q', 'no'] else message.text

    await state.update_data(description=description)
    await message.answer(
        "📸 Mahsulot rasmini yuboring\n\n"
        "(Yoki 'Yo'q' deb yozing):",
        reply_markup=back_to_admin_keyboard()
    )
    await state.set_state(AddProductState.waiting_for_image)

@router.message(AddProductState.waiting_for_image)
async def add_product_image(message: Message, state: FSMContext):
    if message.text == "🔙 Admin paneliga qaytish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu_keyboard())
        return

    image_url = None

    # Agar rasm yuborilgan bo'lsa
    if message.photo:
        # Eng katta o'lchamdagi rasmni olish
        photo = message.photo[-1]
        file_id = photo.file_id

        # File ID ni image_url sifatida saqlash
        # Keyinchalik bu file_id orqali rasmni olish mumkin
        image_url = file_id

    elif message.text and message.text.lower() not in ['yoq', 'yo\'q', 'no']:
        # Agar URL yuborilgan bo'lsa
        if message.text.startswith('http'):
            image_url = message.text

    data = await state.get_data()
    await db.add_product(
        data['category_id'],
        data['name'],
        data['price'],
        data['description'],
        image_url
    )

    response_text = f"✅ '{data['name']}' mahsuloti qo'shildi!\n"
    response_text += f"💰 Narxi: {data['price']:,.0f} so'm"
    if image_url:
        response_text += "\n📸 Rasm qo'shildi"

    await message.answer(
        response_text,
        reply_markup=admin_menu_keyboard()
    )
    await state.clear()

@router.message(F.text == "📸 Mahsulotga rasm qo'shish")
async def add_image_to_product_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    categories = await db.get_categories()

    if not categories:
        await message.answer("❌ Kategoriyalar yo'q!")
        return

    text = "📂 Kategoriyani tanlang:\n\n"
    buttons = []

    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=cat['name'],
            callback_data=f"img_cat_{cat['id']}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("img_cat_"))
async def show_products_for_image(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[2])
    products = await db.get_products_by_category(category_id, available_only=False)

    if not products:
        await callback.answer("Bu kategoriyada mahsulot yo'q!", show_alert=True)
        return

    buttons = []
    for product in products:
        has_image = "📸" if await db.count_product_images(product['id']) else "📷"
        buttons.append([InlineKeyboardButton(
            text=f"{has_image} {product['name']}",
            callback_data=f"img_prod_{product['id']}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(
        "📸 Mahsulotni tanlang:\n\n"
        "📸 = rasm mavjud\n"
        "📷 = rasm yo'q",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("img_prod_"))
async def select_product_for_image(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    product = await db.get_product(product_id)

    await state.update_data(product_id=product_id)
    await state.set_state(AddImageState.waiting_for_image)

    text = f"📸 '{product['name']}' uchun rasm yuboring:\n\n"
    text += "• Rasm fayli yuboring\n"
    text += "• Yoki rasm URL manzilini yuboring"

    n = await db.count_product_images(product_id)
    if n:
        text += f"\n\n📸 Hozir {n}/5 ta rasm bor (yangisi galereyaga qo'shiladi)"

    await callback.message.edit_text(text)
    await callback.answer()

@router.message(AddImageState.waiting_for_image)
async def save_product_image(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data['product_id']

    image_url = None

    if message.photo:
        photo = message.photo[-1]
        image_url = photo.file_id
    elif message.text and message.text.startswith('http'):
        image_url = message.text
    else:
        await message.answer("❌ Iltimos, rasm yoki URL yuboring!")
        return

    if await db.add_product_image(product_id, image_url) is None:
        await message.answer("❌ Maksimum 5 ta rasm. Avval web admin paneldan eskisini o'chiring.", reply_markup=admin_menu_keyboard())
        await state.clear()
        return

    product = await db.get_product(product_id)

    await message.answer(
        f"✅ '{product['name']}' mahsulotiga rasm qo'shildi!",
        reply_markup=admin_menu_keyboard()
    )
    await state.clear()

@router.message(F.text == "🔴 Mahsulotni to'xtatish/yoqish")
async def toggle_product_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    categories = await db.get_categories()

    if not categories:
        await message.answer("❌ Kategoriyalar yo'q!")
        return

    text = "📂 Kategoriyani tanlang:\n\n"
    buttons = []

    for cat in categories:
        buttons.append([InlineKeyboardButton(
            text=cat['name'],
            callback_data=f"toggle_cat_{cat['id']}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("toggle_cat_"))
async def show_products_to_toggle(callback: CallbackQuery):
    category_id = int(callback.data.split("_")[2])
    products = await db.get_products_by_category(category_id, available_only=False)

    if not products:
        await callback.answer("Bu kategoriyada mahsulot yo'q!", show_alert=True)
        return

    buttons = []
    for product in products:
        status = "🟢" if product['is_available'] else "🔴"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {product['name']}",
            callback_data=f"toggle_prod_{product['id']}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Mahsulotni tanlang:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_prod_"))
async def toggle_product(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    product = await db.get_product(product_id)

    await db.toggle_product_availability(product_id)

    # Refresh product data
    product = await db.get_product(product_id)
    status = "🟢 Yoqildi" if product['is_available'] else "🔴 To'xtatildi"

    await callback.answer(f"✅ {status}!", show_alert=True)

    # Refresh list
    category_id = product['category_id']
    products = await db.get_products_by_category(category_id, available_only=False)

    buttons = []
    for prod in products:
        status_icon = "🟢" if prod['is_available'] else "🔴"
        buttons.append([InlineKeyboardButton(
            text=f"{status_icon} {prod['name']}",
            callback_data=f"toggle_prod_{prod['id']}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_reply_markup(reply_markup=keyboard)

@router.message(F.text == "👤 Foydalanuvchi rejimi")
async def user_mode(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    lang = await lang_of(message.from_user.id)
    await message.answer("👤 Foydalanuvchi rejimiga o'tdingiz.", reply_markup=webapp_keyboard(WEB_APP_URL, lang))
    await message.answer(tr(lang, 'use_buttons'), reply_markup=main_menu_keyboard(lang))

# ==================== MAIN ====================

async def on_startup():
    """Bot ishga tushganda"""
    await db.connect()   # standart qo'shimchalar ham shu yerda yaratiladi
    try:   # hamma uchun standart tugma: "Menyu"
        await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="Menyu", web_app=WebAppInfo(url=WEB_APP_URL)))
    except Exception as e:
        logger.warning("Default menu button not set: %s", e)
    logger.info("Bot ishga tushdi!")

async def on_shutdown():
    """Bot to'xtaganda"""
    await db.close()
    logger.info("Bot to'xtatildi!")

async def main():
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
