from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from i18n import tr, LANGS, LANG_NAMES


def phone_keyboard(lang='uz'):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tr(lang, 'btn_phone'), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def main_menu_keyboard(lang='uz'):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(lang, 'btn_menu'))],
            [KeyboardButton(text=tr(lang, 'btn_orders')), KeyboardButton(text=tr(lang, 'btn_profile'))],
            [KeyboardButton(text=tr(lang, 'btn_lang'))],
        ],
        resize_keyboard=True
    )


def webapp_keyboard(url, lang='uz', key='btn_menu'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang, key), web_app=WebAppInfo(url=url))]
    ])


def lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANG_NAMES[code], callback_data=f"lang_{code}")] for code in LANGS
    ])


def admin_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Yangi buyurtmalar"), KeyboardButton(text="📊 Bugungi statistika")],
            [KeyboardButton(text="➕ Mahsulot qo'shish"), KeyboardButton(text="📸 Mahsulotga rasm qo'shish")],
            [KeyboardButton(text="🔴 Mahsulotni to'xtatish/yoqish"), KeyboardButton(text="🗑 Mahsulotni o'chirish")],
            [KeyboardButton(text="📂 Kategoriya qo'shish")],
            [KeyboardButton(text="👤 Foydalanuvchi rejimi")]
        ],
        resize_keyboard=True
    )
    return keyboard

def categories_inline_keyboard(categories):
    buttons = []
    for category in categories:
        buttons.append([InlineKeyboardButton(text=category['name'], callback_data=f"cat_{category['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def products_inline_keyboard(products, category_id):
    buttons = []
    for product in products:
        status = "✅" if product['is_available'] else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {product['name']} - {product['price']:,.0f} so'm",
            callback_data=f"prod_{product['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def quantity_keyboard(product_id):
    buttons = [
        [
            InlineKeyboardButton(text="1", callback_data=f"qty_{product_id}_1"),
            InlineKeyboardButton(text="2", callback_data=f"qty_{product_id}_2"),
            InlineKeyboardButton(text="3", callback_data=f"qty_{product_id}_3"),
        ],
        [
            InlineKeyboardButton(text="4", callback_data=f"qty_{product_id}_4"),
            InlineKeyboardButton(text="5", callback_data=f"qty_{product_id}_5"),
        ],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data=f"back_to_products")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def addons_keyboard(product_id, quantity):
    buttons = [
        [InlineKeyboardButton(text="🍖 Go'sht qo'shish", callback_data=f"addon_{product_id}_{quantity}_meat")],
        [InlineKeyboardButton(text="🥚 Tuxum qo'shish", callback_data=f"addon_{product_id}_{quantity}_egg")],
        [InlineKeyboardButton(text="🧀 Qazi qo'shish", callback_data=f"addon_{product_id}_{quantity}_qazi")],
        [InlineKeyboardButton(text="❌ Qo'shimcha kerak emas", callback_data=f"addon_{product_id}_{quantity}_none")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_order_keyboard():
    buttons = [
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def order_action_keyboard(order_id):
    buttons = [
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_order_{order_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"reject_order_{order_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Admin paneliga qaytish")]],
        resize_keyboard=True
    )
    return keyboard

def cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
    return keyboard

def admin_products_keyboard(products):
    buttons = []
    for product in products:
        status = "🟢" if product['is_available'] else "🔴"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {product['name']}",
            callback_data=f"admin_prod_{product['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def toggle_product_keyboard(product_id, is_available):
    status_text = "🔴 To'xtatish" if is_available else "🟢 Yoqish"
    buttons = [
        [InlineKeyboardButton(text=status_text, callback_data=f"toggle_{product_id}")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
