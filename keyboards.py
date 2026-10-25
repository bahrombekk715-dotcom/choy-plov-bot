from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from translations import get_text

def language_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    return keyboard

def phone_keyboard(lang='uz'):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text(lang, 'btn_phone'), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def main_menu_keyboard(lang='uz'):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, 'btn_menu'))],
            [KeyboardButton(text=get_text(lang, 'btn_my_orders')), KeyboardButton(text=get_text(lang, 'btn_profile'))],
            [KeyboardButton(text=get_text(lang, 'btn_language'))]
        ],
        resize_keyboard=True
    )
    return keyboard

def admin_menu_keyboard(lang='uz'):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, 'btn_new_orders')), KeyboardButton(text=get_text(lang, 'btn_today_stats'))],
            [KeyboardButton(text=get_text(lang, 'btn_add_product')), KeyboardButton(text=get_text(lang, 'btn_add_image'))],
            [KeyboardButton(text=get_text(lang, 'btn_toggle_product')), KeyboardButton(text=get_text(lang, 'btn_delete_product'))],
            [KeyboardButton(text=get_text(lang, 'btn_add_category'))],
            [KeyboardButton(text=get_text(lang, 'btn_user_mode'))]
        ],
        resize_keyboard=True
    )
    return keyboard

def categories_inline_keyboard(categories, lang='uz'):
    buttons = []
    for category in categories:
        buttons.append([InlineKeyboardButton(text=category['name'], callback_data=f"cat_{category['id']}")])
    buttons.append([InlineKeyboardButton(text=get_text(lang, 'btn_back'), callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def products_inline_keyboard(products, category_id, lang='uz'):
    buttons = []
    for product in products:
        status = "✅" if product['is_available'] else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {product['name']} - {product['price']:,.0f} so'm",
            callback_data=f"prod_{product['id']}"
        )])
    buttons.append([InlineKeyboardButton(text=get_text(lang, 'btn_back'), callback_data="back_to_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def quantity_keyboard(product_id, lang='uz'):
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
        [InlineKeyboardButton(text=get_text(lang, 'btn_back'), callback_data=f"back_to_products")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def addons_keyboard(product_id, quantity, lang='uz'):
    buttons = [
        [InlineKeyboardButton(text="🍖 Go'sht qo'shish", callback_data=f"addon_{product_id}_{quantity}_meat")],
        [InlineKeyboardButton(text="🥚 Tuxum qo'shish", callback_data=f"addon_{product_id}_{quantity}_egg")],
        [InlineKeyboardButton(text="🧀 Qazi qo'shish", callback_data=f"addon_{product_id}_{quantity}_qazi")],
        [InlineKeyboardButton(text="❌ Qo'shimcha kerak emas", callback_data=f"addon_{product_id}_{quantity}_none")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_order_keyboard(lang='uz'):
    buttons = [
        [InlineKeyboardButton(text=get_text(lang, 'btn_confirm'), callback_data="confirm_order")],
        [InlineKeyboardButton(text=get_text(lang, 'btn_cancel'), callback_data="cancel_order")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def order_action_keyboard(order_id, lang='uz'):
    buttons = [
        [InlineKeyboardButton(text=get_text(lang, 'btn_confirm'), callback_data=f"approve_order_{order_id}")],
        [InlineKeyboardButton(text=get_text(lang, 'btn_reject'), callback_data=f"reject_order_{order_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_admin_keyboard(lang='uz'):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text(lang, 'btn_back_admin'))]],
        resize_keyboard=True
    )
    return keyboard

def cancel_keyboard(lang='uz'):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text(lang, 'btn_cancel'))]],
        resize_keyboard=True
    )
    return keyboard

def admin_products_keyboard(products, lang='uz'):
    buttons = []
    for product in products:
        status = "🟢" if product['is_available'] else "🔴"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {product['name']}",
            callback_data=f"admin_prod_{product['id']}"
        )])
    buttons.append([InlineKeyboardButton(text=get_text(lang, 'btn_back'), callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def toggle_product_keyboard(product_id, is_available, lang='uz'):
    status_text = "🔴 To'xtatish" if is_available else "🟢 Yoqish"
    buttons = [
        [InlineKeyboardButton(text=status_text, callback_data=f"toggle_{product_id}")],
        [InlineKeyboardButton(text=get_text(lang, 'btn_back'), callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
