import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import BOT_TOKEN, ADMIN_ID
from database import Database
from keyboards import (
    phone_keyboard, main_menu_keyboard, admin_menu_keyboard,
    order_action_keyboard, back_to_admin_keyboard, cancel_keyboard,
    language_keyboard
)
from translations import get_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# Web App URL - Render.com deploy qilgandan keyin yangilanadi
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://your-domain.com')

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

# ==================== TIL TANLASH ====================

@router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]

    user = await db.get_user(callback.from_user.id)

    if user:
        # Mavjud foydalanuvchi - tilni yangilash
        await db.update_user_language(callback.from_user.id, lang)
        await callback.message.edit_text(
            get_text(lang, 'language_changed')
        )
        await callback.message.answer(
            get_text(lang, 'use_buttons'),
            reply_markup=main_menu_keyboard(lang)
        )
    else:
        # Yangi foydalanuvchi - telefon raqamini so'rash
        await db.add_user(
            callback.from_user.id,
            'temp',  # Vaqtincha telefon
            callback.from_user.username,
            callback.from_user.first_name
        )
        await db.update_user_language(callback.from_user.id, lang)

        await callback.message.edit_text(
            get_text(lang, 'welcome_new')
        )
        await callback.message.answer(
            get_text(lang, 'welcome_new'),
            reply_markup=phone_keyboard(lang)
        )

    await callback.answer()

@router.message(F.text.in_(["🌐 Til", "🌐 Язык", "🌐 Language"]))
async def show_language_menu(message: Message):
    lang = await db.get_user_language(message.from_user.id)
    await message.answer(
        get_text(lang, 'select_language'),
        reply_markup=language_keyboard()
    )

# ==================== FOYDALANUVCHI KOMMANDALARI ====================

@router.message(Command("start"))
async def cmd_start(message: Message):
    user = await db.get_user(message.from_user.id)

    # Tilni aniqlash
    lang = await db.get_user_language(message.from_user.id) if user else 'uz'

    if message.from_user.id == ADMIN_ID:
        await message.answer(
            get_text(lang, 'welcome_admin'),
            reply_markup=admin_menu_keyboard(lang)
        )
    elif user:
        # Web App tugmasi
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, 'btn_menu'), web_app=WebAppInfo(url=WEB_APP_URL))]
        ])

        await message.answer(
            get_text(lang, 'welcome_user', name=message.from_user.first_name),
            reply_markup=keyboard
        )
        await message.answer(
            get_text(lang, 'other_buttons'),
            reply_markup=main_menu_keyboard(lang)
        )
    else:
        # Yangi foydalanuvchi - til tanlash
        await message.answer(
            get_text('uz', 'select_language'),
            reply_markup=language_keyboard()
        )

@router.message(F.contact)
async def process_contact(message: Message):
    phone_number = message.contact.phone_number

    user = await db.get_user(message.from_user.id)
    lang = await db.get_user_language(message.from_user.id) if user else 'uz'

    # Telefon raqamini yangilash
    await db.add_user(
        message.from_user.id,
        phone_number,
        message.from_user.username,
        message.from_user.first_name
    )

    # Web App tugmasi
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, 'btn_menu'), web_app=WebAppInfo(url=WEB_APP_URL))]
    ])

    await message.answer(
        get_text(lang, 'phone_saved'),
        reply_markup=keyboard
    )
    await message.answer(
        get_text(lang, 'use_buttons'),
        reply_markup=main_menu_keyboard(lang)
    )

@router.message(F.text.in_(["🍽 Menyu", "🍽 Меню", "🍽 Menu"]))
async def show_menu(message: Message):
    lang = await db.get_user_language(message.from_user.id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, 'btn_open_menu'), web_app=WebAppInfo(url=WEB_APP_URL))]
    ])

    await message.answer(
        get_text(lang, 'open_menu'),
        reply_markup=keyboard
    )

