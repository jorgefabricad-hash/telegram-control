import os
from pathlib import Path
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Document
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from bot.menus import menu_cancelar

AGUARDA_CAMINHO = 0
HOME = Path.home()
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _safe_path(p: str) -> Path:
    path = Path(p).resolve()
    return path


def _listar_dir(path: Path) -> str:
    try:
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    except PermissionError:
        return "⛔ Sem permissão para acessar esta pasta."
    lines = [f"📂 *{path}*\n"]
    for item in items[:30]:
        if item.is_dir():
            lines.append(f"📁 `{item.name}/`")
        else:
            size = item.stat().st_size
            lines.append(f"📄 `{item.name}` ({_fmt_size(size)})")
    if len(list(path.iterdir())) > 30:
        lines.append("_(mostrando primeiros 30 itens)_")
    return "\n".join(lines)


def _fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}TB"


async def show_menu(update: Update, context):
    context.user_data["arq_path"] = str(HOME)
    text = _listar_dir(HOME) + "\n\n_Digite o caminho completo de um arquivo para baixar, ou uma pasta para navegar._"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=menu_cancelar())
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=menu_cancelar())
    return AGUARDA_CAMINHO


async def receber_caminho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    path = _safe_path(texto)

    if path.is_dir():
        context.user_data["arq_path"] = str(path)
        text = _listar_dir(path)
        await update.message.reply_text(
            text + "\n\n_Digite o caminho de um arquivo ou pasta:_",
            parse_mode="Markdown",
            reply_markup=menu_cancelar(),
        )
        return AGUARDA_CAMINHO

    if path.is_file():
        size = path.stat().st_size
        if size > MAX_FILE_SIZE:
            await update.message.reply_text(
                f"⚠️ Arquivo muito grande ({_fmt_size(size)}). Limite: 50 MB.",
                reply_markup=menu_cancelar(),
            )
            return AGUARDA_CAMINHO
        await update.message.reply_text(f"📤 Enviando `{path.name}`...", parse_mode="Markdown")
        with open(path, "rb") as f:
            await update.message.reply_document(document=f, filename=path.name)
        return ConversationHandler.END

    await update.message.reply_text(
        f"❌ Caminho não encontrado: `{texto}`\nDigite novamente:",
        parse_mode="Markdown",
        reply_markup=menu_cancelar(),
    )
    return AGUARDA_CAMINHO


async def handle_callback(query, context, data: str):
    pass


def conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(show_menu, pattern="^menu_arquivos$")],
        states={
            AGUARDA_CAMINHO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_caminho)],
        },
        fallbacks=[CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancelar$")],
        per_message=False,
    )
