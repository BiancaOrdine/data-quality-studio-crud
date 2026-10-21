import streamlit as st
import psycopg


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