@router.message(F.text.in_(["📦 Mening buyurtmalarim", "📦 Мои заказы", "📦 My orders"]))
async def my_orders(message: Message):
    lang = await db.get_user_language(message.from_user.id)
    orders = await db.get_user_orders(message.from_user.id)

    if not orders:
        await message.answer(get_text(lang, 'no_orders'))
        return

    await message.answer(get_text(lang, 'your_orders', count=len(orders)))

    for order in orders[:10]:  # Oxirgi 10 ta
        status_emoji = {
            'pending': '⏳',
            'completed': '✅',
            'cancelled': '❌'
        }

        text = f"{status_emoji.get(order['status'], '❓')} {get_text(lang, 'order_num', id=order['id'])}\n\n"
        text += get_text(lang, 'order_time', time=order['created_at']) + "\n"
        text += get_text(lang, 'order_total', price=f"{order['total_price']:,.0f}") + "\n"
        text += get_text(lang, 'order_address', address=order['address']) + "\n"

        status_key = f"status_{order['status']}"
        status_display = get_text(lang, status_key)
        text += get_text(lang, 'order_status', status=status_display)

        # Buyurtma tafsilotlari
        items = await db.get_order_items(order['id'])
        if items:
            text += get_text(lang, 'order_items')
            for item in items:
                text += f"\n• {item['product_name']} x{item['quantity']}"

                # Qo'shimchalarni ko'rsatish
                addons = await db.get_order_addons(item['id'])
                if addons:
                    addon_names = [addon['name'] for addon in addons]
                    text += f" (+{', '.join(addon_names)})"

        await message.answer(text)

@router.message(F.text.in_(["👤 Profil", "👤 Профиль", "👤 Profile"]))
async def show_profile(message: Message):
    lang = await db.get_user_language(message.from_user.id)
    user = await db.get_user(message.from_user.id)

    if not user:
        await message.answer(get_text(lang, 'profile_not_found'))
        return

    orders = await db.get_user_orders(message.from_user.id)
    completed_orders = [o for o in orders if o['status'] == 'completed']

    text = get_text(lang, 'profile_title')
    text += get_text(lang, 'profile_name', name=user['first_name']) + "\n"
    if user['username']:
        text += get_text(lang, 'profile_username', username=user['username']) + "\n"
    text += get_text(lang, 'profile_phone', phone=user['phone_number']) + "\n"
    text += get_text(lang, 'profile_orders', count=len(orders)) + "\n"
    text += get_text(lang, 'profile_completed', count=len(completed_orders)) + "\n"
    text += get_text(lang, 'profile_registered', date=user['created_at'])

    await message.answer(text)

# ==================== ADMIN KOMMANDALARI ====================

