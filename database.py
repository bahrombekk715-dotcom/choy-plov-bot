import aiosqlite

from config import DB_PATH

TZ_OFFSET_HOURS = 5   # O'zbekiston (UTC+5): "bugun" shu vaqt bo'yicha hisoblanadi
MAX_IMAGES = 5
# (kod, nomi, bitta porsiya narxi, porsiya o'lchami). Mijoz har birini istalgancha ko'paytirib qo'sha oladi.
DEFAULT_ADDONS = [('meat', "Go'sht", 15000, '50 gr'), ('egg', 'Bedana tuxumi', 5000, '1 dona'), ('qazi', 'Qazi', 20000, '25 gr')]
LOCAL = f"DATE(o.created_at, '+{TZ_OFFSET_HOURS} hours')"


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        # Bot va web server alohida jarayonlar, bitta fayl: WAL va kutish vaqti kerak
        await self.db.execute('PRAGMA journal_mode=WAL')
        await self.db.execute('PRAGMA busy_timeout=5000')
        await self.db.execute('PRAGMA foreign_keys=ON')
        await self.create_tables()

    # ------------------------------------------------------------ sxema
    async def create_tables(self):
        await self.db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                phone_number TEXT NOT NULL,
                username TEXT,
                first_name TEXT,
                language TEXT DEFAULT 'uz',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                image_url TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_available BOOLEAN DEFAULT 1,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );
            CREATE TABLE IF NOT EXISTS product_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                position INTEGER DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            CREATE TABLE IF NOT EXISTS addons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                code TEXT,
                unit TEXT,
                is_available BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                phone_number TEXT NOT NULL,
                address TEXT NOT NULL,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                comment TEXT,
                admin_msg_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            CREATE TABLE IF NOT EXISTS order_addons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_item_id INTEGER NOT NULL,
                addon_id INTEGER NOT NULL,
                qty INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (order_item_id) REFERENCES order_items(id),
                FOREIGN KEY (addon_id) REFERENCES addons(id)
            );
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, product_id)
            );
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                address TEXT NOT NULL,
                is_default BOOLEAN DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id);
            CREATE INDEX IF NOT EXISTS idx_oaddons_item ON order_addons(order_item_id);
            CREATE INDEX IF NOT EXISTS idx_products_cat ON products(category_id, is_active);
            CREATE INDEX IF NOT EXISTS idx_images_product ON product_images(product_id, position);
        ''')
        await self._migrate()
        await self.seed_addons()
        await self.db.commit()

    async def _columns(self, table):
        cur = await self.db.execute(f'PRAGMA table_info({table})')
        return {r['name'] for r in await cur.fetchall()}

    async def _migrate(self):
        """Eski bazalarni yangilash (ma'lumot yo'qolmaydi)."""
        if 'language' not in await self._columns('users'):
            await self.db.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'uz'")
        cols = await self._columns('addons')
        if 'code' not in cols:
            await self.db.execute("ALTER TABLE addons ADD COLUMN code TEXT")
        if 'unit' not in cols:
            await self.db.execute("ALTER TABLE addons ADD COLUMN unit TEXT")
        if 'admin_msg_id' not in await self._columns('orders'):
            await self.db.execute("ALTER TABLE orders ADD COLUMN admin_msg_id INTEGER")
        if 'is_available' not in cols:
            await self.db.execute("ALTER TABLE addons ADD COLUMN is_available BOOLEAN DEFAULT 1")
        if 'qty' not in await self._columns('order_addons'):
            await self.db.execute("ALTER TABLE order_addons ADD COLUMN qty INTEGER NOT NULL DEFAULT 1")
        # Eski bitta rasm (image_url) -> galereyaga ko'chiriladi
        cur = await self.db.execute('''
            SELECT p.id, p.image_url FROM products p
            WHERE p.image_url IS NOT NULL AND p.image_url != ''
              AND NOT EXISTS (SELECT 1 FROM product_images i WHERE i.product_id = p.id)''')
        for r in await cur.fetchall():
            url = r['image_url'] if r['image_url'].startswith(('http', '/')) else f"/api/image/{r['image_url']}"
            await self.db.execute('INSERT INTO product_images (product_id, url, position) VALUES (?, ?, 0)', (r['id'], url))

    async def seed_addons(self):
        rows = await self._all('SELECT id, name, code, unit FROM addons ORDER BY id')
        if not rows:
            for code, name, price, unit in DEFAULT_ADDONS:
                await self.db.execute('INSERT INTO addons (name, price, code, unit) VALUES (?, ?, ?, ?)', (name, price, code, unit))
            return
        # eski bazada code/unit yo'q: dastlabki uchta qo'shimcha tartib bo'yicha to'ldiriladi
        for r, (code, name, _, unit) in zip(rows, DEFAULT_ADDONS):
            if not r['code']:
                await self.db.execute('UPDATE addons SET code = ? WHERE id = ?', (code, r['id']))
            if not r['unit']:
                await self.db.execute('UPDATE addons SET unit = ? WHERE id = ?', (unit, r['id']))
            if r['name'] == 'Tuxum':
                await self.db.execute('UPDATE addons SET name = ? WHERE id = ?', (name, r['id']))

    async def _all(self, sql, args=()):
        cur = await self.db.execute(sql, args)
        return await cur.fetchall()

    async def _one(self, sql, args=()):
        cur = await self.db.execute(sql, args)
        return await cur.fetchone()

    # ------------------------------------------------------------ foydalanuvchilar
    async def add_user(self, user_id, phone_number='', username=None, first_name=None, language=None):
        """Yaratadi yoki yangilaydi. Bo'sh telefon mavjud raqamni o'chirib yubormaydi."""
        existing = await self.get_user(user_id)
        lang = language or (existing['language'] if existing else 'uz')
        await self.db.execute(
            '''INSERT INTO users (user_id, phone_number, username, first_name, language) VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 phone_number = CASE WHEN excluded.phone_number != '' THEN excluded.phone_number ELSE users.phone_number END,
                 username=excluded.username, first_name=excluded.first_name, language=excluded.language''',
            (user_id, phone_number or '', username, first_name, lang))
        await self.db.commit()

    async def ensure_user(self, user_id, username=None, first_name=None, language='uz'):
        """Telegram ma'lumotlari bilan avtomatik ro'yxatdan o'tkazadi (telefon so'ralmaydi). Mavjud bo'lsa tegmaydi."""
        await self.db.execute(
            'INSERT OR IGNORE INTO users (user_id, phone_number, username, first_name, language) VALUES (?, \'\', ?, ?, ?)',
            (user_id, username, first_name, language))
        await self.db.commit()
        return await self.get_user(user_id)

    async def set_phone(self, user_id, phone):
        await self.db.execute('UPDATE users SET phone_number = ? WHERE user_id = ?', (phone, user_id))
        await self.db.commit()

    async def get_user(self, user_id):
        return await self._one('SELECT * FROM users WHERE user_id = ?', (user_id,))

    async def get_language(self, user_id):
        row = await self._one('SELECT language FROM users WHERE user_id = ?', (user_id,))
        return (row['language'] if row and row['language'] else 'uz')

    async def set_language(self, user_id, lang):
        await self.db.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))
        await self.db.commit()

    async def get_user_stats(self, user_id):
        r = await self._one(
            "SELECT COUNT(*) n, COALESCE(SUM(CASE WHEN status != 'cancelled' THEN total_price END), 0) spent, "
            "COALESCE(SUM(status IN ('completed', 'delivered')), 0) done FROM orders WHERE user_id = ?", (user_id,))
        return {'orders': r['n'], 'spent': r['spent'], 'completed': r['done']}

    # ------------------------------------------------------------ kategoriyalar
    async def add_category(self, name):
        cur = await self.db.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        await self.db.commit()
        return cur.lastrowid

    async def get_categories(self, active_only=True):
        if active_only:
            return await self._all('SELECT * FROM categories WHERE is_active = 1 ORDER BY id')
        return await self._all('SELECT * FROM categories ORDER BY id')

    async def get_categories_with_counts(self):
        return await self._all('''
            SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id = c.id AND p.is_active = 1) AS products_count
            FROM categories c WHERE c.is_active = 1 ORDER BY c.id''')

    async def get_category(self, category_id):
        return await self._one('SELECT * FROM categories WHERE id = ?', (category_id,))

    async def update_category(self, category_id, name):
        await self.db.execute('UPDATE categories SET name = ? WHERE id = ?', (name, category_id))
        await self.db.commit()

    async def delete_category(self, category_id):
        await self.db.execute('UPDATE categories SET is_active = 0 WHERE id = ?', (category_id,))
        await self.db.execute('UPDATE products SET is_active = 0 WHERE category_id = ?', (category_id,))
        await self.db.commit()

    # ------------------------------------------------------------ mahsulotlar
    async def add_product(self, category_id, name, price, description=None, image_url=None):
        cur = await self.db.execute(
            'INSERT INTO products (category_id, name, price, description) VALUES (?, ?, ?, ?)',
            (category_id, name, price, description))
        pid = cur.lastrowid
        await self.db.commit()
        if image_url:
            await self.add_product_image(pid, image_url)
        return pid

    async def attach_images(self, products):
        """Mahsulotlar ro'yxatiga `images` ([{id, url}]) va `image_url` (birinchisi) qo'shadi."""
        products = [dict(p) for p in products]
        if not products:
            return products
        ids = [p['id'] for p in products]
        marks = ','.join('?' * len(ids))
        rows = await self._all(
            f'SELECT id, product_id, url FROM product_images WHERE product_id IN ({marks}) ORDER BY position, id', ids)
        by = {}
        for r in rows:
            by.setdefault(r['product_id'], []).append({'id': r['id'], 'url': r['url']})
        for p in products:
            p['images'] = by.get(p['id'], [])
            p['image_url'] = p['images'][0]['url'] if p['images'] else None
        return products

    async def get_products_by_category(self, category_id, available_only=True):
        sql = 'SELECT * FROM products WHERE category_id = ? AND is_active = 1'
        if available_only:
            sql += ' AND is_available = 1'
        return await self._all(sql + ' ORDER BY id', (category_id,))

    async def get_all_products(self, active_only=True):
        sql = 'SELECT * FROM products' + (' WHERE is_active = 1' if active_only else '') + ' ORDER BY category_id, id'
        return await self._all(sql)

    async def get_product(self, product_id):
        return await self._one('SELECT * FROM products WHERE id = ?', (product_id,))

    async def update_product(self, product_id, name, price, description, category_id=None):
        if category_id is None:
            await self.db.execute('UPDATE products SET name=?, price=?, description=? WHERE id=?',
                                  (name, price, description, product_id))
        else:
            await self.db.execute('UPDATE products SET name=?, price=?, description=?, category_id=? WHERE id=?',
                                  (name, price, description, category_id, product_id))
        await self.db.commit()

    async def toggle_product_availability(self, product_id):
        await self.db.execute('UPDATE products SET is_available = NOT is_available WHERE id = ?', (product_id,))
        await self.db.commit()

    async def delete_product(self, product_id):
        await self.db.execute('UPDATE products SET is_active = 0 WHERE id = ?', (product_id,))
        await self.db.commit()

    # --- galereya
    async def count_product_images(self, product_id):
        return (await self._one('SELECT COUNT(*) n FROM product_images WHERE product_id = ?', (product_id,)))['n']

    async def add_product_image(self, product_id, url):
        """Galereyaga rasm qo'shadi. Limit (5 ta) to'lgan bo'lsa None qaytaradi."""
        if await self.count_product_images(product_id) >= MAX_IMAGES:
            return None
        pos = (await self._one('SELECT COALESCE(MAX(position), -1) + 1 p FROM product_images WHERE product_id = ?',
                               (product_id,)))['p']
        cur = await self.db.execute('INSERT INTO product_images (product_id, url, position) VALUES (?, ?, ?)',
                                    (product_id, url, pos))
        await self.db.commit()
        return cur.lastrowid

    async def get_image(self, image_id):
        return await self._one('SELECT * FROM product_images WHERE id = ?', (image_id,))

    async def delete_image(self, image_id):
        await self.db.execute('DELETE FROM product_images WHERE id = ?', (image_id,))
        await self.db.commit()

    # ------------------------------------------------------------ qo'shimchalar
    async def add_addon(self, name, price, unit=None, code=None):
        cur = await self.db.execute('INSERT INTO addons (name, price, unit, code) VALUES (?, ?, ?, ?)',
                                    (name, price, unit, code))
        await self.db.commit()
        return cur.lastrowid

    async def update_addon(self, addon_id, name, price, unit):
        await self.db.execute('UPDATE addons SET name = ?, price = ?, unit = ? WHERE id = ?', (name, price, unit, addon_id))
        await self.db.commit()

    async def delete_addon(self, addon_id):
        # eski buyurtmalarda ko'rinib turishi uchun o'chirilmaydi, faqat menyudan yashiriladi
        await self.db.execute('UPDATE addons SET is_active = 0 WHERE id = ?', (addon_id,))
        await self.db.commit()

    async def get_addons(self, active_only=True, available_only=True):
        """Menyu uchun: faqat yoqilganlari. Admin uchun available_only=False (o'chirib qo'yilganlari ham)."""
        sql = 'SELECT * FROM addons'
        where = []
        if active_only:
            where.append('is_active = 1')
        if available_only:
            where.append('is_available = 1')
        return await self._all(sql + (' WHERE ' + ' AND '.join(where) if where else '') + ' ORDER BY id')

    async def toggle_addon_availability(self, addon_id):
        await self.db.execute('UPDATE addons SET is_available = NOT is_available WHERE id = ?', (addon_id,))
        await self.db.commit()
        return bool((await self._one('SELECT is_available FROM addons WHERE id = ?', (addon_id,)))['is_available'])

    # ------------------------------------------------------------ buyurtmalar
    async def create_order_from_cart(self, user_id, phone, address, comment, cart):
        """Narxlar serverda bazadan hisoblanadi (mijoz yuborgan narxga ishonilmaydi).

        cart: [{product_id, quantity, addons: [{id, qty}, ...]}]   (addons: oddiy id ro'yxati ham qabul qilinadi)
        Qaytaradi: (order_id, total). Yaroqsiz bo'lsa ValueError.
        """
        addons = {a['id']: a for a in await self.get_addons()}
        lines, total = [], 0
        for item in cart:
            try:
                pid, qty = int(item['product_id']), int(item['quantity'])
            except (KeyError, TypeError, ValueError):
                raise ValueError('bad_item')
            if not 1 <= qty <= 50:
                raise ValueError('bad_quantity')
            product = await self.get_product(pid)
            if not product or not product['is_active'] or not product['is_available']:
                raise ValueError('unavailable')
            chosen = {}                                              # addon_id -> porsiyalar soni
            for entry in item.get('addons') or []:
                aid, aq = (entry['id'], entry.get('qty', 1)) if isinstance(entry, dict) else (entry, 1)
                if aid not in addons or not isinstance(aq, int) or not 1 <= aq <= 20:
                    raise ValueError('bad_addon')
                chosen[aid] = chosen.get(aid, 0) + aq
            if any(q > 20 for q in chosen.values()):
                raise ValueError('bad_addon')
            line = (product['price'] + sum(addons[i]['price'] * q for i, q in chosen.items())) * qty
            total += line
            lines.append((pid, qty, line, chosen))
        if not lines:
            raise ValueError('empty')

        cur = await self.db.execute(
            'INSERT INTO orders (user_id, phone_number, address, total_price, comment) VALUES (?, ?, ?, ?, ?)',
            (user_id, phone, address, total, comment))
        order_id = cur.lastrowid
        for pid, qty, line, chosen in lines:
            ic = await self.db.execute(
                'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                (order_id, pid, qty, line))
            for aid, aq in chosen.items():
                await self.db.execute('INSERT INTO order_addons (order_item_id, addon_id, qty) VALUES (?, ?, ?)',
                                      (ic.lastrowid, aid, aq))
        await self.db.commit()
        return order_id, total

    async def get_pending_orders(self):
        return await self._all("SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC")

    async def get_order(self, order_id):
        return await self._one('SELECT * FROM orders WHERE id = ?', (order_id,))

    async def get_order_items(self, order_id):
        return await self._all('''
            SELECT oi.*, p.name as product_name,
                   (SELECT url FROM product_images i WHERE i.product_id = oi.product_id ORDER BY i.position, i.id LIMIT 1) AS image_url
            FROM order_items oi JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?''', (order_id,))

    async def get_order_addons(self, order_item_id):
        return await self._all('''
            SELECT a.id, a.code, a.name, a.unit, a.price, oa.qty
            FROM order_addons oa JOIN addons a ON oa.addon_id = a.id
            WHERE oa.order_item_id = ?''', (order_item_id,))

    async def order_with_items(self, order):
        d = dict(order)
        d['items'] = []
        for it in await self.get_order_items(order['id']):
            i = dict(it)
            i['addons'] = [dict(a) for a in await self.get_order_addons(it['id'])]
            d['items'].append(i)
        return d

    async def set_admin_msg(self, order_id, message_id):
        """Adminning bot chatiga yuborilgan buyurtma xabari ID si (keyin holat o'zgarsa shu xabar yangilanadi)."""
        await self.db.execute('UPDATE orders SET admin_msg_id = ? WHERE id = ?', (message_id, order_id))
        await self.db.commit()

    async def update_order_status(self, order_id, status):
        await self.db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        await self.db.commit()

    async def get_user_orders(self, user_id, status=None, date_from=None, date_to=None):
        sql, args = 'SELECT o.* FROM orders o WHERE o.user_id = ?', [user_id]
        if status:
            sql += ' AND o.status = ?'; args.append(status)
        if date_from:
            sql += f' AND {LOCAL} >= ?'; args.append(date_from)
        if date_to:
            sql += f' AND {LOCAL} <= ?'; args.append(date_to)
        return await self._all(sql + ' ORDER BY o.created_at DESC, o.id DESC', args)

    # ------------------------------------------------------------ sevimlilar
    async def toggle_favorite(self, user_id, product_id):
        """Qo'shilsa True, olib tashlansa False."""
        row = await self._one('SELECT 1 FROM favorites WHERE user_id=? AND product_id=?', (user_id, product_id))
        if row:
            await self.db.execute('DELETE FROM favorites WHERE user_id=? AND product_id=?', (user_id, product_id))
        else:
            await self.db.execute('INSERT INTO favorites (user_id, product_id) VALUES (?, ?)', (user_id, product_id))
        await self.db.commit()
        return not row

    async def get_favorite_ids(self, user_id):
        return [r['product_id'] for r in await self._all('SELECT product_id FROM favorites WHERE user_id = ?', (user_id,))]

    async def get_favorites(self, user_id):
        return await self._all('''
            SELECT p.* FROM favorites f JOIN products p ON p.id = f.product_id
            WHERE f.user_id = ? AND p.is_active = 1 ORDER BY f.created_at DESC''', (user_id,))

    # ------------------------------------------------------------ manzillar
    async def get_addresses(self, user_id):
        return await self._all('SELECT * FROM addresses WHERE user_id = ? ORDER BY is_default DESC, id DESC', (user_id,))

    async def get_address(self, address_id, user_id):
        return await self._one('SELECT * FROM addresses WHERE id = ? AND user_id = ?', (address_id, user_id))

    async def save_address(self, user_id, title, address, is_default=False, address_id=None):
        has = await self._one('SELECT 1 FROM addresses WHERE user_id = ?', (user_id,))
        if not has:
            is_default = True            # birinchi manzil avtomatik asosiy
        if is_default:
            await self.db.execute('UPDATE addresses SET is_default = 0 WHERE user_id = ?', (user_id,))
        if address_id:
            await self.db.execute('UPDATE addresses SET title=?, address=?, is_default=? WHERE id=? AND user_id=?',
                                  (title, address, int(is_default), address_id, user_id))
            new_id = address_id
        else:
            cur = await self.db.execute(
                'INSERT INTO addresses (user_id, title, address, is_default) VALUES (?, ?, ?, ?)',
                (user_id, title, address, int(is_default)))
            new_id = cur.lastrowid
        await self.db.commit()
        return new_id

    async def make_default_address(self, address_id, user_id):
        await self.db.execute('UPDATE addresses SET is_default = 0 WHERE user_id = ?', (user_id,))
        await self.db.execute('UPDATE addresses SET is_default = 1 WHERE id = ? AND user_id = ?', (address_id, user_id))
        await self.db.commit()

    async def delete_address(self, address_id, user_id):
        await self.db.execute('DELETE FROM addresses WHERE id = ? AND user_id = ?', (address_id, user_id))
        if not await self._one('SELECT 1 FROM addresses WHERE user_id = ? AND is_default = 1', (user_id,)):
            await self.db.execute(
                'UPDATE addresses SET is_default = 1 WHERE id = (SELECT MAX(id) FROM addresses WHERE user_id = ?)', (user_id,))
        await self.db.commit()

    # ------------------------------------------------------------ admin: statistika
    async def get_today_stats(self):
        return await self._one(f'''
            SELECT COUNT(*) as total_orders,
                   SUM(total_price) as total_revenue,
                   SUM(CASE WHEN status IN ('completed', 'delivered') THEN total_price ELSE 0 END) as completed_revenue
            FROM orders o WHERE {LOCAL} = DATE('now', '+{TZ_OFFSET_HOURS} hours')''')

    async def admin_stats(self, days=14):
        days = max(1, min(int(days), 90))
        today = DATE_NOW = f"DATE('now', '+{TZ_OFFSET_HOURS} hours')"
        t = await self._one(f'''
            SELECT COUNT(*) orders,
                   COALESCE(SUM(CASE WHEN status != 'cancelled' THEN total_price END), 0) revenue,
                   COALESCE(SUM(status = 'pending'), 0) pending,
                   COALESCE(SUM({LOCAL} = {today}), 0) today_orders,
                   COALESCE(SUM(CASE WHEN {LOCAL} = {today} AND status != 'cancelled' THEN total_price END), 0) today_revenue
            FROM orders o''')
        users = (await self._one('SELECT COUNT(*) n FROM users'))['n']
        # Bo'sh kunlar ham 0 bilan chiqishi uchun kunlar ro'yxati rekursiv tuziladi
        daily = await self._all(f'''
            WITH RECURSIVE d(day, n) AS (
                SELECT DATE('now', '+{TZ_OFFSET_HOURS} hours', '-{days - 1} days'), 1
                UNION ALL SELECT DATE(day, '+1 day'), n + 1 FROM d WHERE n < {days})
            SELECT d.day AS date,
                   COALESCE(SUM(CASE WHEN o.status != 'cancelled' THEN o.total_price END), 0) AS revenue,
                   COUNT(o.id) AS orders
            FROM d LEFT JOIN orders o ON {LOCAL} = d.day
            GROUP BY d.day ORDER BY d.day''')
        st = {r['status']: r['n'] for r in await self._all('SELECT status, COUNT(*) n FROM orders GROUP BY status')}
        top = await self._all('''
            SELECT p.name, SUM(oi.quantity) qty FROM order_items oi
            JOIN orders o ON o.id = oi.order_id AND o.status != 'cancelled'
            JOIN products p ON p.id = oi.product_id
            GROUP BY p.id ORDER BY qty DESC LIMIT 6''')
        return {
            'totals': {**dict(t), 'users': users},
            'daily': [dict(r) for r in daily],
            'statuses': {k: st.get(k, 0) for k in ('pending', 'completed', 'delivered', 'cancelled')},
            'top_products': [dict(r) for r in top],
        }

    async def admin_orders(self, status=None, search=None, page=1, per_page=15):
        where, args = ['1=1'], []
        if status:
            where.append('o.status = ?'); args.append(status)
        if search:
            like = f'%{search}%'
            where.append('(o.phone_number LIKE ? OR u.first_name LIKE ? OR u.username LIKE ? OR CAST(o.id AS TEXT) = ?)')
            args += [like, like, like, search.lstrip('#')]
        w = ' AND '.join(where)
        total = (await self._one(f'SELECT COUNT(*) n FROM orders o LEFT JOIN users u ON u.user_id = o.user_id WHERE {w}', args))['n']
        rows = await self._all(f'''
            SELECT o.*, u.first_name, u.username FROM orders o LEFT JOIN users u ON u.user_id = o.user_id
            WHERE {w} ORDER BY o.created_at DESC, o.id DESC LIMIT ? OFFSET ?''', args + [per_page, (max(page, 1) - 1) * per_page])
        items = []
        for r in rows:
            d = await self.order_with_items(r)
            d['first_name'], d['username'] = r['first_name'], r['username']
            items.append(d)
        return {'items': items, 'total': total, 'per_page': per_page}

    async def admin_users(self, search=None, page=1, per_page=15):
        where, args = '1=1', []
        if search:
            like = f'%{search}%'
            where = '(u.first_name LIKE ? OR u.phone_number LIKE ? OR u.username LIKE ?)'
            args = [like, like, like]
        total = (await self._one(f'SELECT COUNT(*) n FROM users u WHERE {where}', args))['n']
        rows = await self._all(f'''
            SELECT u.*, COUNT(o.id) orders_count,
                   COALESCE(SUM(CASE WHEN o.status != 'cancelled' THEN o.total_price END), 0) spent
            FROM users u LEFT JOIN orders o ON o.user_id = u.user_id
            WHERE {where} GROUP BY u.user_id ORDER BY u.created_at DESC LIMIT ? OFFSET ?''',
                              args + [per_page, (max(page, 1) - 1) * per_page])
        return {'items': [dict(r) for r in rows], 'total': total, 'per_page': per_page}

    async def close(self):
        await self.db.close()
