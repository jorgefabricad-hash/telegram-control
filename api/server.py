from fastapi import APIRouter
from database.db import fetch_all, fetch_one

router = APIRouter()


@router.get("/")
def root():
    return {"status": "ok", "endpoints": ["/transacoes", "/km", "/objetivos", "/resumo", "/categorias"]}


@router.get("/transacoes")
def transacoes(tipo: str = None, categoria: str = None, limit: int = 500):
    query = "SELECT * FROM transacoes WHERE 1=1"
    params = []
    if tipo:
        query += " AND tipo=?"
        params.append(tipo)
    if categoria:
        query += " AND categoria=?"
        params.append(categoria)
    query += " ORDER BY data DESC, criado_em DESC LIMIT ?"
    params.append(limit)
    return fetch_all(query, tuple(params))


@router.get("/km")
def km(tipo: str = None, limit: int = 500):
    query = "SELECT * FROM km_registros WHERE 1=1"
    params = []
    if tipo:
        query += " AND tipo=?"
        params.append(tipo)
    query += " ORDER BY data DESC LIMIT ?"
    params.append(limit)
    return fetch_all(query, tuple(params))


@router.get("/objetivos")
def objetivos(status: str = None):
    query = "SELECT * FROM objetivos WHERE 1=1"
    params = []
    if status:
        query += " AND status=?"
        params.append(status)
    query += " ORDER BY criado_em DESC"
    return fetch_all(query, tuple(params))


@router.get("/objetivos/{objetivo_id}/historico")
def historico_objetivo(objetivo_id: int):
    return fetch_all(
        "SELECT * FROM objetivos_historico WHERE objetivo_id=? ORDER BY data ASC",
        (objetivo_id,),
    )


@router.get("/categorias")
def categorias():
    return fetch_all("SELECT * FROM categorias ORDER BY tipo, nome")


@router.get("/resumo")
def resumo():
    saldo = fetch_one(
        "SELECT COALESCE(SUM(CASE WHEN tipo='receita' THEN valor ELSE -valor END),0)::float AS s FROM transacoes"
    )["s"]
    receitas = fetch_one("SELECT COALESCE(SUM(valor),0)::float AS s FROM transacoes WHERE tipo='receita'")["s"]
    despesas = fetch_one("SELECT COALESCE(SUM(valor),0)::float AS s FROM transacoes WHERE tipo='despesa'")["s"]
    km_total = fetch_one("SELECT COALESCE(SUM(km_percorridos),0)::float AS s FROM km_registros WHERE tipo='viagem'")["s"]
    combustivel = fetch_one("SELECT COALESCE(SUM(custo_total),0)::float AS s FROM km_registros WHERE tipo='abastecimento'")["s"]
    obj_ativos = fetch_one("SELECT COUNT(*)::int AS n FROM objetivos WHERE status='ativo'")["n"]
    obj_concluidos = fetch_one("SELECT COUNT(*)::int AS n FROM objetivos WHERE status='concluido'")["n"]

    despesas_mes = fetch_all(
        "SELECT TO_CHAR(data,'YYYY-MM') AS mes, SUM(valor)::float AS total "
        "FROM transacoes WHERE tipo='despesa' GROUP BY mes ORDER BY mes DESC LIMIT 12"
    )
    receitas_mes = fetch_all(
        "SELECT TO_CHAR(data,'YYYY-MM') AS mes, SUM(valor)::float AS total "
        "FROM transacoes WHERE tipo='receita' GROUP BY mes ORDER BY mes DESC LIMIT 12"
    )
    por_categoria = fetch_all(
        "SELECT categoria, tipo, SUM(valor)::float AS total FROM transacoes GROUP BY categoria, tipo ORDER BY total DESC"
    )

    return {
        "saldo": saldo,
        "receitas_total": receitas,
        "despesas_total": despesas,
        "km_total": km_total,
        "combustivel_total": combustivel,
        "objetivos_ativos": obj_ativos,
        "objetivos_concluidos": obj_concluidos,
        "despesas_por_mes": despesas_mes,
        "receitas_por_mes": receitas_mes,
        "por_categoria": por_categoria,
    }
