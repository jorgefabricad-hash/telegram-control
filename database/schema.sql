CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL CHECK(tipo IN ('receita', 'despesa', 'ambos'))
);

CREATE TABLE IF NOT EXISTS transacoes (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL DEFAULT CURRENT_DATE,
    tipo TEXT NOT NULL CHECK(tipo IN ('receita', 'despesa')),
    valor NUMERIC(12,2) NOT NULL,
    categoria TEXT NOT NULL,
    descricao TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS km_registros (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL DEFAULT CURRENT_DATE,
    tipo TEXT NOT NULL CHECK(tipo IN ('abastecimento', 'viagem')),
    km_inicial NUMERIC(10,2),
    km_final NUMERIC(10,2),
    km_percorridos NUMERIC(10,2),
    litros NUMERIC(8,3),
    preco_litro NUMERIC(8,3),
    custo_total NUMERIC(10,2),
    descricao TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS objetivos (
    id SERIAL PRIMARY KEY,
    titulo TEXT NOT NULL,
    descricao TEXT,
    meta_valor NUMERIC(12,2) NOT NULL,
    valor_atual NUMERIC(12,2) NOT NULL DEFAULT 0,
    unidade TEXT DEFAULT '',
    prazo DATE,
    status TEXT NOT NULL DEFAULT 'ativo' CHECK(status IN ('ativo', 'concluido', 'cancelado')),
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS objetivos_historico (
    id SERIAL PRIMARY KEY,
    objetivo_id INTEGER NOT NULL REFERENCES objetivos(id),
    data DATE NOT NULL DEFAULT CURRENT_DATE,
    valor_registrado NUMERIC(12,2) NOT NULL,
    nota TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

INSERT INTO categorias (nome, tipo) VALUES
    ('Salário', 'receita'),
    ('Freelance', 'receita'),
    ('Investimento', 'receita'),
    ('Outros (receita)', 'receita'),
    ('Alimentação', 'despesa'),
    ('Transporte', 'despesa'),
    ('Saúde', 'despesa'),
    ('Educação', 'despesa'),
    ('Lazer', 'despesa'),
    ('Moradia', 'despesa'),
    ('Combustível', 'despesa'),
    ('Manutenção veículo', 'despesa'),
    ('Outros (despesa)', 'despesa')
ON CONFLICT (nome) DO NOTHING;
