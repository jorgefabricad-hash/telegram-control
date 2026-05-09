from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)
from database.db import fetch_all, fetch_one, execute
from bot.menus import menu_cancelar
from reports.generator import gerar_todos

AGUARDA_VALOR, AGUARDA_CATEGORIA, AGUARDA_DESCRICAO = range(3)


async def show_menu(query, context):
    hoje = float(fetch_one(
        "SELECT COALESCE(SUM(valor),0)::float AS s FROM transacoes WHERE tipo='despesa' AND data=CURRENT_DATE"
    )["s"])
    mes = float(fetch_one(
        "SELECT COALESCE(SUM(valor),0)::float AS s FROM transacoes WHERE tipo='despesa' AND TO_CHAR(data,'YYYY-MM')=TO_CHAR(NOW(),'YYYY-MM')"
    )["s"])
    await query.edit_message_text(
        f"💸 *Registro de Despesas*\n\n"
        f"Hoje: R$ {hoje:.2f}\n"
        f"Este mês: R$ {mes:.2f}\n\n"
        f"Digite o valor da despesa:",
        parse_mode="Markdown",
        reply_markup=menu_cancelar(),
    )
    context.user_data["fin_tipo"] = "despesa"
    return AGUARDA_VALOR


async def receber_valor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Valor inválido. Digite um número:", reply_markup=menu_cancelar())
        return AGUARDA_VALOR
    context.user_data["desp_valor"] = valor
    cats = fetch_all("SELECT nome FROM categorias WHERE tipo='despesa' OR tipo='ambos'")
    buttons = [[InlineKeyboardButton(c["nome"], callback_data=f"desp_cat:{c['nome']}")] for c in cats]
    buttons.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    await update.message.reply_text(
        f"Valor: *R$ {valor:.2f}*\n\nEscolha a *categoria*:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return AGUARDA_CATEGORIA


async def receber_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    categoria = query.data.replace("desp_cat:", "")
    context.user_data["desp_categoria"] = categoria
    await query.edit_message_text(
        f"Categoria: *{categoria}*\n\nDigite uma descrição ou /pular:",
        parse_mode="Markdown",
        reply_markup=menu_cancelar(),
    )
    return AGUARDA_DESCRICAO


async def receber_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    descricao = "" if update.message.text == "/pular" else update.message.text
    ud = context.user_data
    execute(
        "INSERT INTO transacoes (tipo, valor, categoria, descricao) VALUES (?,?,?,?)",
        ("despesa", ud["desp_valor"], ud["desp_categoria"], descricao),
    )
    gerar_todos()
    await update.message.reply_text(
        f"✅ *Despesa registrada!*\n\n"
        f"💸 R$ {ud['desp_valor']:.2f} — {ud['desp_categoria']}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="menu_inicio")]]),
    )
    context.user_data.clear()
    return ConversationHandler.END


def conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_menu, pattern="^menu_despesas$"),
            CommandHandler("despesas", show_menu),
        ],
        states={
            AGUARDA_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_valor)],
            AGUARDA_CATEGORIA: [CallbackQueryHandler(receber_categoria, pattern="^desp_cat:")],
            AGUARDA_DESCRICAO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_descricao),
                MessageHandler(filters.COMMAND, receber_descricao),
            ],
        },
        fallbacks=[CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancelar$")],
        per_message=False,
    )
