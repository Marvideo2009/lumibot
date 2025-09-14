import aiosqlite
from typing import Optional


async def init_db(chemin_bdd: str) -> aiosqlite.Connection:
    async with aiosqlite.connect(chemin_bdd) as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS documents_datas (
                url TEXT PRIMARY KEY,
                titre TEXT,
                description TEXT
            );
        ''')
        try:
            await conn.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS documents
                USING fts5(
                    url UNINDEXED,
                    titre,
                    description
                );
            ''')
        except Exception as e:
            print("err:", e)
        await conn.commit()

    conn = await aiosqlite.connect(chemin_bdd)

    await conn.execute("PRAGMA journal_mode=WAL")

    return conn


async def fermer_db(conn: Optional[aiosqlite.Connection]) -> None:
    if conn:
        await conn.close()
