import asyncio
import subprocess
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from config import BLOCKED_COMMANDS
from bot.menus import menu_cancelar

AGUARDA_CMD = 0
TIMEOUT = 30


def _is_blocked(cmd: str) -> bool:
    lower = cmd.lower()
    return any(b in lower for b in BLOCKED_COMMANDS)


async def show_menu(update: Update, context):
    text = (
        "💻 *Executar Comando*\n\n"
        "Digite o comando a executar no terminal do PC.\n"
        "⚠️ Comandos destrutivos são bloqueados.\n\n"
        "_Exemplo:_ `dir C:\\Users` ou `ipconfig`"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_cancelar())
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=menu_cancelar())
    return AGUARDA_CMD


async def receber_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.strip()

    if _is_blocked(cmd):
        await update.message.reply_text(
            f"🚫 *Comando bloqueado por segurança:* `{cmd}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="menu_inicio")]]),
        )
        return ConversationHandler.END

    msg = await update.message.reply_text(f"⏳ Executando: `{cmd}`", parse_mode="Markdown")

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            shell=True,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            await msg.edit_text(f"⏰ Timeout após {TIMEOUT}s\n\nComando: `{cmd}`", parse_mode="Markdown")
            return ConversationHandler.END

        output = stdout.decode("cp850", errors="replace").strip() if stdout else ""
        if not output:
            output = "(sem saída)"

        if len(output) > 3800:
            output = output[:3800] + "\n...[truncado]"

        await msg.edit_text(
            f"✅ `{cmd}`\n\n```\n{output}\n```",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="menu_inicio")]]),
        )
    except Exception as e:
        await msg.edit_text(
            f"❌ Erro: `{e}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="menu_inicio")]]),
        )

    return ConversationHandler.END


def conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_menu, pattern="^menu_cmd$"),
            CommandHandler("cmd", show_menu),
        ],
        states={
            AGUARDA_CMD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_comando)],
        },
        fallbacks=[CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancelar$")],
        per_message=False,
    )