@router.message(F.text.in_(["📋 Yangi buyurtmalar", "📋 Новые заказы", "📋 New orders"]))
async def show_pending_orders(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    lang = await db.get_user_language(message.from_user.id)
    orders = await db.get_pending_orders()

    if not orders:
        await message.answer(get_text(lang, 'no_new_orders'))
        return

    await message.answer(get_text(lang, 'new_orders_title', count=len(orders)))

    for order in orders:
        order_items = await db.get_order_items(order['id'])

        # Foydalanuvchi ma'lumotlari
        user = await db.get_user(order['user_id'])
        user_lang = await db.get_user_language(order['user_id'])

        unknown_text = get_text(lang, 'unknown')
        text = f"🔔 {get_text(lang, 'order_num', id=order['id'])}\n\n"
        text += get_text(lang, 'order_customer', name=user['first_name'] if user else unknown_text) + "\n"
        if user and user['username']:
            text += f"🆔 @{user['username']}\n"
        text += get_text(lang, 'order_phone', phone=order['phone_number']) + "\n"
        text += get_text(lang, 'order_address', address=order['address']) + "\n"
        text += get_text(lang, 'order_time', time=order['created_at']) + "\n\n"

        text += get_text(lang, 'order_items')
        for item in order_items:
            text += f"\n• {item['product_name']} x{item['quantity']} - {item['price']:,.0f} so'm"

            # Qo'shimchalar
            addons = await db.get_order_addons(item['id'])
            if addons:
                for addon in addons:
                    text += f"\n  + {addon['name']}"

        if order['comment']:
            text += get_text(lang, 'order_comment', comment=order['comment'])

        text += f"\n\n💰 {get_text(lang, 'order_total', price=f'{order["total_price"]:,.0f}')}"

        await message.answer(
            text,
            reply_markup=order_action_keyboard(order['id'], lang)
        )

@router.callback_query(F.data.startswith("approve_order_"))
async def approve_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    await db.update_order_status(order_id, "completed")

    order = await db.get_order(order_id)

    # Admin tili
    admin_lang = await db.get_user_language(callback.from_user.id)
    # Mijoz tili
    user_lang = await db.get_user_language(order['user_id'])

    await callback.message.edit_text(
        callback.message.text + get_text(admin_lang, 'order_confirmed')
    )

    try:
        await bot.send_message(
            order['user_id'],
            get_text(user_lang, 'order_approved', id=order_id)
        )
    except Exception as e:
        logger.error(f"Could not send message to user: {e}")

    await callback.answer(get_text(admin_lang, 'order_confirmed').strip())

@router.callback_query(F.data.startswith("reject_order_"))
async def reject_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    await db.update_order_status(order_id, "cancelled")

    order = await db.get_order(order_id)

    # Admin tili
    admin_lang = await db.get_user_language(callback.from_user.id)
    # Mijoz tili
    user_lang = await db.get_user_language(order['user_id'])

    await callback.message.edit_text(
        callback.message.text + get_text(admin_lang, 'order_rejected')
    )

    try:
        await bot.send_message(
            order['user_id'],
            get_text(user_lang, 'order_rejected_msg', id=order_id)
        )
    except Exception as e:
        logger.error(f"Could not send message to user: {e}")

    await callback.answer(get_text(admin_lang, 'order_rejected').strip())

@router.message(F.text.in_(["📊 Bugungi statistika", "📊 Статистика за сегодня", "📊 Today's statistics"]))
async def show_today_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    lang = await db.get_user_language(message.from_user.id)
    stats = await db.get_today_stats()

    text = get_text(lang, 'stats_title')
    text += get_text(lang, 'stats_orders', count=stats['total_orders'] or 0) + "\n"
    text += get_text(lang, 'stats_revenue', amount=f"{stats['total_revenue'] or 0:,.0f}") + "\n"
    text += get_text(lang, 'stats_completed', amount=f"{stats['completed_revenue'] or 0:,.0f}")

    # Kutilayotgan buyurtmalar
    pending = await db.get_pending_orders()
    text += get_text(lang, 'stats_pending', count=len(pending))

    await message.answer(text)

@router.message(F.text.in_(["📂 Kategoriya qo'shish", "📂 Добавить категорию", "📂 Add category"]))
async def add_category_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    lang = await db.get_user_language(message.from_user.id)

    await message.answer(
        get_text(lang, 'enter_category_name'),
        reply_markup=back_to_admin_keyboard(lang)
    )
    await state.set_state(AddCategoryState.waiting_for_name)

@router.message(AddCategoryState.waiting_for_name)
async def add_category_name(message: Message, state: FSMContext):
    lang = await db.get_user_language(message.from_user.id)

    if message.text in [get_text(lang, 'btn_back_admin'), "🔙 Admin paneliga qaytish"]:
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=admin_menu_keyboard(lang))
        return

    await db.add_category(message.text)
    await message.answer(
        get_text(lang, 'category_added', name=message.text),
        reply_markup=admin_menu_keyboard(lang)
    )
    await state.clear()

@router.message(F.text.in_(["➕ Mahsulot qo'shish", "➕ Добавить продукт", "➕ Add product"]))
async def add_product_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    lang = await db.get_user_language(message.from_user.id)
    categories = await db.get_categories(active_only=False)

    if not categories:
        await message.answer(get_text(lang, 'no_categories'))
        return

    text = get_text(lang, 'select_category')
    for cat in categories:
        text += f"/{cat['id']} - {cat['name']}\n"

    await message.answer(text, reply_markup=back_to_admin_keyboard(lang))
    await state.set_state(AddProductState.waiting_for_category)

