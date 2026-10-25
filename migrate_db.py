#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database migration script to add language column to users table
"""
import asyncio
import aiosqlite

async def migrate():
    db = await aiosqlite.connect('bot.db')

    try:
        # Check if language column exists
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'language' not in column_names:
            print("Adding 'language' column to users table...")
            await db.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'uz'")
            await db.commit()
            print("✅ Migration completed successfully!")
        else:
            print("✅ Language column already exists. No migration needed.")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        await db.close()

if __name__ == '__main__':
    asyncio.run(migrate())
