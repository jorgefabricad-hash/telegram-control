from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from database.db import fetch_all, fetch_one, execute
from bot.menus import menu_km, menu_cancelar
from reports.generator import gerar_todos

(
    ABAST_KM, ABAST_LITROS, ABAST_PRECO, ABAST_DESC,
    VIAG_KM_INI, VIAG_KM_FIN, VIAG_DESC,
) = range(7)


async def show_menu(query):
    total_km = float(fetch_one("SELECT COALESCE(SUM(km_percorridos),0)::float AS s FROM km_registros WHERE tipo='viagem'")["s"])
    total_gasto = float(fetch_one("SELECT COALESCE(SUM(custo_total),0)::float AS s FROM km_registros WHERE tipo='abastecimento'")["s"])
    await query.edit_message_text(
        f"🚗 *KM / Veículo*\n\n"
        f"Total rodado: *{total_km:.0f} km*\n"
        f"Total combustível: *R$ {total_gasto:.2f}*\n\n"
        f"O que deseja registrar?",
        parse_mode="Markdown",
        reply_markup=menu_km(),
    )


async def handle_callback(query, context, data: str):
    if data == "km_resumo":
        rows = fetch_all(
            "SELECT TO_CHAR(data,'YYYY-MM') AS mes, "
            "COALESCE(SUM(CASE WHEN tipo='viagem' THEN km_percorridos ELSE 0 END),0)::float AS km, "
            "COALESCE(SUM(CASE WHEN tipo='abastecimento' THEN custo_total ELSE 0 END),0)::float AS custo "
            "FROM km_registros GROUP BY mes ORDER BY mes DESC LIMIT 6"
        )
        if not rows:
            text = "🚗 Nenhum registro de KM ainda."
        else:
            lines = ["🚗 *Resumo por mês:*\n"]
            for r in rows:
                lines.append(f"📅 {r['mes']}: {r['km']:.0f} km | R$ {r['custo']:.2f}")
            text = "\n".join(lines)
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="menu_km")]]),
        )


async def abast_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⛽ *Abastecimento*\n\nDigite o KM atual do veículo:", parse_mode="Markdown", reply_markup=menu_cancelar())
    context.user_data["km_tipo"] = "abastecimento"
    return ABAST_KM


async def abast_receber_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["km_ini"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ KM inválido:", reply_markup=menu_cancelar())
        return ABAST_KM
    await update.message.reply_text("Quantos *litros* abasteceu?", parse_mode="Markdown", reply_markup=menu_cancelar())
    return ABAST_LITROS


async def abast_receber_litros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["km_litros"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Litros inválido:", reply_markup=menu_cancelar())
        return ABAST_LITROS
    await update.message.reply_text("*Preço por litro* (R$):", parse_mode="Markdown", reply_markup=menu_cancelar())
    return ABAST_PRECO


async def abast_receber_preco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["km_preco"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Preço inválido:", reply_markup=menu_cancelar())
        return ABAST_PRECO
    await update.message.reply_text("Observação (ou /pular):", reply_markup=menu_cancelar())
    return ABAST_DESC


async def abast_receber_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = "" if update.message.text == "/pular" else update.message.text
    ud = context.user_data
    custo = round(ud["km_litros"] * ud["km_preco"], 2)
    execute(
        "INSERT INTO km_registros (tipo, km_inicial, litros, preco_litro, custo_total, descricao) VALUES (?,?,?,?,?,?)",
        ("abastecimento", ud["km_ini"], ud["km_litros"], ud["km_preco"], custo, desc),
    )
    gerar_todos()
    total = ud["km_litros"] * ud["km_preco"]
    await update.message.reply_text(
        f"⛽ *Abastecimento registrado!*\n\n"
        f"KM: {ud['km_ini']:.0f}\n"
        f"Litros: {ud['km_litros']:.2f}\n"
        f"Preço/L: R$ {ud['km_preco']:.3f}\n"
        f"Total: R$ {total:.2f}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="menu_inicio")]]),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def viag_km_ini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🛣️ *Viagem*\n\nDigite o KM *inicial*:", parse_mode="Markdown", reply_markup=menu_cancelar())
    context.user_data["km_tipo"] = "viagem"
    return VIAG_KM_INI


async def viag_receber_km_ini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["km_ini"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ KM inválido:", reply_markup=menu_cancelar())
        return VIAG_KM_INI
    await update.message.reply_text("KM *final*:", parse_mode="Markdown", reply_markup=menu_cancelar())
    return VIAG_KM_FIN


async def viag_receber_km_fin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["km_fin"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ KM inválido:", reply_markup=menu_cancelar())
        return VIAG_KM_FIN
    await update.message.reply_text("Destino/observação (ou /pular):", reply_markup=menu_cancelar())
    return VIAG_DESC


async def viag_receber_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = "" if update.message.text == "/pular" else update.message.text
    ud = context.user_data
    percorridos = ud["km_fin"] - ud["km_ini"]
    execute(
        "INSERT INTO km_registros (tipo, km_inicial, km_final, km_percorridos, descricao) VALUES (?,?,?,?,?)",
        ("viagem", ud["km_ini"], ud["km_fin"], round(ud["km_fin"] - ud["km_ini"], 2), desc),
    )
    gerar_todos()
    await update.message.reply_text(
        f"🛣️ *Viagem registrada!*\n\n"
        f"KM inicial: {ud['km_ini']:.0f}\n"
        f"KM final: {ud['km_fin']:.0f}\n"
        f"Percorridos: *{percorridos:.0f} km*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="menu_inicio")]]),
    )
    context.user_data.clear()
    return ConversationHandler.END


def conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(abast_km, pattern="^km_abastecimento$"),
            CallbackQueryHandler(viag_km_ini, pattern="^km_viagem$"),
        ],
        states={
            ABAST_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, abast_receber_km)],
            ABAST_LITROS: [MessageHandler(filters.TEXT & ~filters.COMMAND, abast_receber_litros)],
            ABAST_PRECO: [MessageHandler(filters.TEXT & ~filters.COMMAND, abast_receber_preco)],
            ABAST_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, abast_receber_desc),
                MessageHandler(filters.COMMAND, abast_receber_desc),
            ],
            VIAG_KM_INI: [MessageHandler(filters.TEXT & ~filters.COMMAND, viag_receber_km_ini)],
            VIAG_KM_FIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, viag_receber_km_fin)],
            VIAG_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, viag_receber_desc),
                MessageHandler(filters.COMMAND, viag_receber_desc),
            ],
        },
        fallbacks=[CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancelar$")],
        per_message=False,
    )
