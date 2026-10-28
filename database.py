import asyncio
import datetime as dt
import logging
import re
from contextlib import asynccontextmanager

import asyncpg

from config import DATABASE_URL, TIMEZONE

logger = logging.getLogger(__name__)

_EMOJI = re.compile('[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2190-\u21FF\uFE0F\u200D\u20E3]+')


def clean_name(s):
    """Kategoriya va qo'shimcha nomlaridan emoji/stikerlarni olib tashlaydi."""
    return re.sub(r'\s{2,}', ' ', _EMOJI.sub('', s or '')).strip()


MAX_IMAGES = 5
# (kod, nomi, bitta porsiya narxi, porsiya o'lchami). Mijoz har birini istalgancha ko'paytirib qo'sha oladi.
DEFAULT_ADDONS = [('meat', "Go'sht", 15000, '50 gr'), ('egg', 'Bedana tuxumi', 5000, '1 dona'), ('qazi', 'Qazi', 20000, '25 gr')]

# "Bugun" va kunlik hisobotlar shu vaqt zonasi bo'yicha (standart: O'zbekiston, UTC+5)
LOCAL = f"(o.created_at AT TIME ZONE '{TIMEZONE}')::date"
TODAY = f"(now() AT TIME ZONE '{TIMEZONE}')::date"

LOCK_ID = 727001   # sxema yaratilayotganda bot va web jarayonlari bir-biriga xalaqit bermasligi uchun


def _q(sql):
    """`?` belgilarini PostgreSQL `$1, $2, ...` ga aylantiradi."""
    n = 0

    def rep(_):
        nonlocal n
        n += 1
        return f'${n}'
    return re.sub(r'\?', rep, sql)


def _py(v):
    """Vaqtni avvalgidek 'YYYY-MM-DD HH:MM:SS' (UTC) matniga aylantiradi: sayt va bot shu formatni kutadi."""
    if isinstance(v, dt.datetime):
        if v.tzinfo is not None:
            v = v.astimezone(dt.timezone.utc)
        return v.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(v, dt.date):
        return v.isoformat()
    return v


def _row(r):
    return {k: _py(v) for k, v in r.items()}


def _date(s):
    try:
        return dt.date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