@router.message(AddProductState.waiting_for_category)
async def add_product_category(message: Message, state: FSMContext):
    lang = await db.get_user_language(message.from_user.id)

    if message.text in [get_text(lang, 'btn_back_admin'), "🔙 Admin paneliga qaytish"]:
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=admin_menu_keyboard(lang))
        return

    try:
        category_id = int(message.text.replace('/', ''))
        category = await db.get_category(category_id)

        if not category:
            await message.answer(get_text(lang, 'category_not_found'))
            return

        await state.update_data(category_id=category_id)
        await message.answer(get_text(lang, 'enter_product_name'))
        await state.set_state(AddProductState.waiting_for_name)
    except ValueError:
        await message.answer(get_text(lang, 'invalid_format'))

@router.message(AddProductState.waiting_for_name)
async def add_product_name(message: Message, state: FSMContext):
    lang = await db.get_user_language(message.from_user.id)

    if message.text in [get_text(lang, 'btn_back_admin'), "🔙 Admin paneliga qaytish"]:
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=admin_menu_keyboard(lang))
        return

    await state.update_data(name=message.text)
    await message.answer(get_text(lang, 'enter_product_price'))
    await state.set_state(AddProductState.waiting_for_price)

@router.message(AddProductState.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    lang = await db.get_user_language(message.from_user.id)

    if message.text in [get_text(lang, 'btn_back_admin'), "🔙 Admin paneliga qaytish"]:
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=admin_menu_keyboard(lang))
        return

    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer(get_text(lang, 'enter_product_desc'))
        await state.set_state(AddProductState.waiting_for_description)
    except ValueError:
        await message.answer(get_text(lang, 'invalid_price'))

@router.message(AddProductState.waiting_for_description)
async def add_product_description(message: Message, state: FSMContext):
    lang = await db.get_user_language(message.from_user.id)

    if message.text in [get_text(lang, 'btn_back_admin'), "🔙 Admin paneliga qaytish"]:
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=admin_menu_keyboard(lang))
        return

    description = None if message.text.lower() in ['yoq', 'yo\'q', 'no', 'нет', 'net'] else message.text

    await state.update_data(description=description)
    await message.answer(
        get_text(lang, 'send_product_image'),
        reply_markup=back_to_admin_keyboard(lang)
    )
    await state.set_state(AddProductState.waiting_for_image)

@router.message(AddProductState.waiting_for_image)
async def add_product_image(message: Message, state: FSMContext):
    lang = await db.get_user_language(message.from_user.id)

    if message.text in [get_text(lang, 'btn_back_admin'), "🔙 Admin paneliga qaytish"]:
        await state.clear()
        await message.answer(get_text(lang, 'cancelled'), reply_markup=admin_menu_keyboard(lang))
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

    elif message.text and message.text.lower() not in ['yoq', 'yo\'q', 'no', 'нет', 'net']:
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

    response_text = get_text(lang, 'product_added', name=data['name'], price=f"{data['price']:,.0f}")
    if image_url:
        response_text += get_text(lang, 'image_added')

    await message.answer(
        response_text,
        reply_markup=admin_menu_keyboard(lang)
    )
    await state.clear()

