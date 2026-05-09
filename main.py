import asyncio
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update
from telegram.ext import Application

from config import BOT_TOKEN, API_PORT, ALLOWED_USER_ID
from database.db import init_db
from bot.handlers import register
from api.server import router as api_router

RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")

_bot_app: Application = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bot_app

    init_db()

    _bot_app = Application.builder().token(BOT_TOKEN).build()
    register(_bot_app)
    await _bot_app.initialize()
    await _bot_app.start()

    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/tgwebhook"
        await _bot_app.bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        print(f"Webhook registrado: {webhook_url}")
    else:
        asyncio.create_task(_bot_app.updater.start_polling(drop_pending_updates=True))
        print("Polling iniciado (modo local)")

    yield

    if not RENDER_URL:
        await _bot_app.updater.stop()
        await _bot_app.stop()
        await _bot_app.shutdown()


app = FastAPI(title="Controle Pessoal API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.post("/tgwebhook")
async def tg_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, _bot_app.bot)
    await _bot_app.process_update(update)
    return {"ok": True}


def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN nao configurado.")
        return
    if ALLOWED_USER_ID == 0:
        print("ALLOWED_USER_ID nao configurado.")
        return
    uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="info")


if __name__ == "__main__":
    main()
