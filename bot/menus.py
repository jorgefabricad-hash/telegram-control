from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def menu_principal() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Financeiro", callback_data="menu_financeiro"),
            InlineKeyboardButton("💸 Despesas", callback_data="menu_despesas"),
        ],
        [
            InlineKeyboardButton("🚗 KM / Veículo", callback_data="menu_km"),
            InlineKeyboardButton("🎯 Objetivos", callback_data="menu_objetivos"),
        ],
        [
            InlineKeyboardButton("📊 Relatório", callback_data="menu_relatorio"),
            InlineKeyboardButton("📁 Arquivos", callback_data="menu_arquivos"),
        ],
        [
            InlineKeyboardButton("💻 Executar Comando", callback_data="menu_cmd"),
        ],
    ])


def menu_financeiro() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Lançar Receita", callback_data="fin_receita"),
            InlineKeyboardButton("➖ Lançar Despesa", callback_data="fin_despesa"),
        ],
        [
            InlineKeyboardButton("📈 Ver Saldo", callback_data="fin_saldo"),
            InlineKeyboardButton("📋 Extrato", callback_data="fin_extrato"),
        ],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_inicio")],
    ])


def menu_km() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⛽ Abastecimento", callback_data="km_abastecimento"),
            InlineKeyboardButton("🛣️ Registrar Viagem", callback_data="km_viagem"),
        ],
        [
            InlineKeyboardButton("📊 Resumo KM", callback_data="km_resumo"),
        ],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_inicio")],
    ])


def menu_objetivos() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Novo Objetivo", callback_data="obj_novo"),
            InlineKeyboardButton("📋 Ver Objetivos", callback_data="obj_listar"),
        ],
        [
            InlineKeyboardButton("✏️ Atualizar Progresso", callback_data="obj_atualizar"),
        ],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_inicio")],
    ])


def menu_relatorio() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📁 Gerar CSV", callback_data="rel_csv"),
            InlineKeyboardButton("📊 Gerar Excel", callback_data="rel_excel"),
        ],
        [
            InlineKeyboardButton("💰 Resumo Financeiro", callback_data="rel_financeiro"),
            InlineKeyboardButton("🚗 Resumo KM", callback_data="rel_km"),
        ],
        [InlineKeyboardButton("🔙 Voltar", callback_data="menu_inicio")],
    ])


def menu_cancelar() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],
    ])


def menu_arquivos_nav(path: str = "") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Voltar", callback_data=f"arq_voltar:{path}")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],
    ])
