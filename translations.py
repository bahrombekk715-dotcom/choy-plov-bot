# -*- coding: utf-8 -*-

TRANSLATIONS = {
    'uz': {
        # Asosiy xabarlar
        'welcome_admin': "👨‍💼 Assalomu alaykum, Admin!\n\nAdmin panelidan foydalaning:",
        'welcome_user': "👋 Xush kelibsiz, {name}!\n\n🍽 Buyurtma berish uchun 'Menyu' tugmasini bosing.",
        'welcome_new': "👋 Assalomu alaykum! Choy Plov botiga xush kelibsiz!\n\nDavom etish uchun telefon raqamingizni yuboring:",
        'phone_saved': "✅ Telefon raqamingiz saqlandi!\n\n🍽 Endi buyurtma berishingiz mumkin.",
        'use_buttons': "Quyidagi tugmalardan foydalaning:",
        'other_buttons': "Yoki quyidagi tugmalardan foydalaning:",

        # Tugmalar
        'btn_phone': "📱 Telefon raqamni yuborish",
        'btn_menu': "🍽 Menyu",
        'btn_my_orders': "📦 Mening buyurtmalarim",
        'btn_profile': "👤 Profil",
        'btn_back': "🔙 Ortga",
        'btn_cancel': "❌ Bekor qilish",
        'btn_confirm': "✅ Tasdiqlash",
        'btn_reject': "❌ Bekor qilish",
        'btn_language': "🌐 Til",

        # Admin tugmalari
        'btn_new_orders': "📋 Yangi buyurtmalar",
        'btn_today_stats': "📊 Bugungi statistika",
        'btn_add_product': "➕ Mahsulot qo'shish",
        'btn_add_image': "📸 Mahsulotga rasm qo'shish",
        'btn_toggle_product': "🔴 Mahsulotni to'xtatish/yoqish",
        'btn_delete_product': "🗑 Mahsulotni o'chirish",
        'btn_add_category': "📂 Kategoriya qo'shish",
        'btn_user_mode': "👤 Foydalanuvchi rejimi",
        'btn_back_admin': "🔙 Admin paneliga qaytish",

        # Menyu
        'open_menu': "🍽 Menyuni ko'rish va buyurtma berish uchun quyidagi tugmani bosing:",
        'btn_open_menu': "🍽 Menyuni ochish",

        # Buyurtmalar
        'no_orders': "📭 Sizda buyurtmalar yo'q.",
        'your_orders': "📦 Sizning buyurtmalaringiz ({count} ta):\n",
        'order_num': "Buyurtma #{id}",
        'order_time': "📅 Vaqt: {time}",
        'order_total': "💰 Summa: {price} so'm",
        'order_address': "📍 Manzil: {address}",
        'order_status': "📊 Status: {status}",
        'order_items': "\n\n📦 Mahsulotlar:",

        # Statuslar
        'status_pending': "⏳ Kutilmoqda",
        'status_completed': "✅ Tasdiqlandi",
        'status_cancelled': "❌ Bekor qilindi",
        'status_unknown': "Noma'lum",

        # Profil
        'profile_title': "👤 Profil\n",
        'profile_name': "📝 Ism: {name}",
        'profile_username': "🆔 Username: @{username}",
        'profile_phone': "📱 Telefon: {phone}",
        'profile_orders': "📦 Jami buyurtmalar: {count}",
        'profile_completed': "✅ Tasdiqlangan: {count}",
        'profile_registered': "📅 Ro'yxatdan o'tgan: {date}",
        'profile_not_found': "❌ Profil topilmadi.",

        # Admin - Yangi buyurtmalar
        'no_new_orders': "📭 Yangi buyurtmalar yo'q.",
        'new_orders_title': "📋 Yangi buyurtmalar ({count} ta):",
        'order_customer': "👤 Mijoz: {name}",
        'order_phone': "📱 Telefon: {phone}",
        'order_comment': "\n💬 Izoh: {comment}\n",
        'order_confirmed': "\n\n✅ Tasdiqlandi!",
        'order_rejected': "\n\n❌ Bekor qilindi!",

        # Xabarlar mijozga
        'order_approved': "✅ Buyurtmangiz #{id} tasdiqlandi!\n\n🚗 Yetkazib berish uchun tayyorlanmoqda...\nTez orada yetib boradi!",
        'order_rejected_msg': "❌ Buyurtmangiz #{id} bekor qilindi.\n\nIltimos, qo'shimcha ma'lumot uchun bog'laning.",

        # Statistika
        'stats_title': "📊 Bugungi statistika:\n",
        'stats_orders': "📦 Buyurtmalar soni: {count}",
        'stats_revenue': "💰 Umumiy savdo: {amount} so'm",
        'stats_completed': "✅ Tasdiqlangan: {amount} so'm",
        'stats_pending': "\n⏳ Kutilayotgan: {count} ta",

        # Kategoriya qo'shish
        'enter_category_name': "📝 Kategoriya nomini kiriting:",
        'category_added': "✅ '{name}' kategoriyasi qo'shildi!",
        'no_categories': "❌ Avval kategoriya qo'shing!",
        'select_category': "📂 Kategoriyani tanlang:\n",
        'category_not_found': "❌ Kategoriya topilmadi! Qaytadan kiriting:",

        # Mahsulot qo'shish
        'enter_product_name': "📝 Mahsulot nomini kiriting:",
        'enter_product_price': "💰 Narxini kiriting (faqat raqam):",
        'enter_product_desc': "📝 Tavsifini kiriting (yoki 'Yo'q' deb yozing):",
        'send_product_image': "📸 Mahsulot rasmini yuboring\n\n(Yoki 'Yo'q' deb yozing):",
        'product_added': "✅ '{name}' mahsuloti qo'shildi!\n💰 Narxi: {price} so'm",
        'image_added': "\n📸 Rasm qo'shildi",
        'invalid_format': "❌ Noto'g'ri format! Kategoriya raqamini kiriting:",
        'invalid_price': "❌ Noto'g'ri format! Faqat raqam kiriting:",

        # Rasm qo'shish
        'select_product': "📸 Mahsulotni tanlang:\n\n📸 = rasm mavjud\n📷 = rasm yo'q",
        'send_image_for': "📸 '{name}' uchun rasm yuboring:\n\n• Rasm fayli yuboring\n• Yoki rasm URL manzilini yuboring",
        'image_will_replace': "\n\n⚠️ Hozirgi rasm almashtiriladi",
        'send_image_or_url': "❌ Iltimos, rasm yoki URL yuboring!",
        'image_added_to': "✅ '{name}' mahsulotiga rasm qo'shildi!",

        # To'xtatish/Yoqish
        'select_product_toggle': "Mahsulotni tanlang:",
        'product_enabled': "🟢 Yoqildi",
        'product_disabled': "🔴 To'xtatildi",
        'no_products_in_cat': "Bu kategoriyada mahsulot yo'q!",

        # Umumiy
        'cancelled': "❌ Bekor qilindi.",
        'unknown': "Noma'lum",
        'user_mode_switched': "👤 Foydalanuvchi rejimiga o'tdingiz.",

        # Til tanlash
        'select_language': "🌐 Tilni tanlang / Выберите язык / Select language:",
        'language_changed': "✅ Til o'zgartirildi!",
    },

    'ru': {
        # Основные сообщения
        'welcome_admin': "👨‍💼 Здравствуйте, Админ!\n\nИспользуйте админ панель:",
        'welcome_user': "👋 Добро пожаловать, {name}!\n\n🍽 Нажмите 'Меню' чтобы сделать заказ.",
        'welcome_new': "👋 Здравствуйте! Добро пожаловать в бот Choy Plov!\n\nОтправьте ваш номер телефона для продолжения:",
        'phone_saved': "✅ Ваш номер телефона сохранен!\n\n🍽 Теперь вы можете делать заказы.",
        'use_buttons': "Используйте кнопки ниже:",
        'other_buttons': "Или используйте кнопки ниже:",

        # Кнопки
        'btn_phone': "📱 Отправить номер телефона",
        'btn_menu': "🍽 Меню",
        'btn_my_orders': "📦 Мои заказы",
        'btn_profile': "👤 Профиль",
        'btn_back': "🔙 Назад",
        'btn_cancel': "❌ Отмена",
        'btn_confirm': "✅ Подтвердить",
        'btn_reject': "❌ Отменить",
        'btn_language': "🌐 Язык",

        # Админ кнопки
        'btn_new_orders': "📋 Новые заказы",
        'btn_today_stats': "📊 Статистика за сегодня",
        'btn_add_product': "➕ Добавить продукт",
        'btn_add_image': "📸 Добавить фото к продукту",
        'btn_toggle_product': "🔴 Остановить/включить продукт",
        'btn_delete_product': "🗑 Удалить продукт",
        'btn_add_category': "📂 Добавить категорию",
        'btn_user_mode': "👤 Режим пользователя",
        'btn_back_admin': "🔙 Вернуться в админ панель",

        # Меню
        'open_menu': "🍽 Нажмите кнопку ниже чтобы открыть меню и сделать заказ:",
        'btn_open_menu': "🍽 Открыть меню",

        # Заказы
        'no_orders': "📭 У вас нет заказов.",
        'your_orders': "📦 Ваши заказы ({count} шт):\n",
        'order_num': "Заказ #{id}",
        'order_time': "📅 Время: {time}",
        'order_total': "💰 Сумма: {price} сум",
        'order_address': "📍 Адрес: {address}",
        'order_status': "📊 Статус: {status}",
        'order_items': "\n\n📦 Продукты:",

        # Статусы
        'status_pending': "⏳ Ожидается",
        'status_completed': "✅ Подтвержден",
        'status_cancelled': "❌ Отменен",
        'status_unknown': "Неизвестно",

        # Профиль
        'profile_title': "👤 Профиль\n",
        'profile_name': "📝 Имя: {name}",
        'profile_username': "🆔 Username: @{username}",
        'profile_phone': "📱 Телефон: {phone}",
        'profile_orders': "📦 Всего заказов: {count}",
        'profile_completed': "✅ Подтверждено: {count}",
        'profile_registered': "📅 Зарегистрирован: {date}",
        'profile_not_found': "❌ Профиль не найден.",

        # Админ - Новые заказы
        'no_new_orders': "📭 Нет новых заказов.",
        'new_orders_title': "📋 Новые заказы ({count} шт):",
        'order_customer': "👤 Клиент: {name}",
        'order_phone': "📱 Телефон: {phone}",
        'order_comment': "\n💬 Комментарий: {comment}\n",
        'order_confirmed': "\n\n✅ Подтверждено!",
        'order_rejected': "\n\n❌ Отменено!",

        # Сообщения клиенту
        'order_approved': "✅ Ваш заказ #{id} подтвержден!\n\n🚗 Готовится к доставке...\nСкоро будет доставлен!",
        'order_rejected_msg': "❌ Ваш заказ #{id} отменен.\n\nПожалуйста, свяжитесь для получения дополнительной информации.",

        # Статистика
        'stats_title': "📊 Статистика за сегодня:\n",
        'stats_orders': "📦 Количество заказов: {count}",
        'stats_revenue': "💰 Общие продажи: {amount} сум",
        'stats_completed': "✅ Подтверждено: {amount} сум",
        'stats_pending': "\n⏳ Ожидающих: {count} шт",

        # Добавить категорию
        'enter_category_name': "📝 Введите название категории:",
        'category_added': "✅ Категория '{name}' добавлена!",
        'no_categories': "❌ Сначала добавьте категорию!",
        'select_category': "📂 Выберите категорию:\n",
        'category_not_found': "❌ Категория не найдена! Введите снова:",

        # Добавить продукт
        'enter_product_name': "📝 Введите название продукта:",
        'enter_product_price': "💰 Введите цену (только цифры):",
        'enter_product_desc': "📝 Введите описание (или напишите 'Нет'):",
        'send_product_image': "📸 Отправьте фото продукта\n\n(Или напишите 'Нет'):",
        'product_added': "✅ Продукт '{name}' добавлен!\n💰 Цена: {price} сум",
        'image_added': "\n📸 Фото добавлено",
        'invalid_format': "❌ Неверный формат! Введите номер категории:",
        'invalid_price': "❌ Неверный формат! Введите только цифры:",

        # Добавить фото
        'select_product': "📸 Выберите продукт:\n\n📸 = есть фото\n📷 = нет фото",
        'send_image_for': "📸 Отправьте фото для '{name}':\n\n• Отправьте файл фото\n• Или отправьте URL фото",
        'image_will_replace': "\n\n⚠️ Текущее фото будет заменено",
        'send_image_or_url': "❌ Пожалуйста, отправьте фото или URL!",
        'image_added_to': "✅ Фото добавлено к продукту '{name}'!",

        # Остановить/Включить
        'select_product_toggle': "Выберите продукт:",
        'product_enabled': "🟢 Включено",
        'product_disabled': "🔴 Остановлено",
        'no_products_in_cat': "В этой категории нет продуктов!",

        # Общее
        'cancelled': "❌ Отменено.",
        'unknown': "Неизвестно",
        'user_mode_switched': "👤 Переключено на режим пользователя.",

        # Выбор языка
        'select_language': "🌐 Tilni tanlang / Выберите язык / Select language:",
        'language_changed': "✅ Язык изменен!",
    },

    'en': {
        # Main messages
        'welcome_admin': "👨‍💼 Hello, Admin!\n\nUse the admin panel:",
        'welcome_user': "👋 Welcome, {name}!\n\n🍽 Press 'Menu' to place an order.",
        'welcome_new': "👋 Hello! Welcome to Choy Plov bot!\n\nSend your phone number to continue:",
        'phone_saved': "✅ Your phone number has been saved!\n\n🍽 You can now place orders.",
        'use_buttons': "Use the buttons below:",
        'other_buttons': "Or use the buttons below:",

        # Buttons
        'btn_phone': "📱 Send phone number",
        'btn_menu': "🍽 Menu",
        'btn_my_orders': "📦 My orders",
        'btn_profile': "👤 Profile",
        'btn_back': "🔙 Back",
        'btn_cancel': "❌ Cancel",
        'btn_confirm': "✅ Confirm",
        'btn_reject': "❌ Reject",
        'btn_language': "🌐 Language",

        # Admin buttons
        'btn_new_orders': "📋 New orders",
        'btn_today_stats': "📊 Today's statistics",
        'btn_add_product': "➕ Add product",
        'btn_add_image': "📸 Add image to product",
        'btn_toggle_product': "🔴 Stop/enable product",
        'btn_delete_product': "🗑 Delete product",
        'btn_add_category': "📂 Add category",
        'btn_user_mode': "👤 User mode",
        'btn_back_admin': "🔙 Back to admin panel",

        # Menu
        'open_menu': "🍽 Press the button below to view menu and place an order:",
        'btn_open_menu': "🍽 Open menu",

        # Orders
        'no_orders': "📭 You have no orders.",
        'your_orders': "📦 Your orders ({count} items):\n",
        'order_num': "Order #{id}",
        'order_time': "📅 Time: {time}",
        'order_total': "💰 Total: {price} sum",
        'order_address': "📍 Address: {address}",
        'order_status': "📊 Status: {status}",
        'order_items': "\n\n📦 Products:",

        # Statuses
        'status_pending': "⏳ Pending",
        'status_completed': "✅ Confirmed",
        'status_cancelled': "❌ Cancelled",
        'status_unknown': "Unknown",

        # Profile
        'profile_title': "👤 Profile\n",
        'profile_name': "📝 Name: {name}",
        'profile_username': "🆔 Username: @{username}",
        'profile_phone': "📱 Phone: {phone}",
        'profile_orders': "📦 Total orders: {count}",
        'profile_completed': "✅ Completed: {count}",
        'profile_registered': "📅 Registered: {date}",
        'profile_not_found': "❌ Profile not found.",

        # Admin - New orders
        'no_new_orders': "📭 No new orders.",
        'new_orders_title': "📋 New orders ({count} items):",
        'order_customer': "👤 Customer: {name}",
        'order_phone': "📱 Phone: {phone}",
        'order_comment': "\n💬 Comment: {comment}\n",
        'order_confirmed': "\n\n✅ Confirmed!",
        'order_rejected': "\n\n❌ Rejected!",

        # Messages to customer
        'order_approved': "✅ Your order #{id} has been confirmed!\n\n🚗 Preparing for delivery...\nWill be delivered soon!",
        'order_rejected_msg': "❌ Your order #{id} has been cancelled.\n\nPlease contact us for more information.",

        # Statistics
        'stats_title': "📊 Today's statistics:\n",
        'stats_orders': "📦 Number of orders: {count}",
        'stats_revenue': "💰 Total sales: {amount} sum",
        'stats_completed': "✅ Completed: {amount} sum",
        'stats_pending': "\n⏳ Pending: {count} items",

        # Add category
        'enter_category_name': "📝 Enter category name:",
        'category_added': "✅ Category '{name}' has been added!",
        'no_categories': "❌ Add a category first!",
        'select_category': "📂 Select category:\n",
        'category_not_found': "❌ Category not found! Enter again:",

        # Add product
        'enter_product_name': "📝 Enter product name:",
        'enter_product_price': "💰 Enter price (numbers only):",
        'enter_product_desc': "📝 Enter description (or write 'No'):",
        'send_product_image': "📸 Send product image\n\n(Or write 'No'):",
        'product_added': "✅ Product '{name}' has been added!\n💰 Price: {price} sum",
        'image_added': "\n📸 Image added",
        'invalid_format': "❌ Invalid format! Enter category number:",
        'invalid_price': "❌ Invalid format! Enter numbers only:",

        # Add image
        'select_product': "📸 Select product:\n\n📸 = has image\n📷 = no image",
        'send_image_for': "📸 Send image for '{name}':\n\n• Send image file\n• Or send image URL",
        'image_will_replace': "\n\n⚠️ Current image will be replaced",
        'send_image_or_url': "❌ Please send an image or URL!",
        'image_added_to': "✅ Image added to product '{name}'!",

        # Toggle
        'select_product_toggle': "Select product:",
        'product_enabled': "🟢 Enabled",
        'product_disabled': "🔴 Disabled",
        'no_products_in_cat': "No products in this category!",

        # General
        'cancelled': "❌ Cancelled.",
        'unknown': "Unknown",
        'user_mode_switched': "👤 Switched to user mode.",

        # Language selection
        'select_language': "🌐 Tilni tanlang / Выберите язык / Select language:",
        'language_changed': "✅ Language changed!",
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    """Tilga mos matnni olish"""
    if lang not in TRANSLATIONS:
        lang = 'uz'  # Default til

    text = TRANSLATIONS[lang].get(key, TRANSLATIONS['uz'].get(key, key))

    # Format parametrlarini qo'llash
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass

    return text
