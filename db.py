import pandas as pd
import psycopg
import streamlit as st

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


COLUNAS_INTEIRAS = {
    "compras": ["id_compra", "cliente_id"],
    "pedidos": ["id_pedido", "id_compra", "quantidade"],
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


def proximo_id(tabela):
    """Retorna MAX(ID) + 1 para compras ou pedidos."""
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")

    id_coluna = TABELAS_PERMITIDAS[tabela]["id"]
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT COALESCE(MAX({}), 0) + 1 FROM {}").format(
                    sql.Identifier(id_coluna),
                    sql.Identifier(tabela),
                )
            )
            return int(cursor.fetchone()[0])


def proximo_cliente_id():
    """Gera o próximo cliente_id com base nos IDs já usados em compras."""
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(cliente_id), 0) + 1 FROM compras")
            return int(cursor.fetchone()[0])


def inserir_registro(tabela, dados):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")

    colunas_permitidas = TABELAS_PERMITIDAS[tabela]["colunas"]
    if not dados or any(coluna not in colunas_permitidas for coluna in dados):
        raise ValueError("Colunas inválidas.")

    colunas = list(dados.keys())
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(tabela),
                    sql.SQL(", ").join(sql.Identifier(c) for c in colunas),
                    sql.SQL(", ").join(sql.Placeholder() for _ in colunas),
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
        or any(coluna not in colunas_permitidas for coluna in dados)
    ):
        raise ValueError("Dados inválidos para atualização.")

    atribuicoes = sql.SQL(", ").join(
        sql.SQL("{} = {}").format(sql.Identifier(coluna), sql.Placeholder())
        for coluna in dados
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


def importar_dataframe_para_supabase(dataframe, tabela):
    """Importa um DataFrame para uma tabela, gerando IDs ausentes e ignorando IDs já existentes."""
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")

    config = TABELAS_PERMITIDAS[tabela]
    id_coluna = config["id"]
    colunas_esperadas = config["colunas"]

    df = dataframe.copy()
    df.columns = [str(coluna).strip() for coluna in df.columns]

    colunas_obrigatorias = [coluna for coluna in colunas_esperadas if coluna != id_coluna]
    faltantes = [coluna for coluna in colunas_obrigatorias if coluna not in df.columns]
    extras = [coluna for coluna in df.columns if coluna not in colunas_esperadas]

    if faltantes or extras:
        partes = []
        if faltantes:
            partes.append(f"Colunas obrigatórias ausentes: {faltantes}")
        if extras:
            partes.append(f"Colunas não reconhecidas: {extras}")
        partes.append(f"Colunas esperadas: {colunas_esperadas} (o ID principal pode ser omitido)")
        raise ValueError(". ".join(partes))

    if df.empty:
        return 0

    if id_coluna not in df.columns:
        df[id_coluna] = pd.NA

    # Gera IDs sequenciais para linhas sem ID e normaliza IDs fornecidos no CSV.
    df[id_coluna] = pd.to_numeric(df[id_coluna], errors="coerce")
    ids_existentes_no_arquivo = {
        int(valor) for valor in df[id_coluna].dropna().tolist()
    }
    proximo = proximo_id(tabela)
    ids_gerados = []
    for valor in df[id_coluna].tolist():
        if pd.isna(valor):
            while proximo in ids_existentes_no_arquivo or proximo in ids_gerados:
                proximo += 1
            ids_gerados.append(proximo)
            proximo += 1
        else:
            ids_gerados.append(int(valor))
    df[id_coluna] = ids_gerados

    # Converte campos numéricos para tipos que o PostgreSQL aceita com segurança.
    for coluna in COLUNAS_INTEIRAS[tabela]:
        if coluna in df.columns:
            valores = pd.to_numeric(df[coluna], errors="raise")
            if valores.isna().any():
                raise ValueError(f"A coluna {coluna} contém valores vazios.")
            df[coluna] = valores.astype(int)

    colunas_decimais = ["valor_total"] if tabela == "compras" else ["preco_unitario"]
    for coluna in colunas_decimais:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="raise")
            if df[coluna].isna().any():
                raise ValueError(f"A coluna {coluna} contém valores vazios.")

    if tabela == "compras":
        if df["data_compra"].isna().any():
            raise ValueError("A coluna data_compra contém valores vazios.")
        if df["metodo_pagamento"].isna().any():
            raise ValueError("A coluna metodo_pagamento contém valores vazios.")
    else:
        if df["produto_id"].isna().any():
            raise ValueError("A coluna produto_id contém valores vazios.")

    df = df.drop_duplicates(subset=[id_coluna], keep="first")
    df = df.astype(object).where(pd.notna(df), None)
    registros = df[colunas_esperadas].to_dict(orient="records")
    inseridos = 0

    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            for registro in registros:
                cursor.execute(
                    sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO NOTHING").format(
                        sql.Identifier(tabela),
                        sql.SQL(", ").join(sql.Identifier(c) for c in colunas_esperadas),
                        sql.SQL(", ").join(sql.Placeholder() for _ in colunas_esperadas),
                        sql.Identifier(id_coluna),
                    ),
                    tuple(registro[coluna] for coluna in colunas_esperadas),
                )
                if cursor.rowcount == 1:
                    inseridos += 1

    return inseridos


def importar_csv_para_supabase(caminho_csv, tabela):
    """Compatibilidade temporária com a versão anterior do app.py."""
    dataframe = pd.read_csv(caminho_csv)
    return importar_dataframe_para_supabase(dataframe, tabela)
