from fastapi import BackgroundTasks, Depends, FastAPI, Query, Request, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Union
import aiosqlite
import datetime
import database
import uvicorn

app = FastAPI()
DB_PATH = "data.db"
AUTHORIZED_UA = "Lumibot/2.0 (https://github.com/work-search/api_princ)"
REINDEX_PASSWORD = "SuperMotDePasse1"

# --- MODELES ---
class Page(BaseModel):
    url: str
    titre: str
    description: str

# --- UTILS ---
async def get_conn():
    return await database.init_db(DB_PATH)

async def check_user_agent(request: Request):
    ua = request.headers.get("User-Agent", "")
    if ua != AUTHORIZED_UA:
        raise HTTPException(status_code=403, detail="Invalid User-Agent")
    return True

async def rebuild_fts5():
    """Reconstruit l'index FTS5 à partir de documents_data"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM documents;")
        async with db.execute("SELECT url, titre, description FROM documents_data") as cursor:
            rows = await cursor.fetchall()
        docs = [(row[0], row[1], row[2]) for row in rows]
        await db.executemany(
            "INSERT INTO documents (url, titre, description) VALUES (?, ?, ?)",
            docs
        )
        await db.commit()
    print(f"[{datetime.now()}] [FTS5] Index reconstruit pour {len(docs)} documents")

# --- Scheduler ---
scheduler = AsyncIOScheduler()

# Planifie la réindexation tous les jours à minuit
scheduler.add_job(rebuild_fts5, "cron", hour=0, minute=0)
scheduler.start()

# --- ROUTES ---
@app.post("/add")
async def add_documents(pages: Union[Page, List[Page]], request: Request, background_tasks: BackgroundTasks, request_ok: bool = Depends(check_user_agent)):
    try:
        if isinstance(pages, list):
            if len(pages) > 100:
                raise HTTPException(status_code=400, detail="Batch size exceeds 100")
            pages_to_add = pages
        else:
            pages_to_add = [pages]
        db = await get_conn()
        try:
            docs = [(d.url, d.titre, d.description) for d in pages_to_add]
            await db.executemany("""
                INSERT INTO documents_datas (url, titre, description)
                VALUES (?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    titre=excluded.titre,
                    description=excluded.description
            """, docs)

            await db.commit()
        finally:
            await database.fermer_db(db)
        return {"status": "ok", "count": len(pages_to_add)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search(q: str, limit: int = 10):
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                """
                SELECT url, titre, description
                FROM documents
                WHERE documents MATCH ?
                LIMIT ?
                """,
                (q, limit)
            ) as cursor:
                rows = await cursor.fetchall()
        return {
            "results": [
                {"url": row["url"], "titre": row["titre"], "description": row["description"]}
                for row in rows
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def home():
    try:
        return {"action":
                    {
                        "add":"To add pages",
                        "search":"To search with the argument q to put the request",
                        "export":"Export th database to a db file"
                    },
                    "Example":[
                        "https://lumina.marvideo.fr/add",
                        "https://lumina.marvideo.fr/search?q=request",
                        "https://lumina.marvideo.fr/download",
                        "https://lumina.marvideo.fr/reindex?password=motdepasse"
                    ]
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
async def download_db():
    return FileResponse(DB_PATH, filename="lumibot_pages.db", media_type="application/octet-stream")

@app.get("/reindex")
async def reindex(background_tasks: BackgroundTasks, password: str = Query(...)):
    if password != REINDEX_PASSWORD:
        raise HTTPException(status_code=403, detail="Mot de passe invalide")
    background_tasks.add_task(rebuild_fts5)
    return {"status": "ok", "message": "Réindexation en cours en arrière-plan"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3060)