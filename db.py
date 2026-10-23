
import re

import pandas as pd
import psycopg
import streamlit as st
from psycopg import sql
from psycopg.rows import dict_row

# CONFIGURAÇÃO DAS TABELAS

TABELAS_PERMITIDAS = {
    "compras": {
        "id": "id_compra",
        "colunas": [
            "id_compra",
            "cliente_id",
            "data_compra",
            "valor_total",
            "metodo_pagamento",
        ],
    },
    "pedidos": {
        "id": "id_pedido",
        "colunas": [
            "id_pedido",
            "id_compra",
            "produto_id",
            "quantidade",
            "preco_unitario",
        ],
    },
    "produtos": {
        "id": "produto_id",
        "colunas": [
            "produto_id",
            "nome_produto",
            "categoria",
            "preco_unitario",
        ],
    },
}

COLUNAS_INTEIRAS = {
    "compras": ["id_compra", "cliente_id"],
    "pedidos": ["id_pedido", "id_compra", "quantidade"],
    "produtos": [],
}


# CONEXÃO COM O BANCO

def conectar_banco():
    """Abre uma conexão com o PostgreSQL usando os secrets do Streamlit."""
    config = st.secrets["connections"]["postgresql"]

    return psycopg.connect(
        host=config["host"],
        port=config["port"],
        dbname=config["database"],
        user=config["username"],
        password=config["password"],
        sslmode="require",
        connect_timeout=10,
    )


def testar_conexao():
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            return cursor.fetchone()[0] == 1

# INICIALIZAÇÃO DOS PRODUTOS

def inicializar_tabela_produtos():
    """
    Cria a tabela de produtos caso não exista e registra produtos
    encontrados nos pedidos antigos, preservando seu histórico.
    """
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS produtos (
                    produto_id TEXT PRIMARY KEY,
                    nome_produto TEXT NOT NULL,
                    categoria TEXT NOT NULL DEFAULT 'Geral',
                    preco_unitario NUMERIC(12,2) NOT NULL DEFAULT 0,
                    CONSTRAINT produtos_preco_nao_negativo
                        CHECK (preco_unitario >= 0)
                );
            """)

            cursor.execute("""
                INSERT INTO produtos (
                    produto_id,
                    nome_produto,
                    categoria,
                    preco_unitario
                )
                SELECT DISTINCT
                    p.produto_id::text,
                    p.produto_id::text,
                    'Importado dos pedidos',
                    0
                FROM pedidos p
                WHERE p.produto_id IS NOT NULL
                  AND BTRIM(p.produto_id::text) <> ''
                ON CONFLICT (produto_id) DO NOTHING;
            """)


# CONSULTAS

def listar_registros(tabela):
    """Retorna os registros de uma tabela em ordem de ID."""
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")

    coluna_id = TABELAS_PERMITIDAS[tabela]["id"]

    with conectar_banco() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                sql.SQL("SELECT * FROM {} ORDER BY {}").format(
                    sql.Identifier(tabela),
                    sql.Identifier(coluna_id),
                )
            )
            return cursor.fetchall()


def proximo_id(tabela):
    """Gera o próximo ID numérico para compras ou pedidos."""
    if tabela not in ("compras", "pedidos"):
        raise ValueError(
            "Geração numérica de ID não disponível para esta tabela."
        )

    coluna_id = TABELAS_PERMITIDAS[tabela]["id"]

    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "SELECT COALESCE(MAX({}), 0) + 1 FROM {}"
                ).format(
                    sql.Identifier(coluna_id),
                    sql.Identifier(tabela),
                )
            )
            return int(cursor.fetchone()[0])


def proximo_produto_id():
    """Gera o próximo ID no formato P001, P002, P003..."""
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT produto_id
                FROM produtos
                WHERE produto_id ~ '^P[0-9]+$';
            """)

            numeros = [
                int(re.search(r"\d+", row[0]).group())
                for row in cursor.fetchall()
            ]

            proximo = max(numeros, default=0) + 1
            return f"P{proximo:03d}"


