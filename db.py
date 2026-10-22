import re
import pandas as pd
import psycopg
import streamlit as st
from psycopg import sql
from psycopg.rows import dict_row

TABELAS_PERMITIDAS = {
    "compras": {"id": "id_compra", "colunas": ["id_compra", "cliente_id", "data_compra", "valor_total", "metodo_pagamento"]},
    "pedidos": {"id": "id_pedido", "colunas": ["id_pedido", "id_compra", "produto_id", "quantidade", "preco_unitario"]},
    "produtos": {"id": "produto_id", "colunas": ["produto_id", "nome_produto", "categoria", "preco_unitario"]},
}
COLUNAS_INTEIRAS = {
    "compras": ["id_compra", "cliente_id"],
    "pedidos": ["id_pedido", "id_compra", "quantidade"],
    "produtos": [],
}


def conectar_banco():
    config = st.secrets["connections"]["postgresql"]
    return psycopg.connect(host=config["host"], port=config["port"], dbname=config["database"], user=config["username"], password=config["password"], sslmode="require", connect_timeout=10)


def testar_conexao():
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            return cursor.fetchone()[0] == 1


def inicializar_tabela_produtos():
    """Cria a tabela de produtos se ela ainda não existir e preserva IDs já usados nos pedidos."""
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS produtos (
                    produto_id TEXT PRIMARY KEY,
                    nome_produto TEXT NOT NULL,
                    categoria TEXT NOT NULL DEFAULT 'Geral',
                    preco_unitario NUMERIC(12,2) NOT NULL DEFAULT 0,
                    CONSTRAINT produtos_preco_nao_negativo CHECK (preco_unitario >= 0)
                );
            """)
            # IDs antigos encontrados em pedidos são registrados para não quebrar o histórico.
            cursor.execute("""
                INSERT INTO produtos (produto_id, nome_produto, categoria, preco_unitario)
                SELECT DISTINCT p.produto_id::text, p.produto_id::text, 'Importado dos pedidos', 0
                FROM pedidos p
                WHERE p.produto_id IS NOT NULL AND BTRIM(p.produto_id::text) <> ''
                ON CONFLICT (produto_id) DO NOTHING;
            """)


def listar_registros(tabela):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")
    with conectar_banco() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(sql.SQL("SELECT * FROM {} ORDER BY {}").format(sql.Identifier(tabela), sql.Identifier(TABELAS_PERMITIDAS[tabela]["id"])))
            return cursor.fetchall()


def proximo_id(tabela):
    if tabela not in ("compras", "pedidos"):
        raise ValueError("Geração numérica de ID não disponível para esta tabela.")
    id_coluna = TABELAS_PERMITIDAS[tabela]["id"]
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql.SQL("SELECT COALESCE(MAX({}), 0) + 1 FROM {}").format(sql.Identifier(id_coluna), sql.Identifier(tabela)))
            return int(cursor.fetchone()[0])


def proximo_produto_id():
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT produto_id FROM produtos WHERE produto_id ~ '^P[0-9]+$'")
            numeros = [int(re.search(r"\d+", row[0]).group()) for row in cursor.fetchall()]
            return f"P{(max(numeros, default=0) + 1):03d}"


def proximo_cliente_id():
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(cliente_id), 0) + 1 FROM compras")
            return int(cursor.fetchone()[0])


def _validar_valores(tabela, dados):
    campos_monetarios = {"compras": ["valor_total"], "pedidos": ["preco_unitario"], "produtos": ["preco_unitario"]}
    for campo in campos_monetarios.get(tabela, []):
        if campo in dados:
            valor = float(dados[campo])
            if not pd.notna(valor) or valor < 0 or valor >= 10_000_000_000:
                raise ValueError(f"O campo {campo.replace('_', ' ')} deve ser um valor entre R$ 0,00 e R$ 9.999.999.999,99.")
            dados[campo] = round(valor, 2)


def inserir_registro(tabela, dados):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")
    permitidas = TABELAS_PERMITIDAS[tabela]["colunas"]
    if not dados or any(c not in permitidas for c in dados):
        raise ValueError("Foram enviados campos inválidos.")
    dados = dict(dados)
    _validar_valores(tabela, dados)
    colunas = list(dados)
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(sql.Identifier(tabela), sql.SQL(", ").join(map(sql.Identifier, colunas)), sql.SQL(", ").join(sql.Placeholder() for _ in colunas)), tuple(dados[c] for c in colunas))


def atualizar_registro(tabela, id_valor, dados):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")
    config = TABELAS_PERMITIDAS[tabela]
    if not dados or config["id"] in dados or any(c not in config["colunas"] for c in dados):
        raise ValueError("O ID principal não pode ser alterado.")
    dados = dict(dados)
    _validar_valores(tabela, dados)
    atribuicoes = sql.SQL(", ").join(sql.SQL("{} = {}").format(sql.Identifier(c), sql.Placeholder()) for c in dados)
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql.SQL("UPDATE {} SET {} WHERE {} = {}").format(sql.Identifier(tabela), atribuicoes, sql.Identifier(config["id"]), sql.Placeholder()), (*dados.values(), id_valor))
            return cursor.rowcount


def excluir_registro(tabela, id_valor):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Tabela não permitida.")
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql.SQL("DELETE FROM {} WHERE {} = {}").format(sql.Identifier(tabela), sql.Identifier(TABELAS_PERMITIDAS[tabela]["id"]), sql.Placeholder()), (id_valor,))
            return cursor.rowcount


def importar_dataframe_para_supabase(dataframe, tabela):
    if tabela not in TABELAS_PERMITIDAS:
        raise ValueError("Selecione uma tabela válida.")
    config = TABELAS_PERMITIDAS[tabela]
    id_coluna = config["id"]
    colunas = config["colunas"]
    df = dataframe.copy()
    df.columns = [str(c).strip() for c in df.columns]
    faltantes = [c for c in colunas if c != id_coluna and c not in df.columns]
    extras = [c for c in df.columns if c not in colunas]
    if faltantes or extras:
        raise ValueError(f"Colunas ausentes: {faltantes or 'nenhuma'}. Colunas não reconhecidas: {extras or 'nenhuma'}. Esperadas: {colunas} (o ID principal pode ser omitido).")
    if df.empty:
        return 0
    if id_coluna not in df.columns:
        df[id_coluna] = pd.NA
    if tabela in ("compras", "pedidos"):
        df[id_coluna] = pd.to_numeric(df[id_coluna], errors="coerce")
        usados = {int(x) for x in df[id_coluna].dropna()}
        prox = proximo_id(tabela)
        novos = []
        for val in df[id_coluna].tolist():
            if pd.isna(val):
                while prox in usados or prox in novos:
                    prox += 1
                novos.append(prox); prox += 1
            else:
                novos.append(int(val))
        df[id_coluna] = novos
    else:
        df[id_coluna] = df[id_coluna].where(df[id_coluna].notna(), None)
        prox = proximo_produto_id()
        def gerar_produto():
            nonlocal prox
            valor = prox
            numero = int(valor[1:]) + 1
            prox = f"P{numero:03d}"
            return valor
        df[id_coluna] = [str(v).strip() if pd.notna(v) and str(v).strip() else gerar_produto() for v in df[id_coluna]]
    for coluna in COLUNAS_INTEIRAS[tabela]:
        if coluna in df:
            valores = pd.to_numeric(df[coluna], errors="raise")
            if valores.isna().any():
                raise ValueError(f"Preencha todos os valores da coluna {coluna}.")
            df[coluna] = valores.astype(int)
    for coluna in (["valor_total"] if tabela == "compras" else ["preco_unitario"]):
        if coluna in df:
            serie = df[coluna].astype(str).str.replace("R$", "", regex=False).str.replace(" ", "", regex=False)
            # Aceita tanto 1234.56 quanto 1.234,56.
            serie = serie.map(lambda x: x.replace(".", "").replace(",", ".") if "," in x else x)
            df[coluna] = pd.to_numeric(serie, errors="raise")
            if df[coluna].isna().any() or (df[coluna] < 0).any() or (df[coluna] >= 10_000_000_000).any():
                raise ValueError(f"A coluna {coluna} deve conter valores monetários válidos até R$ 9.999.999.999,99.")
    if tabela == "compras":
        df["data_compra"] = pd.to_datetime(df["data_compra"], errors="coerce").dt.date
        if df["data_compra"].isna().any() or df["metodo_pagamento"].isna().any():
            raise ValueError("Confira as datas e os métodos de pagamento: não podem ficar vazios.")
    elif tabela == "pedidos":
        if df["produto_id"].isna().any() or df["quantidade"].le(0).any():
            raise ValueError("Cada pedido precisa ter produto e quantidade maior que zero.")
    else:
        if df["nome_produto"].isna().any() or df["nome_produto"].astype(str).str.strip().eq("").any():
            raise ValueError("Informe o nome de todos os produtos.")
        df["categoria"] = df["categoria"].fillna("Geral")
    df = df.drop_duplicates(subset=[id_coluna], keep="first")
    df = df.astype(object).where(pd.notna(df), None)
    registros = df[colunas].to_dict(orient="records")
    total = 0
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            for reg in registros:
                cursor.execute(sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO NOTHING").format(sql.Identifier(tabela), sql.SQL(", ").join(map(sql.Identifier, colunas)), sql.SQL(", ").join(sql.Placeholder() for _ in colunas), sql.Identifier(id_coluna)), tuple(reg[c] for c in colunas))
                total += cursor.rowcount
    return total


def importar_csv_para_supabase(caminho_csv, tabela):
    return importar_dataframe_para_supabase(pd.read_csv(caminho_csv), tabela)
