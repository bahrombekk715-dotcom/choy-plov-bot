"""Eski SQLite bazadagi (data/bot.db) barcha ma'lumotni PostgreSQL ga ko'chiradi.

Ishlatish:
    python migrate_sqlite_to_postgres.py                 # data/bot.db  ->  DATABASE_URL
    python migrate_sqlite_to_postgres.py path/to/bot.db  # boshqa fayl
    python migrate_sqlite_to_postgres.py --force         # PostgreSQL da ma'lumot bo'lsa ham ustidan yozadi

Docker'da:
    docker compose run --rm bot python migrate_sqlite_to_postgres.py

Eslatma: ko'chirishdan oldin botni to'xtating (docker compose stop bot), aks holda ko'chirish paytida kelgan buyurtmalar tushmay qoladi.
Bitta tranzaksiyada ishlaydi: xato bo'lsa PostgreSQL bo'sh holatda qoladi va qayta urinish mumkin. SQLite fayl o'zgartirilmaydi.
"""
import asyncio
import datetime as dt
import sqlite3
import sys

import asyncpg

from config import DATABASE_URL, SQLITE_PATH
from database import Database

# Tartib muhim: bog'langan (FOREIGN KEY) jadvallar o'zidan keyin keladi
TABLES = ['users', 'categories', 'products', 'product_images', 'addons', 'orders', 'order_items',
          'order_addons', 'product_addons', 'favorites', 'addresses']
SERIAL = ['categories', 'products', 'product_images', 'addons', 'orders', 'order_items', 'order_addons', 'addresses']
BOOLS = {'categories': {'is_active'}, 'products': {'is_active', 'is_available'},
         'addons': {'is_active', 'is_available'}, 'addresses': {'is_default'}}
STAMPS = {'users': {'created_at'}, 'orders': {'created_at'}, 'favorites': {'created_at'}}


def stamp(v):
    """SQLite 'YYYY-MM-DD HH:MM:SS' (UTC) matnini timezone'li vaqtga aylantiradi."""
    if v is None or isinstance(v, dt.datetime):
        return v
    d = dt.datetime.fromisoformat(str(v).replace(' ', 'T'))
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def convert(table, col, v):
    if v is None:
        return None
    if col in BOOLS.get(table, ()):
        return bool(v)
    if col in STAMPS.get(table, ()):
        return stamp(v)
    return v


async def main(path, force):
    src = sqlite3.connect(path)
    src.row_factory = sqlite3.Row
    have = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if 'users' not in have:
        sys.exit(f"{path}: bu bot bazasiga o'xshamaydi (users jadvali yo'q)")

    db = Database()
    await db.connect()                 # jadvallarni yaratadi
    pool = db.pool
    try:
        busy = {t: n for t in ('users', 'products', 'orders')
                if (n := await pool.fetchval(f'SELECT COUNT(*) FROM {t}'))}
        if busy and not force:
            sys.exit(f"PostgreSQL bo'sh emas ({busy}). Ustidan yozish uchun --force bilan qayta ishga tushiring.")

        report = []
        async with pool.acquire() as c:
            async with c.transaction():
                await c.execute('TRUNCATE ' + ', '.join(TABLES) + ', meta RESTART IDENTITY CASCADE')
                for t in TABLES:
                    if t not in have:
                        continue
                    pg_cols = {r['column_name'] for r in await c.fetch(
                        "SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = $1", t)}
                    rows = src.execute(f'SELECT * FROM {t}').fetchall()
                    if not rows:
                        report.append((t, 0, 0)); continue
                    cols = [k for k in rows[0].keys() if k in pg_cols]
                    sql = f'INSERT INTO {t} ({", ".join(cols)}) VALUES ({", ".join(f"${i + 1}" for i in range(len(cols)))})'
                    await c.executemany(sql, [[convert(t, k, r[k]) for k in cols] for r in rows])
                    report.append((t, len(rows), await c.fetchval(f'SELECT COUNT(*) FROM {t}')))
                for t in SERIAL:     # keyingi yangi yozuvlar mavjud id lar bilan to'qnashmasligi uchun
                    await c.execute(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), "
                                    f"COALESCE((SELECT MAX(id) FROM {t}), 0) + 1, false)")
                # qo'shimchalar va sevimlilar allaqachon ko'chirildi: bir martalik "hammasiga bog'lash" qayta ishlamasin
                await c.execute("INSERT INTO meta (key, value) VALUES ('schema_version', '1')")
        print(f"{'jadval':<18}{'SQLite':>8}{'PostgreSQL':>12}")
        for t, a, b in report:
            print(f'{t:<18}{a:>8}{b:>12}' + ('' if a == b else '   <-- farq bor!'))
        print("\nTayyor. Endi botni ishga tushiring.")
    finally:
        await db.close()
        src.close()


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    try:
        asyncio.run(main(args[0] if args else SQLITE_PATH, '--force' in sys.argv))
    except asyncpg.PostgresError as e:
        sys.exit(f"PostgreSQL xatosi: {e}")