@router.message(F.text.in_(["📸 Mahsulotga rasm qo'shish", "📸 Добавить фото к продукту", "📸 Add image to product"]))
async def add_image_to_product_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    lang = await db.get_user_language(message.from_user.id)
    categories = await db.get_categories()

    if not categories:
        await message.answer(get_text(lang, 'no_categories'))
        return

    text = get_text(lang, 'select_category')
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
    lang = await db.get_user_language(callback.from_user.id)
    category_id = int(callback.data.split("_")[2])
    products = await db.get_products_by_category(category_id, available_only=False)

    if not products:
        await callback.answer(get_text(lang, 'no_products_in_cat'), show_alert=True)
        return

    buttons = []
    for product in products:
        has_image = "📸" if product.get('image_url') else "📷"
        buttons.append([InlineKeyboardButton(
            text=f"{has_image} {product['name']}",
            callback_data=f"img_prod_{product['id']}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(
        get_text(lang, 'select_product'),
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("img_prod_"))
async def select_product_for_image(callback: CallbackQuery, state: FSMContext):
    lang = await db.get_user_language(callback.from_user.id)
    product_id = int(callback.data.split("_")[2])
    product = await db.get_product(product_id)

    await state.update_data(product_id=product_id)
    await state.set_state(AddImageState.waiting_for_image)

    text = get_text(lang, 'send_image_for', name=product['name'])

    if product.get('image_url'):
        text += get_text(lang, 'image_will_replace')

    await callback.message.edit_text(text)
    await callback.answer()

@router.message(AddImageState.waiting_for_image)
async def save_product_image(message: Message, state: FSMContext):
    lang = await db.get_user_language(message.from_user.id)
    data = await state.get_data()
    product_id = data['product_id']

    image_url = None

    if message.photo:
        photo = message.photo[-1]
        image_url = photo.file_id
    elif message.text and message.text.startswith('http'):
        image_url = message.text
    else:
        await message.answer(get_text(lang, 'send_image_or_url'))
        return

    await db.update_product_image(product_id, image_url)

    product = await db.get_product(product_id)

    await message.answer(
        get_text(lang, 'image_added_to', name=product['name']),
        reply_markup=admin_menu_keyboard(lang)
    )
    await state.clear()

@router.message(F.text.in_(["🔴 Mahsulotni to'xtatish/yoqish", "🔴 Остановить/включить продукт", "🔴 Stop/enable product"]))
async def toggle_product_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    lang = await db.get_user_language(message.from_user.id)
    categories = await db.get_categories()

    if not categories:
        await message.answer(get_text(lang, 'no_categories'))
        return

    text = get_text(lang, 'select_category')
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
    lang = await db.get_user_language(callback.from_user.id)
    category_id = int(callback.data.split("_")[2])
    products = await db.get_products_by_category(category_id, available_only=False)

    if not products:
        await callback.answer(get_text(lang, 'no_products_in_cat'), show_alert=True)
        return

    buttons = []
    for product in products:
        status = "🟢" if product['is_available'] else "🔴"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {product['name']}",
            callback_data=f"toggle_prod_{product['id']}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(get_text(lang, 'select_product_toggle'), reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_prod_"))
async def toggle_product(callback: CallbackQuery):
    lang = await db.get_user_language(callback.from_user.id)
    product_id = int(callback.data.split("_")[2])
    product = await db.get_product(product_id)

    await db.toggle_product_availability(product_id)

    # Refresh product data
    product = await db.get_product(product_id)
    status = get_text(lang, 'product_enabled') if product['is_available'] else get_text(lang, 'product_disabled')

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

@router.message(F.text.in_(["👤 Foydalanuvchi rejimi", "👤 Режим пользователя", "👤 User mode"]))
async def user_mode(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    lang = await db.get_user_language(message.from_user.id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, 'btn_menu'), web_app=WebAppInfo(url=WEB_APP_URL))]
    ])

    await message.answer(
        get_text(lang, 'user_mode_switched'),
        reply_markup=keyboard
    )
    await message.answer(
        get_text(lang, 'use_buttons'),
        reply_markup=main_menu_keyboard(lang)
    )

# ==================== MAIN ====================

async def on_startup():
    """Bot ishga tushganda"""
    await db.connect()

    # Standart qo'shimchalarni qo'shamiz
    addons = await db.get_addons()
    if not addons:
        await db.add_addon("Go'sht", 15000)
        await db.add_addon("Tuxum", 5000)
        await db.add_addon("Qazi", 20000)
        logger.info("Default addons created")

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
