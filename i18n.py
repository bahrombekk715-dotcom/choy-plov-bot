"""Ko'p tillilik: O'zbek (uz), Rus (ru), Ingliz (en).

Bitta manba: bot xabarlari ham, web sayt matnlari ham (kalit `w_` bilan boshlansa
web uchun, `/api/i18n/{lang}` orqali beriladi) shu yerda turadi.
Har bir yozuv: kalit -> (uz, ru, en)
"""

LANGS = ('uz', 'ru', 'en')
DEFAULT_LANG = 'uz'
LANG_NAMES = {'uz': "🇺🇿 O'zbekcha", 'ru': '🇷🇺 Русский', 'en': '🇬🇧 English'}


def norm_lang(code):
    """Telegram language_code yoki saqlangan qiymatni uz/ru/en ga keltirish."""
    if not code:
        return DEFAULT_LANG
    code = str(code).lower()[:2]
    return code if code in LANGS else ('ru' if code in ('be', 'kk', 'uk', 'ky', 'tg') else 'en')


S = {
    # ---------------- BOT ----------------
    'choose_lang': ("🌐 Tilni tanlang", "🌐 Выберите язык", "🌐 Choose your language"),
    'lang_saved': ("✅ Til o'zgartirildi: O'zbekcha", "✅ Язык изменён: Русский", "✅ Language changed: English"),
    'welcome_new': (
        "👋 Assalomu alaykum! Choy Plov botiga xush kelibsiz!\n\nDavom etish uchun telefon raqamingizni yuboring:",
        "👋 Здравствуйте! Добро пожаловать в Choy Plov!\n\nЧтобы продолжить, отправьте свой номер телефона:",
        "👋 Hello! Welcome to Choy Plov!\n\nTo continue, please share your phone number:"),
    'btn_phone': ("📱 Telefon raqamni yuborish", "📱 Отправить номер телефона", "📱 Share phone number"),
    'phone_saved': (
        "✅ Telefon raqamingiz saqlandi!\n\n🍽 Endi buyurtma berishingiz mumkin.",
        "✅ Номер телефона сохранён!\n\n🍽 Теперь вы можете сделать заказ.",
        "✅ Your phone number is saved!\n\n🍽 You can place an order now."),
    'welcome_back': (
        "👋 Xush kelibsiz, {name}!\n\n🍽 Buyurtma berish uchun 'Menyu' tugmasini bosing.",
        "👋 С возвращением, {name}!\n\n🍽 Нажмите «Меню», чтобы сделать заказ.",
        "👋 Welcome back, {name}!\n\n🍽 Tap “Menu” to place an order."),
    'use_buttons': ("Yoki quyidagi tugmalardan foydalaning:", "Или воспользуйтесь кнопками ниже:", "Or use the buttons below:"),
    'btn_menu': ("🍽 Menyu", "🍽 Меню", "🍽 Menu"),
    'btn_open_menu': ("🍽 Menyuni ochish", "🍽 Открыть меню", "🍽 Open menu"),
    'btn_orders': ("📦 Mening buyurtmalarim", "📦 Мои заказы", "📦 My orders"),
    'btn_profile': ("👤 Profil", "👤 Профиль", "👤 Profile"),
    'btn_admin_web': ("🖥 Web admin panel", "🖥 Веб-админка", "🖥 Web admin panel"),
    'btn_lang': ("🌐 Til", "🌐 Язык", "🌐 Language"),
    'open_menu_text': (
        "🍽 Menyuni ko'rish va buyurtma berish uchun quyidagi tugmani bosing:",
        "🍽 Нажмите кнопку ниже, чтобы открыть меню и сделать заказ:",
        "🍽 Tap the button below to view the menu and place an order:"),
    'need_register': ("Avval /start bosing va telefon raqamingizni yuboring.",
                      "Сначала нажмите /start и отправьте номер телефона.",
                      "Please press /start and share your phone number first."),
    'no_orders': ("📭 Sizda buyurtmalar yo'q.", "📭 У вас пока нет заказов.", "📭 You have no orders yet."),
    'orders_title': ("📦 Sizning buyurtmalaringiz ({n} ta):\n", "📦 Ваши заказы ({n}):\n", "📦 Your orders ({n}):\n"),
    'order_no': ("Buyurtma #{id}", "Заказ #{id}", "Order #{id}"),
    'lbl_time': ("📅 Vaqt", "📅 Время", "📅 Time"),
    'lbl_sum': ("💰 Summa", "💰 Сумма", "💰 Total"),
    'lbl_address': ("📍 Manzil", "📍 Адрес", "📍 Address"),
    'lbl_status': ("📊 Holat", "📊 Статус", "📊 Status"),
    'lbl_products': ("📦 Mahsulotlar", "📦 Товары", "📦 Items"),
    'currency': ("so'm", "сум", "UZS"),
    'st_pending': ("⏳ Kutilmoqda", "⏳ Ожидает", "⏳ Pending"),
    'st_completed': ("✅ Tasdiqlandi", "✅ Подтверждён", "✅ Confirmed"),
    'st_cancelled': ("❌ Bekor qilindi", "❌ Отменён", "❌ Cancelled"),
    'profile_title': ("👤 Profil", "👤 Профиль", "👤 Profile"),
    'lbl_name': ("📝 Ism", "📝 Имя", "📝 Name"),
    'lbl_phone': ("📱 Telefon", "📱 Телефон", "📱 Phone"),
    'lbl_total_orders': ("📦 Jami buyurtmalar", "📦 Всего заказов", "📦 Total orders"),
    'lbl_done_orders': ("✅ Tasdiqlangan", "✅ Подтверждено", "✅ Confirmed"),
    'lbl_registered': ("📅 Ro'yxatdan o'tgan", "📅 Дата регистрации", "📅 Registered"),
    'lbl_language': ("🌐 Til", "🌐 Язык", "🌐 Language"),
    # --- "SMS" xabarnomalar (Telegram orqali) ---
    'n_created': (
        "🔔 Buyurtmangiz #{id} qabul qilindi!\n\n💰 Summa: {total} so'm\n📍 Manzil: {address}\n\n⏳ Admin tasdiqlashini kuting. Holati o'zgarsa xabar beramiz.",
        "🔔 Ваш заказ #{id} принят!\n\n💰 Сумма: {total} сум\n📍 Адрес: {address}\n\n⏳ Ожидайте подтверждения. Мы сообщим, когда статус изменится.",
        "🔔 Your order #{id} has been received!\n\n💰 Total: {total} UZS\n📍 Address: {address}\n\n⏳ Please wait for confirmation. We'll notify you of any status change."),
    'n_approved': (
        "✅ Buyurtmangiz #{id} tasdiqlandi!\n\n🚗 Yetkazib berish uchun tayyorlanmoqda...\nTez orada yetib boradi!",
        "✅ Ваш заказ #{id} подтверждён!\n\n🚗 Готовим к доставке...\nСкоро будет у вас!",
        "✅ Your order #{id} is confirmed!\n\n🚗 We're preparing it for delivery...\nIt will arrive soon!"),
    'n_cancelled': (
        "❌ Buyurtmangiz #{id} bekor qilindi.\n\nQo'shimcha ma'lumot uchun biz bilan bog'laning.",
        "❌ Ваш заказ #{id} отменён.\n\nЗа подробностями свяжитесь с нами.",
        "❌ Your order #{id} was cancelled.\n\nPlease contact us for more details."),

    # ---------------- WEB ----------------
    'w_menu': ("Menyu", "Меню", "Menu"),
    'w_favorites': ("Sevimlilar", "Избранное", "Favorites"),
    'w_orders': ("Buyurtmalar", "Заказы", "Orders"),
    'w_profile': ("Profil", "Профиль", "Profile"),
    'w_categories': ("Kategoriyalar", "Категории", "Categories"),
    'w_all': ("Hammasi", "Все", "All"),
    'w_back': ("Orqaga", "Назад", "Back"),
    'w_cart': ("Savat", "Корзина", "Cart"),
    'w_cart_empty': ("Savat bo'sh", "Корзина пуста", "Your cart is empty"),
    'w_add_to_cart': ("Savatchaga qo'shish", "В корзину", "Add to cart"),
    'w_added': ("Savatchaga qo'shildi", "Добавлено в корзину", "Added to cart"),
    'w_quantity': ("Miqdor", "Количество", "Quantity"),
    'w_addons': ("Qo'shimchalar", "Добавки", "Add-ons"),
    'w_addon_meat': ("Go'sht", "Мясо", "Meat"),
    'w_addon_egg': ("Bedana tuxumi", "Перепелиное яйцо", "Quail egg"),
    'w_addon_qazi': ("Qazi", "Казы", "Qazi sausage"),
    'w_total': ("Jami", "Итого", "Total"),
    'w_currency': ("so'm", "сум", "UZS"),
    'w_checkout': ("Buyurtma berish", "Оформить заказ", "Checkout"),
    'w_place_order': ("Buyurtmani tasdiqlash", "Подтвердить заказ", "Place order"),
    'w_phone': ("Telefon raqam", "Номер телефона", "Phone number"),
    'w_address': ("Yetkazib berish manzili", "Адрес доставки", "Delivery address"),
    'w_address_ph': ("Manzilni kiriting...", "Введите адрес...", "Enter address..."),
    'w_comment': ("Izoh (ixtiyoriy)", "Комментарий (необязательно)", "Comment (optional)"),
    'w_saved_addresses': ("Saqlangan manzillar", "Сохранённые адреса", "Saved addresses"),
    'w_new_address': ("Yangi manzil", "Новый адрес", "New address"),
    'w_save_address': ("Manzilni saqlash", "Сохранить адрес", "Save address"),
    'w_order_done': ("Buyurtma qabul qilindi!", "Заказ принят!", "Order received!"),
    'w_order_number': ("Buyurtma raqami", "Номер заказа", "Order number"),
    'w_order_done_hint': ("Holati o'zgarsa Telegram orqali xabar beramiz.", "О смене статуса сообщим в Telegram.", "We'll notify you in Telegram when the status changes."),
    'w_ok': ("OK", "OK", "OK"),
    'w_unavailable': ("Mavjud emas", "Нет в наличии", "Unavailable"),
    'w_no_products': ("Bu kategoriyada mahsulot yo'q", "В этой категории нет товаров", "No products in this category"),
    'w_no_categories': ("Kategoriyalar mavjud emas", "Категорий нет", "No categories yet"),
    'w_no_favorites': ("Hali sevimli mahsulotlar yo'q", "В избранном пока пусто", "No favorites yet"),
    'w_no_orders': ("Buyurtmalar topilmadi", "Заказы не найдены", "No orders found"),
    'w_no_addresses': ("Saqlangan manzillar yo'q", "Нет сохранённых адресов", "No saved addresses"),
    'w_status_all': ("Hammasi", "Все", "All"),
    'w_status_pending': ("Kutilmoqda", "Ожидает", "Pending"),
    'w_status_completed': ("Tasdiqlandi", "Подтверждён", "Confirmed"),
    'w_status_cancelled': ("Bekor qilindi", "Отменён", "Cancelled"),
    'w_date_from': ("Dan", "С", "From"),
    'w_date_to': ("Gacha", "По", "To"),
    'w_reset': ("Tozalash", "Сбросить", "Reset"),
    'w_reorder': ("Qayta buyurtma", "Повторить заказ", "Reorder"),
    'w_items': ("Mahsulotlar", "Товары", "Items"),
    'w_language': ("Til", "Язык", "Language"),
    'w_my_stats': ("Statistika", "Статистика", "Statistics"),
    'w_stat_orders': ("Buyurtmalar", "Заказов", "Orders"),
    'w_stat_spent': ("Sarflangan", "Потрачено", "Spent"),
    'w_addresses': ("Manzillarim", "Мои адреса", "My addresses"),
    'w_add_address': ("Manzil qo'shish", "Добавить адрес", "Add address"),
    'w_address_title': ("Nomi (Uy, Ish...)", "Название (Дом, Работа...)", "Title (Home, Work...)"),
    'w_default': ("Asosiy", "Основной", "Default"),
    'w_make_default': ("Asosiy qilish", "Сделать основным", "Make default"),
    'w_save': ("Saqlash", "Сохранить", "Save"),
    'w_cancel': ("Bekor qilish", "Отмена", "Cancel"),
    'w_delete': ("O'chirish", "Удалить", "Delete"),
    'w_edit': ("Tahrirlash", "Изменить", "Edit"),
    'w_saved': ("Saqlandi", "Сохранено", "Saved"),
    'w_error': ("Xatolik yuz berdi", "Произошла ошибка", "Something went wrong"),
    'w_need_telegram': ("Bu funksiya uchun saytni Telegram bot orqali oching", "Откройте сайт через Telegram-бота, чтобы пользоваться этой функцией", "Open the site through the Telegram bot to use this feature"),
    'w_fill_phone': ("Telefon raqamni kiriting", "Введите номер телефона", "Enter your phone number"),
    'w_fill_address': ("Manzilni kiriting", "Введите адрес", "Enter your address"),
    'w_need_register': ("Avval Telegram botda /start bosib, telefon raqamingizni yuboring", "Сначала нажмите /start в Telegram-боте и отправьте номер телефона", "First press /start in the Telegram bot and share your phone number"),
    'w_admin_panel': ("Admin panel", "Админ-панель", "Admin panel"),
    'w_name': ("Ism", "Имя", "Name"),
    'w_member_since': ("A'zo bo'lgan sana", "Дата регистрации", "Member since"),
    'w_loading': ("Yuklanmoqda...", "Загрузка...", "Loading..."),
    'w_remove': ("Olib tashlash", "Убрать", "Remove"),
}


def tr(lang, key, **kw):
    entry = S.get(key)
    if not entry:
        return key
    text = entry[LANGS.index(lang if lang in LANGS else DEFAULT_LANG)]
    return text.format(**kw) if kw else text


def variants(key):
    """Kalitning barcha tillardagi variantlari (tugma matnini filtrlash uchun)."""
    return set(S[key])


def web_dict(lang):
    i = LANGS.index(lang if lang in LANGS else DEFAULT_LANG)
    return {k: v[i] for k, v in S.items() if k.startswith('w_')}
