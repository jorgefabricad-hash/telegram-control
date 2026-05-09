import asyncio
import threading
import sys
import uvicorn
from telegram.ext import Application
from config import BOT_TOKEN, API_PORT, ALLOWED_USER_ID
from database.db import init_db
from bot.handlers import register
from api.server import app as fastapi_app

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def run_api():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=API_PORT, log_level="warning")


async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    register(application)
    print(f"🤖 Bot iniciado. Aguardando mensagens...")
    print(f"🌐 API REST disponível em http://localhost:{API_PORT}")
    print(f"📊 Docs da API: http://localhost:{API_PORT}/docs")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    try:
        await asyncio.Event().wait()
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN não configurado. Copie .env.example para .env e preencha.")
        return
    if ALLOWED_USER_ID == 0:
        print("❌ ALLOWED_USER_ID não configurado. Preencha seu Telegram Chat ID no .env.")
        return

    init_db()
    print("✅ Banco de dados inicializado.")

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
