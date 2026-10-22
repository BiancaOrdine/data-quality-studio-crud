
import streamlit as st
import psycopg
import pandas as pd

from pathlib import Path
from psycopg import sql
from psycopg.rows import dict_row


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
}


def conectar_banco():
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


def listar_registros(tabela):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")

    with conectar_banco() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                sql.SQL("SELECT * FROM {} ORDER BY {}").format(
                    sql.Identifier(tabela),
                    sql.Identifier(TABELAS_PERMITIDAS[tabela]["id"]),
                )
            )
            return cursor.fetchall()


def inserir_registro(tabela, dados):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")

    colunas_permitidas = TABELAS_PERMITIDAS[tabela]["colunas"]

    if not dados or any(c not in colunas_permitidas for c in dados):
        raise ValueError("Colunas inválidas.")

    colunas = list(dados.keys())

    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(tabela),
                    sql.SQL(", ").join(
                        sql.Identifier(c) for c in colunas
                    ),
                    sql.SQL(", ").join(
                        sql.Placeholder() for _ in colunas
                    ),
                ),
                tuple(dados[c] for c in colunas),
            )


def atualizar_registro(tabela, id_valor, dados):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")

    config = TABELAS_PERMITIDAS[tabela]
    id_coluna = config["id"]
    colunas_permitidas = config["colunas"]

    if (
        not dados
        or id_coluna in dados
        or any(c not in colunas_permitidas for c in dados)
    ):
        raise ValueError("Dados inválidos para atualização.")

    atribuicoes = sql.SQL(", ").join(
        sql.SQL("{} = {}").format(
            sql.Identifier(c), sql.Placeholder()
        )
        for c in dados
    )

    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("UPDATE {} SET {} WHERE {} = {}").format(
                    sql.Identifier(tabela),
                    atribuicoes,
                    sql.Identifier(id_coluna),
                    sql.Placeholder(),
                ),
                (*dados.values(), id_valor),
            )
            return cursor.rowcount


def excluir_registro(tabela, id_valor):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")

    id_coluna = TABELAS_PERMITIDAS[tabela]["id"]

    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("DELETE FROM {} WHERE {} = {}").format(
                    sql.Identifier(tabela),
                    sql.Identifier(id_coluna),
                    sql.Placeholder(),
                ),
                (id_valor,),
            )
            return cursor.rowcount


def importar_csv_para_supabase(caminho_csv, tabela):
    mapeamentos = {
        "compras": {
            "id_compra": "id_compra",
            "cliente_id": "cliente_id",
            "data_compra": "data_compra",
            "valor_total": "valor_total",
            "metodo_pagamento": "metodo_pagamento",
        },
        "pedidos": {
            "id_pedido": "id_pedido",
            "id_compra": "id_compra",
            "id_do_produto": "produto_id",
            "quantidade": "quantidade",
            "preco_unitário": "preco_unitario",
        },
    }

    if tabela not in mapeamentos:
        raise ValueError("Tabela não permitida.")

    df = pd.read_csv(caminho_csv)
    df.columns = df.columns.str.strip()

    mapa = mapeamentos[tabela]

    if set(df.columns) != set(mapa.keys()):
        raise ValueError(
            f"Colunas inesperadas em {caminho_csv}. "
            f"Esperadas: {list(mapa.keys())}. "
            f"Encontradas: {list(df.columns)}"
        )

    df = df.rename(columns=mapa)

    id_coluna = TABELAS_PERMITIDAS[tabela]["id"]

    if df[id_coluna].isna().any():
        raise ValueError(
            f"O CSV contém IDs vazios na coluna {id_coluna}."
        )

    df = df.drop_duplicates(subset=[id_coluna], keep="first")
    df = df.astype(object).where(pd.notna(df), None)

    colunas = list(mapa.values())
    registros = df.to_dict(orient="records")

    if not registros:
        return 0

    inseridos = 0

    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            for registro in registros:
                cursor.execute(
                    sql.SQL(
                        "INSERT INTO {} ({}) VALUES ({}) "
                        "ON CONFLICT ({}) DO NOTHING"
                    ).format(
                        sql.Identifier(tabela),
                        sql.SQL(", ").join(
                            sql.Identifier(c) for c in colunas
                        ),
                        sql.SQL(", ").join(
                            sql.Placeholder() for _ in colunas
                        ),
                        sql.Identifier(id_coluna),
                    ),
                    tuple(registro[c] for c in colunas),
                )

                if cursor.rowcount == 1:
                    inseridos += 1

    return inseridos