class Database:
    def __init__(self, dsn=None):
        self.dsn = dsn or DATABASE_URL
        self.pool = None

    async def connect(self, retries=15):
        """Baza hali ishga tushmagan bo'lsa (masalan, docker'da) bir necha marta qayta urinadi."""
        for attempt in range(1, retries + 1):
            try:
                self.pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=10, command_timeout=30)
                break
            except (OSError, asyncpg.PostgresError, asyncio.TimeoutError) as e:
                if attempt == retries:
                    raise
                logger.warning('PostgreSQL ga ulanib bo\'lmadi (%s/%s): %s', attempt, retries, e)
                await asyncio.sleep(2)
        await self.create_tables()

    async def close(self):
        if self.pool:
            await self.pool.close()

    # ------------------------------------------------------------ yordamchilar
    async def _all(self, sql, args=(), conn=None):
        try:
            rows = await (conn or self.pool).fetch(_q(sql), *args)
        except asyncpg.DataError:        # masalan, int32 dan katta id: "topilmadi" deb hisoblanadi
            return []
        return [_row(r) for r in rows]

    async def _one(self, sql, args=(), conn=None):
        try:
            r = await (conn or self.pool).fetchrow(_q(sql), *args)
        except asyncpg.DataError:
            return None
        return _row(r) if r else None

    async def _val(self, sql, args=(), conn=None):
        try:
            return await (conn or self.pool).fetchval(_q(sql), *args)
        except asyncpg.DataError:
            return None

    async def _exec(self, sql, args=(), conn=None):
        try:
            return await (conn or self.pool).execute(_q(sql), *args)
        except asyncpg.DataError:
            return None

    @asynccontextmanager
    async def _tx(self):
        """Bir nechta so'rovni bitta tranzaksiyada bajaradi (xato bo'lsa hammasi bekor qilinadi)."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    # ------------------------------------------------------------ sxema
    SCHEMA = '''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            phone_number TEXT NOT NULL DEFAULT '',
            username TEXT,
            first_name TEXT,
            language TEXT DEFAULT 'uz',
            lat DOUBLE PRECISION,
            lon DOUBLE PRECISION,
            location_address TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        );
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            name TEXT NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            description TEXT,
            image_url TEXT,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_available BOOLEAN NOT NULL DEFAULT TRUE
        );
        CREATE TABLE IF NOT EXISTS product_images (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(id),
            url TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS addons (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            code TEXT,
            unit TEXT,
            is_available BOOLEAN NOT NULL DEFAULT TRUE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        );
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(user_id),
            phone_number TEXT NOT NULL,
            address TEXT NOT NULL,
            total_price DOUBLE PRECISION NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            comment TEXT,
            lat DOUBLE PRECISION,
            lon DOUBLE PRECISION,
            admin_msg_id BIGINT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            price DOUBLE PRECISION NOT NULL
        );
        CREATE TABLE IF NOT EXISTS order_addons (
            id SERIAL PRIMARY KEY,
            order_item_id INTEGER NOT NULL REFERENCES order_items(id),
            addon_id INTEGER NOT NULL REFERENCES addons(id),
            qty INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS product_addons (
            product_id INTEGER NOT NULL,
            addon_id INTEGER NOT NULL,
            PRIMARY KEY (product_id, addon_id)
        );
        CREATE TABLE IF NOT EXISTS favorites (
            user_id BIGINT NOT NULL,
            product_id INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (user_id, product_id)
        );
        CREATE TABLE IF NOT EXISTS addresses (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            title TEXT NOT NULL,
            address TEXT NOT NULL,
            is_default BOOLEAN NOT NULL DEFAULT FALSE,
            lat DOUBLE PRECISION,
            lon DOUBLE PRECISION
        );
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
        CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id);
        CREATE INDEX IF NOT EXISTS idx_oaddons_item ON order_addons(order_item_id);
        CREATE INDEX IF NOT EXISTS idx_products_cat ON products(category_id, is_active);
        CREATE INDEX IF NOT EXISTS idx_images_product ON product_images(product_id, position);
        CREATE INDEX IF NOT EXISTS idx_addresses_user ON addresses(user_id);
    '''

    async def create_tables(self):
        async with self.pool.acquire() as c:
            await c.execute('SELECT pg_advisory_lock($1)', LOCK_ID)
            try:
                await c.execute(self.SCHEMA)
                await self.seed_addons(c)
                await self._seed_product_addons(c)
                await self._migrate_legacy_images(c)
            finally:
                await c.execute('SELECT pg_advisory_unlock($1)', LOCK_ID)

    async def _migrate_legacy_images(self, c):
        """Eski bitta rasm (image_url) -> galereyaga ko'chiriladi."""
        rows = await self._all('''
            SELECT p.id, p.image_url FROM products p
            WHERE p.image_url IS NOT NULL AND p.image_url != ''
              AND NOT EXISTS (SELECT 1 FROM product_images i WHERE i.product_id = p.id)''', conn=c)
        for r in rows:
            url = r['image_url'] if r['image_url'].startswith(('http', '/')) else f"/api/image/{r['image_url']}"
            await self._exec('INSERT INTO product_images (product_id, url, position) VALUES (?, ?, 0)', (r['id'], url), conn=c)

    async def seed_addons(self, c):
        rows = await self._all('SELECT id, name, code, unit FROM addons ORDER BY id', conn=c)
        if not rows:
            for code, name, price, unit in DEFAULT_ADDONS:
                await self._exec('INSERT INTO addons (name, price, code, unit) VALUES (?, ?, ?, ?)', (name, price, code, unit), conn=c)
            return
        # code/unit bo'sh bo'lsa (eski ma'lumot), dastlabki uchta qo'shimcha tartib bo'yicha to'ldiriladi
        for r, (code, name, _, unit) in zip(rows, DEFAULT_ADDONS):
            if not r['code']:
                await self._exec('UPDATE addons SET code = ? WHERE id = ?', (code, r['id']), conn=c)
            if not r['unit']:
                await self._exec('UPDATE addons SET unit = ? WHERE id = ?', (unit, r['id']), conn=c)
            if r['name'] == 'Tuxum':
                await self._exec('UPDATE addons SET name = ? WHERE id = ?', (name, r['id']), conn=c)

    async def _seed_product_addons(self, c):
        """Bir martalik: qo'shimchalar mahsulotga bog'lanadigan bo'lishidan oldin hamma mahsulotda hamma qo'shimcha bor edi.
        Yangi bazada mahsulot yo'q, shuning uchun hech narsa bog'lanmaydi; belgi qo'yiladi va qayta bajarilmaydi."""
        ver = await self._val("SELECT value FROM meta WHERE key = 'schema_version'", conn=c)
        if ver is None:
            await self._exec('''INSERT INTO product_addons (product_id, addon_id)
                                SELECT p.id, a.id FROM products p CROSS JOIN addons a WHERE a.is_active
                                ON CONFLICT DO NOTHING''', conn=c)
            await self._exec("INSERT INTO meta (key, value) VALUES ('schema_version', '1') ON CONFLICT (key) DO NOTHING", conn=c)
        # mavjud kategoriya/qo'shimcha nomlaridagi emojilarni tozalaymiz
        for tbl, cols in (('categories', ('name',)), ('addons', ('name', 'unit'))):
            for r in await self._all(f'SELECT id, {", ".join(cols)} FROM {tbl}', conn=c):
                for col in cols:
                    if r[col] and clean_name(r[col]) != r[col]:
                        new = clean_name(r[col])
                        if col == 'unit':
                            new = new or None
                        await self._exec(f'UPDATE {tbl} SET {col} = ? WHERE id = ?', (new, r['id']), conn=c)

    # ------------------------------------------------------------ foydalanuvchilar
    async def add_user(self, user_id, phone_number='', username=None, first_name=None, language=None):
        """Yaratadi yoki yangilaydi. Bo'sh telefon mavjud raqamni o'chirib yubormaydi."""
        existing = await self.get_user(user_id)
        lang = language or (existing['language'] if existing else 'uz')
        await self._exec(
            '''INSERT INTO users (user_id, phone_number, username, first_name, language) VALUES (?, ?, ?, ?, ?)
               ON CONFLICT (user_id) DO UPDATE SET
                 phone_number = CASE WHEN EXCLUDED.phone_number != '' THEN EXCLUDED.phone_number ELSE users.phone_number END,
                 username = EXCLUDED.username, first_name = EXCLUDED.first_name, language = EXCLUDED.language''',
            (user_id, phone_number or '', username, first_name, lang))

    async def ensure_user(self, user_id, username=None, first_name=None, language='uz'):
        """Telegram ma'lumotlari bilan avtomatik ro'yxatdan o'tkazadi (telefon so'ralmaydi). Mavjud bo'lsa tegmaydi."""
        await self._exec(
            "INSERT INTO users (user_id, phone_number, username, first_name, language) VALUES (?, '', ?, ?, ?) "
            "ON CONFLICT (user_id) DO NOTHING",
            (user_id, username, first_name, language))
        return await self.get_user(user_id)

    async def set_phone(self, user_id, phone):
        await self._exec('UPDATE users SET phone_number = ? WHERE user_id = ?', (phone, user_id))

    async def set_location(self, user_id, lat, lon, address=None):
        await self._exec('UPDATE users SET lat = ?, lon = ?, location_address = ? WHERE user_id = ?',
                         (lat, lon, address, user_id))

    async def get_user(self, user_id):
        return await self._one('SELECT * FROM users WHERE user_id = ?', (user_id,))

    async def get_language(self, user_id):
        row = await self._one('SELECT language FROM users WHERE user_id = ?', (user_id,))
        return (row['language'] if row and row['language'] else 'uz')

    async def set_language(self, user_id, lang):
        await self._exec('UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))

    async def get_user_stats(self, user_id):
        r = await self._one(
            "SELECT COUNT(*) AS n, COALESCE(SUM(CASE WHEN status != 'cancelled' THEN total_price END), 0) AS spent, "
            "COUNT(*) FILTER (WHERE status IN ('completed', 'delivered')) AS done FROM orders WHERE user_id = ?", (user_id,))
        return {'orders': r['n'], 'spent': r['spent'], 'completed': r['done']}

    # ------------------------------------------------------------ kategoriyalar
    async def add_category(self, name):
        name = clean_name(name)
        return await self._val('INSERT INTO categories (name) VALUES (?) RETURNING id', (name,))

    async def get_categories(self, active_only=True):
        if active_only:
            return await self._all('SELECT * FROM categories WHERE is_active = TRUE ORDER BY id')
        return await self._all('SELECT * FROM categories ORDER BY id')

    async def get_categories_with_counts(self):
        return await self._all('''
            SELECT c.*, (SELECT COUNT(*) FROM products p WHERE p.category_id = c.id AND p.is_active = TRUE) AS products_count
            FROM categories c WHERE c.is_active = TRUE ORDER BY c.id''')

    async def get_category(self, category_id):
        return await self._one('SELECT * FROM categories WHERE id = ?', (category_id,))

    async def update_category(self, category_id, name):
        await self._exec('UPDATE categories SET name = ? WHERE id = ?', (clean_name(name), category_id))

    async def delete_category(self, category_id):
        async with self._tx() as c:
            await self._exec('UPDATE categories SET is_active = FALSE WHERE id = ?', (category_id,), conn=c)
            await self._exec('UPDATE products SET is_active = FALSE WHERE category_id = ?', (category_id,), conn=c)

    # ------------------------------------------------------------ mahsulotlar
    async def add_product(self, category_id, name, price, description=None, image_url=None):
        pid = await self._val(
            'INSERT INTO products (category_id, name, price, description) VALUES (?, ?, ?, ?) RETURNING id',
            (category_id, name, price, description))
        if image_url:
            await self.add_product_image(pid, image_url)
        return pid

    async def attach_images(self, products):
        """Mahsulotlar ro'yxatiga `images` ([{id, url}]) va `image_url` (birinchisi) qo'shadi."""
        products = [dict(p) for p in products]
        if not products:
            return products
        ids = [p['id'] for p in products]
        rows = await self._all(
            'SELECT id, product_id, url FROM product_images WHERE product_id = ANY(?::int[]) ORDER BY position, id', (ids,))
        by = {}
        for r in rows:
            by.setdefault(r['product_id'], []).append({'id': r['id'], 'url': r['url']})
        for p in products:
            p['images'] = by.get(p['id'], [])
            p['image_url'] = p['images'][0]['url'] if p['images'] else None
        return products

    async def attach_addon_ids(self, products):
        """Mahsulot lug'atlariga `addon_ids` (shu mahsulotga qo'shiladigan qo'shimchalar) qo'shadi."""
        by = {}
        for r in await self._all('SELECT product_id, addon_id FROM product_addons ORDER BY addon_id'):
            by.setdefault(r['product_id'], []).append(r['addon_id'])
        for p in products:
            p['addon_ids'] = by.get(p['id'], [])
        return products

    async def set_product_addons(self, product_id, addon_ids):
        async with self._tx() as c:
            await self._exec('DELETE FROM product_addons WHERE product_id = ?', (product_id,), conn=c)
            for aid in dict.fromkeys(addon_ids):
                await self._exec('INSERT INTO product_addons (product_id, addon_id) VALUES (?, ?) ON CONFLICT DO NOTHING',
                                 (product_id, aid), conn=c)

    async def set_addon_products(self, addon_id, product_ids):
        async with self._tx() as c:
            await self._exec('DELETE FROM product_addons WHERE addon_id = ?', (addon_id,), conn=c)
            for pid in dict.fromkeys(product_ids):
                await self._exec('INSERT INTO product_addons (product_id, addon_id) VALUES (?, ?) ON CONFLICT DO NOTHING',
                                 (pid, addon_id), conn=c)

    async def get_addon_product_ids(self, addon_id):
        return [r['product_id'] for r in await self._all('SELECT product_id FROM product_addons WHERE addon_id = ?', (addon_id,))]

    async def get_products_by_category(self, category_id, available_only=True):
        sql = 'SELECT * FROM products WHERE category_id = ? AND is_active = TRUE'
        if available_only:
            sql += ' AND is_available = TRUE'
        return await self._all(sql + ' ORDER BY id', (category_id,))

    async def get_all_products(self, active_only=True):
        sql = 'SELECT * FROM products' + (' WHERE is_active = TRUE' if active_only else '') + ' ORDER BY category_id, id'
        return await self._all(sql)

    async def get_product(self, product_id):
        return await self._one('SELECT * FROM products WHERE id = ?', (product_id,))

    async def update_product(self, product_id, name, price, description, category_id=None):
        if category_id is None:
            await self._exec('UPDATE products SET name = ?, price = ?, description = ? WHERE id = ?',
                             (name, price, description, product_id))
        else:
            await self._exec('UPDATE products SET name = ?, price = ?, description = ?, category_id = ? WHERE id = ?',
                             (name, price, description, category_id, product_id))

    async def toggle_product_availability(self, product_id):
        await self._exec('UPDATE products SET is_available = NOT is_available WHERE id = ?', (product_id,))

    async def delete_product(self, product_id):
        await self._exec('UPDATE products SET is_active = FALSE WHERE id = ?', (product_id,))

    # --- galereya
    async def count_product_images(self, product_id):
        return await self._val('SELECT COUNT(*) FROM product_images WHERE product_id = ?', (product_id,)) or 0

    async def add_product_image(self, product_id, url):
        """Galereyaga rasm qo'shadi. Limit (5 ta) to'lgan bo'lsa None qaytaradi."""
        async with self._tx() as c:
            if (await self._val('SELECT COUNT(*) FROM product_images WHERE product_id = ?', (product_id,), conn=c) or 0) >= MAX_IMAGES:
                return None
            pos = await self._val('SELECT COALESCE(MAX(position), -1) + 1 FROM product_images WHERE product_id = ?',
                                  (product_id,), conn=c)
            return await self._val('INSERT INTO product_images (product_id, url, position) VALUES (?, ?, ?) RETURNING id',
                                   (product_id, url, pos), conn=c)

    async def get_image(self, image_id):
        return await self._one('SELECT * FROM product_images WHERE id = ?', (image_id,))

    async def delete_image(self, image_id):
        await self._exec('DELETE FROM product_images WHERE id = ?', (image_id,))

    # ------------------------------------------------------------ qo'shimchalar
    async def add_addon(self, name, price, unit=None, code=None):
        name, unit = clean_name(name), clean_name(unit) or None
        return await self._val('INSERT INTO addons (name, price, unit, code) VALUES (?, ?, ?, ?) RETURNING id',
                               (name, price, unit, code))

    async def update_addon(self, addon_id, name, price, unit):
        name, unit = clean_name(name), clean_name(unit) or None
        await self._exec('UPDATE addons SET name = ?, price = ?, unit = ? WHERE id = ?', (name, price, unit, addon_id))

    async def delete_addon(self, addon_id):
        # eski buyurtmalarda ko'rinib turishi uchun o'chirilmaydi, faqat menyudan yashiriladi
        await self._exec('UPDATE addons SET is_active = FALSE WHERE id = ?', (addon_id,))

    async def get_addons(self, active_only=True, available_only=True):
        """Menyu uchun: faqat yoqilganlari. Admin uchun available_only=False (o'chirib qo'yilganlari ham)."""
        sql = 'SELECT * FROM addons'
        where = []
        if active_only:
            where.append('is_active = TRUE')
        if available_only:
            where.append('is_available = TRUE')
        return await self._all(sql + (' WHERE ' + ' AND '.join(where) if where else '') + ' ORDER BY id')

    async def toggle_addon_availability(self, addon_id):
        return bool(await self._val('UPDATE addons SET is_available = NOT is_available WHERE id = ? RETURNING is_available',
                                    (addon_id,)))

    # ------------------------------------------------------------ buyurtmalar
    async def _price_cart(self, cart, lenient=False):
        """Savatni serverda narxlaydi. lenient=True (admin tahriri): mavjudlik tekshirilmaydi."""
        addons = {a['id']: a for a in await self.get_addons(active_only=not lenient, available_only=not lenient)}
        lines, total = [], 0
        for item in cart:
            try:
                pid, qty = int(item['product_id']), int(item['quantity'])
            except (KeyError, TypeError, ValueError):
                raise ValueError('bad_item')
            if not 1 <= qty <= 50:
                raise ValueError('bad_quantity')
            product = await self.get_product(pid)
            if not product or (not lenient and (not product['is_active'] or not product['is_available'])):
                raise ValueError('unavailable')
            allowed = {r['addon_id'] for r in await self._all('SELECT addon_id FROM product_addons WHERE product_id = ?', (pid,))}
            chosen = {}                                              # addon_id -> porsiyalar soni
            for entry in item.get('addons') or []:
                aid, aq = (entry['id'], entry.get('qty', 1)) if isinstance(entry, dict) else (entry, 1)
                if aid not in addons or (not lenient and aid not in allowed) or not isinstance(aq, int) or not 1 <= aq <= 20:
                    raise ValueError('bad_addon')
                chosen[aid] = chosen.get(aid, 0) + aq
            if any(q > 20 for q in chosen.values()):
                raise ValueError('bad_addon')
            line = (product['price'] + sum(addons[i]['price'] * q for i, q in chosen.items())) * qty
            total += line
            lines.append((pid, qty, line, chosen))
        if not lines:
            raise ValueError('empty')
        return lines, total

    async def _insert_lines(self, order_id, lines, conn):
        for pid, qty, line, chosen in lines:
            item_id = await self._val(
                'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?) RETURNING id',
                (order_id, pid, qty, line), conn=conn)
            for aid, aq in chosen.items():
                await self._exec('INSERT INTO order_addons (order_item_id, addon_id, qty) VALUES (?, ?, ?)',
                                 (item_id, aid, aq), conn=conn)

    async def create_order_from_cart(self, user_id, phone, address, comment, cart, lat=None, lon=None):
        """Narxlar serverda bazadan hisoblanadi (mijoz yuborgan narxga ishonilmaydi).

        cart: [{product_id, quantity, addons: [{id, qty}, ...]}]   (addons: oddiy id ro'yxati ham qabul qilinadi)
        lat/lon: mijoz yuborgan lokatsiya (ixtiyoriy). Qaytaradi: (order_id, total). Yaroqsiz bo'lsa ValueError.
        """
        lines, total = await self._price_cart(cart)
        async with self._tx() as c:
            order_id = await self._val(
                'INSERT INTO orders (user_id, phone_number, address, total_price, comment, lat, lon) '
                'VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id',
                (user_id, phone, address, total, comment, lat, lon), conn=c)
            await self._insert_lines(order_id, lines, c)
        return order_id, total

    async def replace_order_items(self, order_id, cart):
        """Admin tasdiqlashdan oldin buyurtma tarkibini o'zgartiradi (qo'shadi/olib tashlaydi). Faqat 'pending'. Yangi jami qaytadi."""
        async with self._tx() as c:
            order = await self._one('SELECT * FROM orders WHERE id = ? FOR UPDATE', (order_id,), conn=c)
            if not order or order['status'] != 'pending':
                raise ValueError('not_pending')
            lines, total = await self._price_cart(cart, lenient=True)
            await self._exec('DELETE FROM order_addons WHERE order_item_id IN (SELECT id FROM order_items WHERE order_id = ?)',
                             (order_id,), conn=c)
            await self._exec('DELETE FROM order_items WHERE order_id = ?', (order_id,), conn=c)
            await self._insert_lines(order_id, lines, c)
            await self._exec('UPDATE orders SET total_price = ? WHERE id = ?', (total, order_id), conn=c)
        return total

    async def cancel_user_order(self, order_id, user_id):
        """Mijoz faqat tasdiqlanmagan ('pending') buyurtmani bekor qila oladi. Muvaffaqiyatli bo'lsa True."""
        row = await self._val("UPDATE orders SET status = 'cancelled' WHERE id = ? AND user_id = ? AND status = 'pending' RETURNING id",
                              (order_id, user_id))
        return row is not None

    async def get_pending_orders(self):
        return await self._all("SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC")

    async def get_order(self, order_id):
        return await self._one('SELECT * FROM orders WHERE id = ?', (order_id,))

    async def get_order_items(self, order_id):
        return await self._all('''
            SELECT oi.*, p.name AS product_name,
                   (SELECT url FROM product_images i WHERE i.product_id = oi.product_id ORDER BY i.position, i.id LIMIT 1) AS image_url
            FROM order_items oi JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ? ORDER BY oi.id''', (order_id,))

    async def get_order_addons(self, order_item_id):
        return await self._all('''
            SELECT a.id, a.code, a.name, a.unit, a.price, oa.qty
            FROM order_addons oa JOIN addons a ON oa.addon_id = a.id
            WHERE oa.order_item_id = ? ORDER BY oa.id''', (order_item_id,))

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
        await self._exec('UPDATE orders SET admin_msg_id = ? WHERE id = ?', (message_id, order_id))

    async def update_order_status(self, order_id, status):
        await self._exec('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))

    async def get_user_orders(self, user_id, status=None, date_from=None, date_to=None):
        sql, args = 'SELECT o.* FROM orders o WHERE o.user_id = ?', [user_id]
        if status:
            sql += ' AND o.status = ?'; args.append(status)
        if _date(date_from):
            sql += f' AND {LOCAL} >= ?'; args.append(_date(date_from))
        if _date(date_to):
            sql += f' AND {LOCAL} <= ?'; args.append(_date(date_to))
        return await self._all(sql + ' ORDER BY o.created_at DESC, o.id DESC', args)

    # ------------------------------------------------------------ sevimlilar
    async def toggle_favorite(self, user_id, product_id):
        """Qo'shilsa True, olib tashlansa False."""
        async with self._tx() as c:
            exists = await self._val('SELECT 1 FROM favorites WHERE user_id = ? AND product_id = ?', (user_id, product_id), conn=c)
            if exists:
                await self._exec('DELETE FROM favorites WHERE user_id = ? AND product_id = ?', (user_id, product_id), conn=c)
            else:
                await self._exec('INSERT INTO favorites (user_id, product_id) VALUES (?, ?) ON CONFLICT DO NOTHING',
                                 (user_id, product_id), conn=c)
            return not exists

    async def get_favorite_ids(self, user_id):
        return [r['product_id'] for r in await self._all('SELECT product_id FROM favorites WHERE user_id = ?', (user_id,))]

    async def get_favorites(self, user_id):
        return await self._all('''
            SELECT p.* FROM favorites f JOIN products p ON p.id = f.product_id
            WHERE f.user_id = ? AND p.is_active = TRUE ORDER BY f.created_at DESC''', (user_id,))

    # ------------------------------------------------------------ manzillar
    async def get_addresses(self, user_id):
        return await self._all('SELECT * FROM addresses WHERE user_id = ? ORDER BY is_default DESC, id DESC', (user_id,))

    async def get_address(self, address_id, user_id):
        return await self._one('SELECT * FROM addresses WHERE id = ? AND user_id = ?', (address_id, user_id))

    async def save_address(self, user_id, title, address, is_default=False, address_id=None, lat=None, lon=None):
        async with self._tx() as c:
            has = await self._val('SELECT 1 FROM addresses WHERE user_id = ?', (user_id,), conn=c)
            if not has:
                is_default = True            # birinchi manzil avtomatik asosiy
            if is_default:
                await self._exec('UPDATE addresses SET is_default = FALSE WHERE user_id = ?', (user_id,), conn=c)
            if address_id:
                await self._exec('UPDATE addresses SET title = ?, address = ?, is_default = ?, lat = ?, lon = ? WHERE id = ? AND user_id = ?',
                                 (title, address, bool(is_default), lat, lon, address_id, user_id), conn=c)
                return address_id
            return await self._val(
                'INSERT INTO addresses (user_id, title, address, is_default, lat, lon) VALUES (?, ?, ?, ?, ?, ?) RETURNING id',
                (user_id, title, address, bool(is_default), lat, lon), conn=c)

    async def make_default_address(self, address_id, user_id):
        async with self._tx() as c:
            await self._exec('UPDATE addresses SET is_default = FALSE WHERE user_id = ?', (user_id,), conn=c)
            await self._exec('UPDATE addresses SET is_default = TRUE WHERE id = ? AND user_id = ?', (address_id, user_id), conn=c)

    async def delete_address(self, address_id, user_id):
        async with self._tx() as c:
            await self._exec('DELETE FROM addresses WHERE id = ? AND user_id = ?', (address_id, user_id), conn=c)
            if not await self._val('SELECT 1 FROM addresses WHERE user_id = ? AND is_default = TRUE', (user_id,), conn=c):
                await self._exec(
                    'UPDATE addresses SET is_default = TRUE WHERE id = (SELECT MAX(id) FROM addresses WHERE user_id = ?)',
                    (user_id,), conn=c)

    # ------------------------------------------------------------ admin: statistika
    async def get_today_stats(self):
        return await self._one(f'''
            SELECT COUNT(*) AS total_orders,
                   SUM(total_price) AS total_revenue,
                   SUM(CASE WHEN status IN ('completed', 'delivered') THEN total_price ELSE 0 END) AS completed_revenue
            FROM orders o WHERE {LOCAL} = {TODAY}''')

    async def admin_stats(self, days=14):
        days = max(1, min(int(days), 90))
        t = await self._one(f'''
            SELECT COUNT(*) AS orders,
                   COALESCE(SUM(CASE WHEN status != 'cancelled' THEN total_price END), 0) AS revenue,
                   COUNT(*) FILTER (WHERE status = 'pending') AS pending,
                   COUNT(*) FILTER (WHERE {LOCAL} = {TODAY}) AS today_orders,
                   COALESCE(SUM(CASE WHEN {LOCAL} = {TODAY} AND status != 'cancelled' THEN total_price END), 0) AS today_revenue
            FROM orders o''')
        users = await self._val('SELECT COUNT(*) FROM users')
        # Bo'sh kunlar ham 0 bilan chiqishi uchun kunlar ro'yxati alohida tuziladi
        daily = await self._all(f'''
            SELECT to_char(d.day, 'YYYY-MM-DD') AS date,
                   COALESCE(SUM(CASE WHEN o.status != 'cancelled' THEN o.total_price END), 0) AS revenue,
                   COUNT(o.id) AS orders
            FROM (SELECT ({TODAY} - {days - 1} + g.i) AS day FROM generate_series(0, {days - 1}) AS g(i)) d
            LEFT JOIN orders o ON {LOCAL} = d.day
            GROUP BY d.day ORDER BY d.day''')
        st = {r['status']: r['n'] for r in await self._all('SELECT status, COUNT(*) AS n FROM orders GROUP BY status')}
        top = await self._all('''
            SELECT p.name, SUM(oi.quantity) AS qty FROM order_items oi
            JOIN orders o ON o.id = oi.order_id AND o.status != 'cancelled'
            JOIN products p ON p.id = oi.product_id
            GROUP BY p.id ORDER BY qty DESC LIMIT 6''')
        return {
            'totals': {**t, 'users': users},
            'daily': daily,
            'statuses': {k: st.get(k, 0) for k in ('pending', 'completed', 'delivered', 'cancelled')},
            'top_products': top,
        }

    async def admin_orders(self, status=None, search=None, page=1, per_page=15):
        where, args = ['TRUE'], []
        if status:
            where.append('o.status = ?'); args.append(status)
        if search:
            like = f'%{search}%'
            where.append('(o.phone_number ILIKE ? OR u.first_name ILIKE ? OR u.username ILIKE ? OR o.id::text = ?)')
            args += [like, like, like, search.lstrip('#')]
        w = ' AND '.join(where)
        total = await self._val(f'SELECT COUNT(*) FROM orders o LEFT JOIN users u ON u.user_id = o.user_id WHERE {w}', args)
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
        where, args = 'TRUE', []
        if search:
            like = f'%{search}%'
            where = '(u.first_name ILIKE ? OR u.phone_number ILIKE ? OR u.username ILIKE ?)'
            args = [like, like, like]
        total = await self._val(f'SELECT COUNT(*) FROM users u WHERE {where}', args)
        rows = await self._all(f'''
            SELECT u.*, COUNT(o.id) AS orders_count,
                   COALESCE(SUM(CASE WHEN o.status != 'cancelled' THEN o.total_price END), 0) AS spent
            FROM users u LEFT JOIN orders o ON o.user_id = u.user_id
            WHERE {where} GROUP BY u.user_id ORDER BY u.created_at DESC LIMIT ? OFFSET ?''',
                              args + [per_page, (max(page, 1) - 1) * per_page])
        return {'items': rows, 'total': total, 'per_page': per_page}
