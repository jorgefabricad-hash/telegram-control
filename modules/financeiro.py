from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from database.db import fetch_all, fetch_one, execute
from bot.menus import menu_financeiro, menu_cancelar
from reports.generator import gerar_todos

AGUARDA_TIPO, AGUARDA_VALOR, AGUARDA_CATEGORIA, AGUARDA_DESCRICAO = range(4)


async def show_menu(query):
    saldo = _calcular_saldo()
    await query.edit_message_text(
        f"💰 *Financeiro*\n\nSaldo atual: *R$ {saldo:.2f}*\n\nO que deseja fazer?",
        parse_mode="Markdown",
        reply_markup=menu_financeiro(),
    )


def _calcular_saldo() -> float:
    r = fetch_one("SELECT COALESCE(SUM(CASE WHEN tipo='receita' THEN valor ELSE -valor END),0)::float AS s FROM transacoes")
    return float(r["s"]) if r else 0.0


async def handle_callback(query, context, data: str):
    if data == "fin_saldo":
        saldo = _calcular_saldo()
        total_rec = float(fetch_one("SELECT COALESCE(SUM(valor),0)::float AS s FROM transacoes WHERE tipo='receita'")["s"])
        total_desp = float(fetch_one("SELECT COALESCE(SUM(valor),0)::float AS s FROM transacoes WHERE tipo='despesa'")["s"])
        await query.edit_message_text(
            f"📈 *Resumo Financeiro*\n\n"
            f"✅ Receitas: R$ {total_rec:.2f}\n"
            f"❌ Despesas: R$ {total_desp:.2f}\n"
            f"💰 Saldo: R$ {saldo:.2f}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="menu_financeiro")]]),
        )
    elif data == "fin_extrato":
        rows = fetch_all(
            "SELECT data::text, tipo, valor::float, categoria, descricao FROM transacoes ORDER BY criado_em DESC LIMIT 10"
        )
        if not rows:
            text = "📋 Nenhuma transação registrada ainda."
        else:
            lines = ["📋 *Últimas 10 transações:*\n"]
            for r in rows:
                emoji = "✅" if r["tipo"] == "receita" else "❌"
                lines.append(f"{emoji} {r['data']} | {r['categoria']} | R$ {r['valor']:.2f}")
                if r["descricao"]:
                    lines.append(f"   _{r['descricao']}_")
            text = "\n".join(lines)
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="menu_financeiro")]]),
        )
    elif data in ("fin_receita", "fin_despesa"):
        context.user_data["fin_tipo"] = "receita" if data == "fin_receita" else "despesa"
        await query.edit_message_text(
            f"{'➕ Receita' if data=='fin_receita' else '➖ Despesa'}\n\nDigite o *valor* (ex: 150.00):",
            parse_mode="Markdown",
            reply_markup=menu_cancelar(),
        )
        return AGUARDA_VALOR


async def receber_valor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Valor inválido. Digite um número (ex: 150.00):", reply_markup=menu_cancelar())
        return AGUARDA_VALOR
    context.user_data["fin_valor"] = valor
    tipo = context.user_data.get("fin_tipo", "despesa")
    cats = fetch_all(f"SELECT nome FROM categorias WHERE tipo='{tipo}' OR tipo='ambos'")
    buttons = [[InlineKeyboardButton(c["nome"], callback_data=f"fin_cat:{c['nome']}")] for c in cats]
    buttons.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    await update.message.reply_text(
        "Escolha a *categoria*:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return AGUARDA_CATEGORIA


async def receber_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    categoria = query.data.replace("fin_cat:", "")
    context.user_data["fin_categoria"] = categoria
    await query.edit_message_text(
        f"Categoria: *{categoria}*\n\nDigite uma descrição (ou /pular):",
        parse_mode="Markdown",
        reply_markup=menu_cancelar(),
    )
    return AGUARDA_DESCRICAO


async def receber_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    descricao = "" if update.message.text == "/pular" else update.message.text
    ud = context.user_data
    execute(
        "INSERT INTO transacoes (tipo, valor, categoria, descricao) VALUES (?,?,?,?)",
        (ud["fin_tipo"], ud["fin_valor"], ud["fin_categoria"], descricao),
    )
    gerar_todos()
    saldo = _calcular_saldo()
    emoji = "✅" if ud["fin_tipo"] == "receita" else "❌"
    await update.message.reply_text(
        f"{emoji} *Lançamento registrado!*\n\n"
        f"Tipo: {ud['fin_tipo'].capitalize()}\n"
        f"Valor: R$ {ud['fin_valor']:.2f}\n"
        f"Categoria: {ud['fin_categoria']}\n"
        f"Saldo atual: R$ {saldo:.2f}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="menu_inicio")]]),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Operação cancelada.")
    return ConversationHandler.END


def conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callback, pattern="^fin_(receita|despesa)$")],
        states={
            AGUARDA_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_valor)],
            AGUARDA_CATEGORIA: [CallbackQueryHandler(receber_categoria, pattern="^fin_cat:")],
            AGUARDA_DESCRICAO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_descricao),
                MessageHandler(filters.COMMAND, receber_descricao),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancelar$"),
        ],
        per_message=False,
    )
