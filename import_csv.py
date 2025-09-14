import pandas as pd
import asyncio
import aiosqlite

DB_PATH = "data.db"
CSV_PATH = "lumibot_pages.csv"

async def import_csv():
    # Charger le CSV avec pandas
    df = pd.read_csv(CSV_PATH)

    # Vérification des colonnes nécessaires
    required_cols = {"url", "titre", "description"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Le CSV doit contenir les colonnes : {required_cols}")

    async with aiosqlite.connect(DB_PATH) as conn:
        # Optimisations SQLite pour gros imports
        await conn.execute("PRAGMA synchronous = OFF;")
        await conn.execute("PRAGMA journal_mode = MEMORY;")

        count = 0
        await conn.execute("BEGIN")
        for _, row in df.iterrows():
            url = str(row["url"])
            titre = str(row.get("titre", ""))
            description = str(row.get("description", ""))

            await conn.execute(
                "INSERT INTO documents_datas (url, titre, description) VALUES (?, ?, ?) ON CONFLICT(url) DO UPDATE SET titre=excluded.titre, description=excluded.description",
                (url, titre, description)
            )
            print(f"Adding {url}")
            count += 1

        await conn.commit()
        print(f"[OK] Import terminé : {count} lignes insérées/mises à jour.")

if __name__ == "__main__":
    asyncio.run(import_csv())