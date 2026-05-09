import pandas as pd
from pathlib import Path
from config import EXPORTS_DIR
from database.db import fetch_all

EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _df_transacoes() -> pd.DataFrame:
    rows = fetch_all("SELECT id, data, tipo, valor, categoria, descricao, criado_em FROM transacoes ORDER BY data DESC")
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["id","data","tipo","valor","categoria","descricao","criado_em"])


def _df_km() -> pd.DataFrame:
    rows = fetch_all("SELECT id, data, tipo, km_inicial, km_final, km_percorridos, litros, preco_litro, custo_total, descricao FROM km_registros ORDER BY data DESC")
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["id","data","tipo","km_inicial","km_final","km_percorridos","litros","preco_litro","custo_total","descricao"])


def _df_objetivos() -> pd.DataFrame:
    rows = fetch_all("SELECT id, titulo, descricao, meta_valor, valor_atual, unidade, prazo, status, criado_em FROM objetivos ORDER BY status, prazo")
    if rows:
        df = pd.DataFrame(rows)
        df["progresso_pct"] = (df["valor_atual"] / df["meta_valor"] * 100).round(1)
        return df
    return pd.DataFrame(columns=["id","titulo","descricao","meta_valor","valor_atual","unidade","prazo","status","criado_em","progresso_pct"])


def _df_resumo_mensal() -> pd.DataFrame:
    rows = fetch_all(
        "SELECT TO_CHAR(data,'YYYY-MM') AS mes, "
        "SUM(CASE WHEN tipo='receita' THEN valor ELSE 0 END)::float AS receitas, "
        "SUM(CASE WHEN tipo='despesa' THEN valor ELSE 0 END)::float AS despesas, "
        "SUM(CASE WHEN tipo='receita' THEN valor ELSE -valor END)::float AS saldo "
        "FROM transacoes GROUP BY mes ORDER BY mes"
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["mes","receitas","despesas","saldo"])


def _df_por_categoria() -> pd.DataFrame:
    rows = fetch_all(
        "SELECT categoria, tipo, SUM(valor) AS total, COUNT(*) AS qtd "
        "FROM transacoes GROUP BY categoria, tipo ORDER BY tipo, total DESC"
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["categoria","tipo","total","qtd"])


def gerar_csv():
    _df_transacoes().to_csv(EXPORTS_DIR / "transacoes.csv", index=False, encoding="utf-8-sig")
    _df_km().to_csv(EXPORTS_DIR / "km.csv", index=False, encoding="utf-8-sig")
    _df_objetivos().to_csv(EXPORTS_DIR / "objetivos.csv", index=False, encoding="utf-8-sig")
    _df_resumo_mensal().to_csv(EXPORTS_DIR / "resumo_mensal.csv", index=False, encoding="utf-8-sig")
    _df_por_categoria().to_csv(EXPORTS_DIR / "por_categoria.csv", index=False, encoding="utf-8-sig")


def gerar_excel():
    path = EXPORTS_DIR / "controle_pessoal.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        _df_transacoes().to_excel(writer, sheet_name="Transações", index=False)
        _df_km().to_excel(writer, sheet_name="KM Veículo", index=False)
        _df_objetivos().to_excel(writer, sheet_name="Objetivos", index=False)
        _df_resumo_mensal().to_excel(writer, sheet_name="Resumo Mensal", index=False)
        _df_por_categoria().to_excel(writer, sheet_name="Por Categoria", index=False)


def gerar_todos():
    try:
        gerar_csv()
        gerar_excel()
    except Exception:
        pass
