from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from database.db import fetch_all, fetch_one, execute
from bot.menus import menu_objetivos, menu_cancelar
from reports.generator import gerar_todos

(
    OBJ_TITULO, OBJ_META, OBJ_UNIDADE, OBJ_PRAZO,
    ATU_ESCOLHER, ATU_VALOR, ATU_NOTA,
) = range(7)


async def show_menu(query):
    ativos = fetch_one("SELECT COUNT(*)::int AS n FROM objetivos WHERE status='ativo'")["n"]
    concluidos = fetch_one("SELECT COUNT(*)::int AS n FROM objetivos WHERE status='concluido'")["n"]
    await query.edit_message_text(
        f"🎯 *Objetivos*\n\nAtivos: *{ativos}* | Concluídos: *{concluidos}*\n\nO que deseja fazer?",
        parse_mode="Markdown",
        reply_markup=menu_objetivos(),
    )


async def iniciar_atualizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point correto para atualizar progresso de objetivo."""
    query = update.callback_query
    await query.answer()
    rows = fetch_all("SELECT id, titulo FROM objetivos WHERE status='ativo'")
    if not rows:
        await query.edit_message_text(
            "Nenhum objetivo ativo para atualizar.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="menu_objetivos")]]),
        )
        return ConversationHandler.END
    buttons = [[InlineKeyboardButton(r["titulo"], callback_data=f"obj_sel:{r['id']}")] for r in rows]
    buttons.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    await query.edit_message_text(
        "Qual objetivo deseja atualizar?",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return ATU_ESCOLHER


async def handle_callback(query, context, data: str):
    if data == "obj_listar":
        rows = fetch_all("SELECT * FROM objetivos WHERE status='ativo' ORDER BY prazo ASC")
        if not rows:
            text = "🎯 Nenhum objetivo ativo."
        else:
            lines = ["🎯 *Objetivos Ativos:*\n"]
            for r in rows:
                pct = (r["valor_atual"] / r["meta_valor"] * 100) if r["meta_valor"] else 0
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                prazo = f" | Prazo: {r['prazo']}" if r["prazo"] else ""
                lines.append(
                    f"*{r['titulo']}*\n"
                    f"[{bar}] {pct:.0f}%\n"
                    f"{r['valor_atual']:.2f}/{r['meta_valor']:.2f} {r['unidade']}{prazo}\n"
                )
            text = "\n".join(lines)
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="menu_objetivos")]]),
        )
    elif data == "obj_atualizar":
        rows = fetch_all("SELECT id, titulo FROM objetivos WHERE status='ativo'")
        if not rows:
            await query.edit_message_text(
                "Nenhum objetivo ativo para atualizar.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="menu_objetivos")]]),
            )
            return
        buttons = [[InlineKeyboardButton(r["titulo"], callback_data=f"obj_sel:{r['id']}")] for r in rows]
        buttons.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
        await query.edit_message_text(
            "Qual objetivo deseja atualizar?",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return ATU_ESCOLHER


async def obj_novo_titulo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎯 *Novo Objetivo*\n\nDigite o *título* do objetivo:", parse_mode="Markdown", reply_markup=menu_cancelar())
    return OBJ_TITULO


async def receber_titulo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["obj_titulo"] = update.message.text
    await update.message.reply_text("Qual é a *meta* (valor numérico)?\nEx: 10000 para R$10.000 ou 500 para 500km", parse_mode="Markdown", reply_markup=menu_cancelar())
    return OBJ_META


async def receber_meta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["obj_meta"] = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Valor inválido:", reply_markup=menu_cancelar())
        return OBJ_META
    await update.message.reply_text("Qual a *unidade*? (ex: R$, km, kg, livros) ou /pular:", parse_mode="Markdown", reply_markup=menu_cancelar())
    return OBJ_UNIDADE


async def receber_unidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["obj_unidade"] = "" if update.message.text == "/pular" else update.message.text
    await update.message.reply_text("Qual o *prazo*? (ex: 2025-12-31) ou /pular:", parse_mode="Markdown", reply_markup=menu_cancelar())
    return OBJ_PRAZO


async def receber_prazo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prazo = None if update.message.text == "/pular" else update.message.text
    ud = context.user_data
    obj_id = execute(
        "INSERT INTO objetivos (titulo, meta_valor, unidade, prazo) VALUES (?,?,?,?)",
        (ud["obj_titulo"], ud["obj_meta"], ud["obj_unidade"], prazo),
    )
    gerar_todos()
    await update.message.reply_text(
        f"🎯 *Objetivo criado!*\n\n"
        f"*{ud['obj_titulo']}*\n"
        f"Meta: {ud['obj_meta']:.2f} {ud['obj_unidade']}\n"
        f"Prazo: {prazo or 'Sem prazo'}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="menu_inicio")]]),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def atu_escolher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    obj_id = int(query.data.replace("obj_sel:", ""))
    obj = fetch_one("SELECT * FROM objetivos WHERE id=?", (obj_id,))
    context.user_data["atu_obj"] = obj
    pct = (obj["valor_atual"] / obj["meta_valor"] * 100) if obj["meta_valor"] else 0
    await query.edit_message_text(
        f"✏️ *{obj['titulo']}*\n\n"
        f"Progresso atual: {obj['valor_atual']:.2f}/{obj['meta_valor']:.2f} {obj['unidade']} ({pct:.0f}%)\n\n"
        f"Digite o *novo valor acumulado total* (não o incremento):",
        parse_mode="Markdown",
        reply_markup=menu_cancelar(),
    )
    return ATU_VALOR


async def atu_receber_valor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Valor inválido:", reply_markup=menu_cancelar())
        return ATU_VALOR
    context.user_data["atu_valor"] = valor
    await update.message.reply_text("Adicione uma nota (ou /pular):", reply_markup=menu_cancelar())
    return ATU_NOTA


async def atu_receber_nota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nota = "" if update.message.text == "/pular" else update.message.text
    ud = context.user_data
    obj = ud["atu_obj"]
    novo_valor = ud["atu_valor"]
    execute("UPDATE objetivos SET valor_atual=? WHERE id=?", (novo_valor, obj["id"]))
    execute(
        "INSERT INTO objetivos_historico (objetivo_id, valor_registrado, nota) VALUES (?,?,?)",
        (obj["id"], novo_valor, nota),
    )
    if novo_valor >= obj["meta_valor"]:
        execute("UPDATE objetivos SET status='concluido' WHERE id=?", (obj["id"],))
        msg_extra = "\n\n🏆 *OBJETIVO CONCLUÍDO!* Parabéns!"
    else:
        msg_extra = ""
    gerar_todos()
    pct = (novo_valor / obj["meta_valor"] * 100) if obj["meta_valor"] else 0
    bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
    await update.message.reply_text(
        f"✅ *Progresso atualizado!*\n\n"
        f"*{obj['titulo']}*\n"
        f"[{bar}] {pct:.0f}%\n"
        f"{novo_valor:.2f}/{obj['meta_valor']:.2f} {obj['unidade']}{msg_extra}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="menu_inicio")]]),
    )
    context.user_data.clear()
    return ConversationHandler.END


def conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(obj_novo_titulo, pattern="^obj_novo$"),
            CallbackQueryHandler(iniciar_atualizar, pattern="^obj_atualizar$"),
        ],
        states={
            OBJ_TITULO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_titulo)],
            OBJ_META: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_meta)],
            OBJ_UNIDADE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_unidade),
                MessageHandler(filters.COMMAND, receber_unidade),
            ],
            OBJ_PRAZO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_prazo),
                MessageHandler(filters.COMMAND, receber_prazo),
            ],
            ATU_ESCOLHER: [CallbackQueryHandler(atu_escolher, pattern="^obj_sel:")],
            ATU_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, atu_receber_valor)],
            ATU_NOTA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, atu_receber_nota),
                MessageHandler(filters.COMMAND, atu_receber_nota),
            ],
        },
        fallbacks=[CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancelar$")],
        per_message=False,
    )
