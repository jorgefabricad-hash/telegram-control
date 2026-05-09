from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from config import ALLOWED_USER_IDS
from bot.menus import menu_principal
from modules import financeiro, despesas, km, objetivos, arquivos, comandos


def only_owner(func):
    async def wrapper(update: Update, context):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USER_IDS:
            if update.message:
                await update.message.reply_text("⛔ Acesso negado.")
            elif update.callback_query:
                await update.callback_query.answer("⛔ Acesso negado.", show_alert=True)
            return ConversationHandler.END
        return await func(update, context)
    wrapper.__name__ = func.__name__
    return wrapper


@only_owner
async def start(update: Update, context):
    await update.message.reply_text(
        "🏠 *Painel de Controle Pessoal*\n\nEscolha uma categoria:",
        parse_mode="Markdown",
        reply_markup=menu_principal(),
    )


@only_owner
async def menu_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_inicio":
        await query.edit_message_text(
            "🏠 *Painel de Controle Pessoal*\n\nEscolha uma categoria:",
            parse_mode="Markdown",
            reply_markup=menu_principal(),
        )
    elif data == "menu_financeiro":
        await financeiro.show_menu(query)
    elif data in ("fin_receita", "fin_despesa", "fin_saldo", "fin_extrato"):
        await financeiro.handle_callback(query, context, data)
    elif data == "menu_despesas":
        await despesas.show_menu(update, context)
    elif data == "menu_km":
        await km.show_menu(query)
    elif data in ("km_abastecimento", "km_viagem", "km_resumo"):
        await km.handle_callback(query, context, data)
    elif data == "menu_objetivos":
        await objetivos.show_menu(query)
    elif data in ("obj_novo", "obj_listar", "obj_atualizar"):
        await objetivos.handle_callback(query, context, data)
    elif data == "menu_relatorio":
        from bot.menus import menu_relatorio
        await query.edit_message_text(
            "📊 *Relatórios*\n\nEscolha o tipo:",
            parse_mode="Markdown",
            reply_markup=menu_relatorio(),
        )
    elif data in ("rel_csv", "rel_excel", "rel_financeiro", "rel_km"):
        from modules.relatorios import handle_relatorio
        await handle_relatorio(query, context, data)
    elif data == "menu_arquivos":
        await arquivos.show_menu(update, context)
    elif data.startswith("arq_"):
        await arquivos.handle_callback(query, context, data)
    elif data == "menu_cmd":
        await comandos.show_menu(update, context)
    elif data == "cancelar":
        await query.edit_message_text("❌ Operação cancelada.")
        context.user_data.clear()


def register(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))

    app.add_handler(financeiro.conversation_handler())
    app.add_handler(despesas.conversation_handler())
    app.add_handler(km.conversation_handler())
    app.add_handler(objetivos.conversation_handler())
    app.add_handler(comandos.conversation_handler())
    app.add_handler(arquivos.conversation_handler())

    app.add_handler(CallbackQueryHandler(menu_callback))
