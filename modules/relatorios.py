from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from reports.generator import gerar_todos, EXPORTS_DIR


async def handle_relatorio(query, context, data: str):
    gerar_todos()

    if data == "rel_financeiro":
        from database.db import fetch_one
        saldo = fetch_one("SELECT COALESCE(SUM(CASE WHEN tipo='receita' THEN valor ELSE -valor END),0) AS s FROM transacoes")["s"]
        rec = fetch_one("SELECT COALESCE(SUM(valor),0) AS s FROM transacoes WHERE tipo='receita'")["s"]
        desp = fetch_one("SELECT COALESCE(SUM(valor),0) AS s FROM transacoes WHERE tipo='despesa'")["s"]
        top = fetch_one(
            "SELECT categoria, SUM(valor) AS t FROM transacoes WHERE tipo='despesa' GROUP BY categoria ORDER BY t DESC LIMIT 1"
        )
        top_cat = f"{top['categoria']} (R$ {top['t']:.2f})" if top else "—"
        await query.edit_message_text(
            f"📊 *Resumo Financeiro*\n\n"
            f"✅ Total Receitas: R$ {rec:.2f}\n"
            f"❌ Total Despesas: R$ {desp:.2f}\n"
            f"💰 Saldo: R$ {saldo:.2f}\n\n"
            f"🔝 Maior categoria: {top_cat}\n\n"
            f"_Arquivos CSV/Excel atualizados em `reports/exports/`_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="menu_relatorio")]]),
        )
        return

    if data == "rel_km":
        from database.db import fetch_one
        km = fetch_one("SELECT COALESCE(SUM(km_percorridos),0) AS s FROM km_registros WHERE tipo='viagem'")["s"]
        gasto = fetch_one("SELECT COALESCE(SUM(custo_total),0) AS s FROM km_registros WHERE tipo='abastecimento'")["s"]
        await query.edit_message_text(
            f"🚗 *Resumo KM*\n\n"
            f"Total rodado: *{km:.0f} km*\n"
            f"Total combustível: *R$ {gasto:.2f}*\n\n"
            f"_Arquivos CSV/Excel atualizados em `reports/exports/`_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="menu_relatorio")]]),
        )
        return

    ext = "csv" if data == "rel_csv" else "xlsx"
    files = list(EXPORTS_DIR.glob(f"*.{ext}"))
    if not files:
        await query.edit_message_text(
            f"⚠️ Nenhum arquivo {ext.upper()} encontrado. Registre dados primeiro.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="menu_relatorio")]]),
        )
        return

    await query.edit_message_text(
        f"📤 Enviando {len(files)} arquivo(s) {ext.upper()}...",
        reply_markup=None,
    )
    for f in files:
        with open(f, "rb") as fh:
            await query.message.reply_document(document=fh, filename=f.name)
