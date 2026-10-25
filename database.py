import aiosqlite
import datetime

class Database:
    def __init__(self, db_path='bot.db'):
        self.db_path = db_path

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self.create_tables()

    async def create_tables(self):
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                phone_number TEXT NOT NULL,
                username TEXT,
                first_name TEXT,
                language TEXT DEFAULT 'uz',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        await self.db.execute('''
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
            )
        ''')

        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS addons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')

        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                phone_number TEXT NOT NULL,
                address TEXT NOT NULL,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS order_addons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_item_id INTEGER NOT NULL,
                addon_id INTEGER NOT NULL,
                FOREIGN KEY (order_item_id) REFERENCES order_items(id),
                FOREIGN KEY (addon_id) REFERENCES addons(id)
            )
        ''')

        await self.db.commit()

    async def add_user(self, user_id, phone_number, username=None, first_name=None):
        await self.db.execute(
            'INSERT OR REPLACE INTO users (user_id, phone_number, username, first_name) VALUES (?, ?, ?, ?)',
            (user_id, phone_number, username, first_name)
        )
        await self.db.commit()

    async def get_user(self, user_id):
        cursor = await self.db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return await cursor.fetchone()

    async def update_user_language(self, user_id, language):
        await self.db.execute(
            'UPDATE users SET language = ? WHERE user_id = ?',
            (language, user_id)
        )
        await self.db.commit()

    async def get_user_language(self, user_id):
        cursor = await self.db.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        return result['language'] if result else 'uz'

    async def add_category(self, name):
        cursor = await self.db.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        await self.db.commit()
        return cursor.lastrowid

    async def get_categories(self, active_only=True):
        if active_only:
            cursor = await self.db.execute('SELECT * FROM categories WHERE is_active = 1')
        else:
            cursor = await self.db.execute('SELECT * FROM categories')
        return await cursor.fetchall()

    async def get_category(self, category_id):
        cursor = await self.db.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
        return await cursor.fetchone()

    async def update_category(self, category_id, name):
        await self.db.execute('UPDATE categories SET name = ? WHERE id = ?', (name, category_id))
        await self.db.commit()

    async def delete_category(self, category_id):
        await self.db.execute('UPDATE categories SET is_active = 0 WHERE id = ?', (category_id,))
        await self.db.commit()

    async def add_product(self, category_id, name, price, description=None, image_url=None):
        cursor = await self.db.execute(
            'INSERT INTO products (category_id, name, price, description, image_url) VALUES (?, ?, ?, ?, ?)',
            (category_id, name, price, description, image_url)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def get_products_by_category(self, category_id, available_only=True):
        if available_only:
            cursor = await self.db.execute(
                'SELECT * FROM products WHERE category_id = ? AND is_active = 1 AND is_available = 1',
                (category_id,)
            )
        else:
            cursor = await self.db.execute(
                'SELECT * FROM products WHERE category_id = ? AND is_active = 1',
                (category_id,)
            )
        return await cursor.fetchall()

    async def get_product(self, product_id):
        cursor = await self.db.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        return await cursor.fetchone()

    async def update_product(self, product_id, name, price, description, image_url=None):
        await self.db.execute(
            'UPDATE products SET name = ?, price = ?, description = ?, image_url = ? WHERE id = ?',
            (name, price, description, image_url, product_id)
        )
        await self.db.commit()

    async def update_product_image(self, product_id, image_url):
        await self.db.execute(
            'UPDATE products SET image_url = ? WHERE id = ?',
            (image_url, product_id)
        )
        await self.db.commit()

    async def toggle_product_availability(self, product_id):
        await self.db.execute(
            'UPDATE products SET is_available = NOT is_available WHERE id = ?',
            (product_id,)
        )
        await self.db.commit()

    async def delete_product(self, product_id):
        await self.db.execute('UPDATE products SET is_active = 0 WHERE id = ?', (product_id,))
        await self.db.commit()

    async def add_addon(self, name, price):
        cursor = await self.db.execute('INSERT INTO addons (name, price) VALUES (?, ?)', (name, price))
        await self.db.commit()
        return cursor.lastrowid

    async def get_addons(self, active_only=True):
        if active_only:
            cursor = await self.db.execute('SELECT * FROM addons WHERE is_active = 1')
        else:
            cursor = await self.db.execute('SELECT * FROM addons')
        return await cursor.fetchall()

    async def create_order(self, user_id, phone_number, address, total_price, comment=None):
        cursor = await self.db.execute(
            'INSERT INTO orders (user_id, phone_number, address, total_price, comment) VALUES (?, ?, ?, ?, ?)',
            (user_id, phone_number, address, total_price, comment)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def add_order_item(self, order_id, product_id, quantity, price):
        cursor = await self.db.execute(
            'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
            (order_id, product_id, quantity, price)
        )
        await self.db.commit()
        return cursor.lastrowid

    async def add_order_addon(self, order_item_id, addon_id):
        await self.db.execute(
            'INSERT INTO order_addons (order_item_id, addon_id) VALUES (?, ?)',
            (order_item_id, addon_id)
        )
        await self.db.commit()

    async def get_pending_orders(self):
        cursor = await self.db.execute(
            'SELECT * FROM orders WHERE status = "pending" ORDER BY created_at DESC'
        )
        return await cursor.fetchall()

    async def get_order(self, order_id):
        cursor = await self.db.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        return await cursor.fetchone()

    async def get_order_items(self, order_id):
        cursor = await self.db.execute('''
            SELECT oi.*, p.name as product_name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order_id,))
        return await cursor.fetchall()

    async def get_order_addons(self, order_item_id):
        cursor = await self.db.execute('''
            SELECT a.name, a.price
            FROM order_addons oa
            JOIN addons a ON oa.addon_id = a.id
            WHERE oa.order_item_id = ?
        ''', (order_item_id,))
        return await cursor.fetchall()

    async def update_order_status(self, order_id, status):
        await self.db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        await self.db.commit()

    async def get_user_orders(self, user_id):
        cursor = await self.db.execute(
            'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        )
        return await cursor.fetchall()

    async def get_today_stats(self):
        today = datetime.date.today()
        cursor = await self.db.execute('''
            SELECT
                COUNT(*) as total_orders,
                SUM(total_price) as total_revenue,
                SUM(CASE WHEN status = 'completed' THEN total_price ELSE 0 END) as completed_revenue
            FROM orders
            WHERE DATE(created_at) = ?
        ''', (today,))
        return await cursor.fetchone()

    async def close(self):
        await self.db.close()
