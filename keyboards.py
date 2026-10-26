from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from i18n import tr


def webapp_keyboard(url, lang='uz', key='btn_menu'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(lang, key), web_app=WebAppInfo(url=url))]
    ])


def order_keyboard(order_id, status='pending'):
    """Adminga keladigan buyurtma xabari tugmalari: kutilmoqda -> tasdiqlash/bekor, tasdiqlangan -> yetkazib berildi."""
    if status == 'pending':
        rows = [[InlineKeyboardButton(text="Tasdiqlash", callback_data=f"approve_order_{order_id}")],
                [InlineKeyboardButton(text="Bekor qilish", callback_data=f"reject_order_{order_id}")]]
    elif status == 'completed':
        rows = [[InlineKeyboardButton(text="Yetkazib berildi", callback_data=f"delivered_order_{order_id}")]]
    else:
        return None
    return InlineKeyboardMarkup(inline_keyboard=rows)