def proximo_cliente_id():
    """Retorna o próximo ID numérico de cliente."""
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(MAX(cliente_id), 0) + 1
                FROM compras;
            """)
            return int(cursor.fetchone()[0])


# VALIDAÇÕES

def _validar_valores(tabela, dados):
    campos_monetarios = {
        "compras": ["valor_total"],
        "pedidos": ["preco_unitario"],
        "produtos": ["preco_unitario"],
    }

    for campo in campos_monetarios.get(tabela, []):
        if campo not in dados:
            continue

        try:
            valor = float(dados[campo])
        except (TypeError, ValueError):
            raise ValueError(
                f"O campo {campo.replace('_', ' ')} "
                "deve conter um valor monetário válido."
            )

        if (
            not pd.notna(valor)
            or valor < 0
            or valor >= 10_000_000_000
        ):
            raise ValueError(
                f"O campo {campo.replace('_', ' ')} deve ser "
                "um valor entre R$ 0,00 e R$ 9.999.999.999,99."
            )

        dados[campo] = round(valor, 2)

# CADASTRAR

def inserir_registro(tabela, dados):
    """Cadastra um registro e confirma a operação no banco."""
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")

    permitidas = TABELAS_PERMITIDAS[tabela]["colunas"]

    if not dados or any(campo not in permitidas for campo in dados):
        raise ValueError("Foram enviados campos inválidos.")

    dados = dict(dados)
    _validar_valores(tabela, dados)

    colunas = list(dados)

    comando = sql.SQL(
        "INSERT INTO {} ({}) VALUES ({})"
    ).format(
        sql.Identifier(tabela),
        sql.SQL(", ").join(
            sql.Identifier(coluna) for coluna in colunas
        ),
        sql.SQL(", ").join(
            sql.Placeholder() for _ in colunas
        ),
    )

    valores = tuple(dados[coluna] for coluna in colunas)

    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(comando, valores)

# EDITAR

def atualizar_registro(tabela, id_valor, dados):
    """Atualiza os campos de um registro sem permitir alterar seu ID."""
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")

    config = TABELAS_PERMITIDAS[tabela]

    if (
        not dados
        or config["id"] in dados
        or any(campo not in config["colunas"] for campo in dados)
    ):
        raise ValueError("O ID principal não pode ser alterado.")

    dados = dict(dados)
    _validar_valores(tabela, dados)

    atribuicoes = sql.SQL(", ").join(
        sql.SQL("{} = {}").format(
            sql.Identifier(campo),
            sql.Placeholder(),
        )
        for campo in dados
    )

    comando = sql.SQL(
        "UPDATE {} SET {} WHERE {} = {}"
    ).format(
        sql.Identifier(tabela),
        atribuicoes,
        sql.Identifier(config["id"]),
        sql.Placeholder(),
    )

    valores = (*dados.values(), id_valor)

    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(comando, valores)
            return cursor.rowcount


# EXCLUIR

def excluir_registro(tabela, id_valor):
    """Exclui um registro pelo ID e retorna quantas linhas foram removidas."""
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")

    coluna_id = TABELAS_PERMITIDAS[tabela]["id"]

    comando = sql.SQL(
        "DELETE FROM {} WHERE {} = {}"
    ).format(
        sql.Identifier(tabela),
        sql.Identifier(coluna_id),
        sql.Placeholder(),
    )

    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(comando, (id_valor,))
            return cursor.rowcount

# IMPORTAÇÃO DE DATAFRAME

def importar_dataframe_para_supabase(dataframe, tabela):
    """
    Valida e importa registros em lote.
    IDs já existentes não são sobrescritos.
    """

    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Selecione uma tabela válida.")

    config = TABELAS_PERMITIDAS[tabela]
    id_coluna = config["id"]
    colunas = config["colunas"]

    df = dataframe.copy()
    df.columns = [str(coluna).strip() for coluna in df.columns]

    faltantes = [
        coluna
        for coluna in colunas
        if coluna != id_coluna and coluna not in df.columns
    ]

    extras = [
        coluna for coluna in df.columns
        if coluna not in colunas
    ]

    if faltantes or extras:
        raise ValueError(
            f"Colunas ausentes: {faltantes or 'nenhuma'}. "
            f"Colunas não reconhecidas: {extras or 'nenhuma'}. "
            f"Esperadas: {colunas} (o ID principal pode ser omitido)."
        )

    if df.empty:
        return 0

    if id_coluna not in df.columns:
        df[id_coluna] = pd.NA

    # Geração de IDs

    if tabela in ("compras", "pedidos"):
        df[id_coluna] = pd.to_numeric(
            df[id_coluna],
            errors="coerce",
        )

        usados = {
            int(valor)
            for valor in df[id_coluna].dropna()
        }

        proximo = proximo_id(tabela)
        novos_ids = []

        for valor in df[id_coluna].tolist():
            if pd.isna(valor):
                while proximo in usados or proximo in novos_ids:
                    proximo += 1

                novos_ids.append(proximo)
                proximo += 1
            else:
                novos_ids.append(int(valor))

        df[id_coluna] = novos_ids

    else:
        df[id_coluna] = df[id_coluna].where(
            df[id_coluna].notna(),
            None,
        )

        proximo = proximo_produto_id()

        def gerar_produto():
            nonlocal proximo

            valor = proximo
            numero = int(valor[1:]) + 1
            proximo = f"P{numero:03d}"

            return valor

        df[id_coluna] = [
            str(valor).strip()
            if pd.notna(valor) and str(valor).strip()
            else gerar_produto()
            for valor in df[id_coluna]
        ]

# Validação das colunas inteiras

    for coluna in COLUNAS_INTEIRAS[tabela]:
        if coluna in df.columns:
            valores = pd.to_numeric(
                df[coluna],
                errors="raise",
            )

            if valores.isna().any():
                raise ValueError(
                    f"Preencha todos os valores da coluna {coluna}."
                )

            if (valores % 1 != 0).any():
                raise ValueError(
                    f"A coluna {coluna} deve conter números inteiros."
                )

            df[coluna] = valores.astype(int)

    # Validação de valores monetários
    if tabela == "compras":
        colunas_monetarias = ["valor_total"]
    else:
        colunas_monetarias = ["preco_unitario"]

    for coluna in colunas_monetarias:
        if coluna in df.columns:
            serie = (
                df[coluna]
                .astype(str)
                .str.replace("R$", "", regex=False)
                .str.replace(" ", "", regex=False)
            )

            # Aceita 1234.56 e 1.234,56.
            serie = serie.map(
                lambda valor:
                    valor.replace(".", "").replace(",", ".")
                    if "," in valor
                    else valor
            )

            df[coluna] = pd.to_numeric(
                serie,
                errors="raise",
            )

            if (
                df[coluna].isna().any()
                or (df[coluna] < 0).any()
                or (df[coluna] >= 10_000_000_000).any()
            ):
                raise ValueError(
                    f"A coluna {coluna} deve conter valores "
                    "monetários válidos até R$ 9.999.999.999,99."
                )

    # Validações específicas por tabela

    if tabela == "compras":
        df["data_compra"] = pd.to_datetime(
            df["data_compra"],
            errors="coerce",
        ).dt.date

        if (
            df["data_compra"].isna().any()
            or df["metodo_pagamento"].isna().any()
        ):
            raise ValueError(
                "Confira as datas e os métodos de pagamento: "
                "não podem ficar vazios."
            )

    elif tabela == "pedidos":
        if (
            df["produto_id"].isna().any()
            or df["quantidade"].le(0).any()
        ):
            raise ValueError(
                "Cada pedido precisa ter produto e quantidade "
                "maior que zero."
            )

    else:
        if (
            df["nome_produto"].isna().any()
            or df["nome_produto"].astype(str).str.strip().eq("").any()
        ):
            raise ValueError("Informe o nome de todos os produtos.")

        df["categoria"] = df["categoria"].fillna("Geral")

    # Remove IDs repetidos dentro do próprio arquivo.
    df = df.drop_duplicates(
        subset=[id_coluna],
        keep="first",
    )

    # Converte NaN/NaT para None, aceito pelo PostgreSQL.
    df = df.astype(object).where(pd.notna(df), None)

    registros = df[colunas].to_dict(orient="records")

    if not registros:
        return 0

    # INSERÇÃO EM LOTE

    comando = sql.SQL(
        "INSERT INTO {} ({}) VALUES ({}) "
        "ON CONFLICT ({}) DO NOTHING"
    ).format(
        sql.Identifier(tabela),
        sql.SQL(", ").join(
            sql.Identifier(coluna) for coluna in colunas
        ),
        sql.SQL(", ").join(
            sql.Placeholder() for _ in colunas
        ),
        sql.Identifier(id_coluna),
    )

    valores = [
        tuple(registro[coluna] for coluna in colunas)
        for registro in registros
    ]

    # Uma conexão e uma operação de lote em vez de um INSERT por linha.
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(comando, valores)
            return cursor.rowcount


def importar_csv_para_supabase(caminho_csv, tabela):
    """Lê um CSV e encaminha os dados para a importação validada."""
    dataframe = pd.read_csv(caminho_csv)
    return importar_dataframe_para_supabase(dataframe, tabela)
