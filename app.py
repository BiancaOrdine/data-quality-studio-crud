from pathlib import Path
import re

import pandas as pd
import streamlit as st
import plotly.express as px

from db import (
    listar_registros,
    inserir_registro,
    atualizar_registro,
    excluir_registro,
    inicializar_tabela_produtos,
    importar_dataframe_para_supabase,
)


PASTA_PROJETO = Path(__file__).parent
PASTA_DADOS = PASTA_PROJETO / "dados_processados"

ROSA = "#774EBF"
ROSA_CLARO = "#E1C3FF"
AMEIXA = "#774EBF"
FUNDO = "#FCF7EE"
BRANCO = "#FFFFFF"
TEXTO = "#302743"
TEXTO_SECUNDARIO = "#665A77"
LINHA = "#E1D7EB"


st.set_page_config(
    page_title="Kraken Hub | Atlética T.I.",
    page_icon="🦑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

    
# Estilos

st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        --dq-purple: #774EBF;
        --dq-lilac: #E1C3FF;
        --dq-cream: #FCF7EE;
        --dq-yellow: #F9CC74;
        --dq-white: #FFFFFF;
        --dq-text: #302743;
        --dq-muted: #665A77;
        --dq-line: #E1D7EB;
    }

    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"], .stApp {
        background: var(--dq-cream) !important;
        color: var(--dq-text) !important;
        scroll-behavior: smooth;
    }

    [data-testid="stHeader"] {
        background: var(--dq-cream) !important;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1500px;
        padding: 6.8rem 2.5rem 1.5rem;
        scroll-behavior: smooth;
        scroll-padding-top: 7rem;
    }

    h1, h2, h3, h4 {
        color: var(--dq-text) !important;
        letter-spacing: -0.035em !important;
    }
    h1 { font-size: clamp(2.1rem, 4vw, 3.2rem) !important; font-weight: 750 !important; line-height: 1.12 !important; }
    h2 { font-size: 1.35rem !important; font-weight: 650 !important; }
    h3 { font-size: 1.02rem !important; font-weight: 650 !important; }
    p, label { color: var(--dq-muted); }

    .kraken-nav {
        position: fixed;
        top: 0.65rem;
        left: max(1rem, calc((100vw - 1500px) / 2 + 2.5rem));
        right: max(1rem, calc((100vw - 1500px) / 2 + 2.5rem));
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: nowrap;
        box-sizing: border-box;
        padding: 0.8rem 1rem;
        margin: 0;
        background: rgba(252, 247, 238, 0.98);
        border: 1px solid var(--dq-line);
        border-radius: 16px;
        box-shadow: 0 6px 22px rgba(67, 42, 105, 0.10);
        backdrop-filter: blur(12px);
    }
    .kraken-nav-brand { color: var(--dq-purple) !important; font-weight: 800; letter-spacing: -0.03em; white-space: nowrap; flex: 0 0 auto; }
    .kraken-nav-links { display: flex; align-items: center; justify-content: flex-end; gap: 0.25rem; flex-wrap: nowrap; min-width: 0; }
    .kraken-nav a { color: var(--dq-text) !important; text-decoration: none !important; font-size: 0.82rem; font-weight: 650; padding: 0.48rem 0.65rem; border-radius: 9px; white-space: nowrap; }
    .kraken-nav a:hover, .kraken-nav a:focus-visible { background: var(--dq-lilac); color: var(--dq-purple) !important; }
    [id] { scroll-margin-top: 7rem; }

    .kraken-cover {
        position: relative;
        overflow: hidden;
        padding: clamp(1.8rem, 5vw, 4.2rem);
        margin: 0.2rem 0 2rem;
        border-radius: 24px;
        background: linear-gradient(125deg, #774EBF 0%, #6940AC 68%, #55338F 100%);
        color: #FFFFFF;
        box-shadow: 0 18px 45px rgba(91, 56, 150, 0.18);
    }
    .kraken-cover:after {
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        right: -70px;
        top: -95px;
        border: 42px solid rgba(225, 195, 255, 0.18);
        border-radius: 50%;
        pointer-events: none;
    }
    .kraken-cover-kicker { color: #F9CC74; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 0.9rem; }
    .kraken-cover h1 { color: #FFFFFF !important; font-size: clamp(2.5rem, 6vw, 4.7rem) !important; margin: 0; }
    .kraken-cover p { position: relative; z-index: 1; max-width: 660px; margin: 1rem 0 0; color: rgba(255,255,255,0.88) !important; font-size: 1.02rem; line-height: 1.75; }
    .kraken-cover-tag { display: inline-block; margin-top: 1.3rem; padding: 0.45rem 0.75rem; border: 1px solid rgba(255,255,255,0.3); border-radius: 999px; color: #FFFFFF; font-size: 0.78rem; }

    .dq-eyebrow { font-size: 0.7rem; font-weight: 750; letter-spacing: 0.15em; color: var(--dq-purple); margin-bottom: 0.65rem; }
    .dq-intro { font-size: 0.98rem; line-height: 1.7; color: var(--dq-muted) !important; max-width: 650px; margin-top: 0.8rem; }
    .dq-rule { border: none; border-top: 1px solid var(--dq-line); margin: 1.65rem 0; }
    .dq-kpi { height: 100%; min-height: 112px; padding: 1.1rem 1.15rem; border: 1px solid var(--dq-line); border-radius: 14px; background: var(--dq-white); }
    .dq-kpi-label { font-size: 0.8rem; color: var(--dq-muted) !important; margin-bottom: 0.65rem; }
    .dq-kpi-value { font-size: clamp(1.3rem, 2vw, 1.9rem); font-weight: 750; letter-spacing: -0.045em; color: var(--dq-text) !important; overflow-wrap: anywhere; line-height: 1.2; }
    .dq-kpi-accent { width: 27px; height: 4px; background: var(--dq-yellow); border-radius: 5px; margin-top: 0.9rem; }
    .dq-status { padding: 0.85rem 1rem; border: 1px solid #E1C3FF; border-radius: 10px; background: #F3E8FF; color: #52338C; font-size: 0.88rem; line-height: 1.6; margin: 0.5rem 0 1rem; }
    .dq-footer { text-align: center; color: var(--dq-muted) !important; font-size: 0.8rem; line-height: 1.6; padding: 0.5rem 0 1rem; }
    .dq-footer strong { color: var(--dq-purple) !important; }

    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--dq-muted) !important; opacity: 1 !important; font-size: 0.8rem; }
    [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
    [data-testid="stSelectbox"] label, [data-testid="stNumberInput"] label { color: var(--dq-muted) !important; font-size: 0.82rem; }
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    [data-testid="stNumberInput"] input { background: #FFFFFF !important; border-color: var(--dq-line) !important; color: var(--dq-text) !important; border-radius: 9px !important; }
    [data-testid="stSelectbox"] div[data-baseweb="select"] *, [data-testid="stNumberInput"] input { color: var(--dq-text) !important; -webkit-text-fill-color: var(--dq-text) !important; }
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [role="option"] { background: #FFFFFF !important; color: var(--dq-text) !important; }
    [role="option"]:hover { background: #F3E8FF !important; }
    [data-testid="stDataFrame"] { background: #FFFFFF !important; border: 1px solid var(--dq-line) !important; border-radius: 10px !important; overflow: hidden; }
    [data-testid="stDataFrame"] iframe { background: #FFFFFF !important; }
    [data-testid="stPlotlyChart"] { width: 100% !important; min-width: 0 !important; background: transparent !important; }
    [data-testid="stHorizontalBlock"] { min-width: 0; gap: 1rem; }
    [data-testid="stAlert"] { border-radius: 10px !important; }
    .stButton button, [data-testid="stFormSubmitButton"] button { border-radius: 9px; border-color: var(--dq-purple); }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs div[role="tablist"] [data-baseweb="tab-highlight"] { background-color: #774EBF !important; height: 3px !important;}
    .stTabs [data-baseweb="tab-border"],
    .stTabs div[role="tablist"] {border-color: #774EBF !important;}
    .stTabs button[aria-selected="true"] {color: #774EBF !important; border-bottom-color: #774EBF !important;}
    .stTabs button[aria-selected="true"]::after {background-color: #774EBF !important; border-color: #774EBF !important;}
    .stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] { background: var(--dq-purple); color: #FFFFFF; }
    .stButton button:hover, [data-testid="stFormSubmitButton"] button:hover { border-color: var(--dq-purple); color: var(--dq-purple); }

    @media (max-width: 900px) {
        [data-testid="stMainBlockContainer"] {
            padding: 7.4rem 1rem 1.2rem !important;
            scroll-padding-top: 7.8rem;
        }
        .kraken-nav {
            top: 0.45rem;
            left: 0.55rem;
            right: 0.55rem;
            padding: 0.6rem 0.7rem;
            border-radius: 12px;
            gap: 0.35rem;
            flex-wrap: wrap;
        }
        .kraken-nav-brand { font-size: 0.78rem; }
        .kraken-nav-links {
            width: 100%;
            justify-content: flex-start;
            gap: 0.15rem;
            overflow-x: auto;
            overscroll-behavior-x: contain;
            scrollbar-width: none;
            padding-bottom: 1px;
        }
        .kraken-nav-links::-webkit-scrollbar { display: none; }
        .kraken-nav a { padding: 0.4rem 0.55rem; font-size: 0.75rem; }
        .kraken-cover { border-radius: 18px; }
        h1 { font-size: 2.15rem !important; }
        .dq-kpi { min-height: 95px; padding: 0.9rem; }
    }
    @media (max-width: 420px) {
        [data-testid="stMainBlockContainer"] { padding-top: 7.7rem !important; }
        .kraken-nav { padding: 0.55rem 0.6rem; }
        .kraken-nav-links { margin-right: -0.1rem; }
        .kraken-nav a { font-size: 0.72rem; padding: 0.38rem 0.48rem; }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Leitura dos dados

@st.cache_data
def carregar_validacao():
    return pd.read_csv(PASTA_DADOS / "validacao.csv")


# Compras e pedidos vêm diretamente do Supabase para refletir as alterações do CRUD.
try:
    # A inicialização cria a tabela e importa IDs legados; não precisa rodar
    # novamente a cada interação do usuário.
    if not st.session_state.get("_kraken_produtos_inicializados", False):
        inicializar_tabela_produtos()
        st.session_state["_kraken_produtos_inicializados"] = True

    # Uma leitura por tabela nesta execução. O CRUD reutiliza estes dados.
    compras = pd.DataFrame(listar_registros("compras"))
    pedidos = pd.DataFrame(listar_registros("pedidos"))
    produtos = pd.DataFrame(listar_registros("produtos"))
    if compras.empty and len(compras.columns) == 0:
        compras = pd.DataFrame(columns=[
            "id_compra", "cliente_id", "data_compra", "valor_total", "metodo_pagamento"
        ])
    if pedidos.empty and len(pedidos.columns) == 0:
        pedidos = pd.DataFrame(columns=[
            "id_pedido", "id_compra", "produto_id", "quantidade", "preco_unitario"
        ])
    if produtos.empty and len(produtos.columns) == 0:
        produtos = pd.DataFrame(columns=["produto_id", "nome_produto", "categoria", "preco_unitario"])
except Exception as erro:
    st.error("Não foi possível carregar os dados do banco de dados.")
    st.caption(f"Detalhes técnicos: {type(erro).__name__}")
    compras = pd.DataFrame(columns=[
        "id_compra", "cliente_id", "data_compra", "valor_total", "metodo_pagamento"
    ])
    pedidos = pd.DataFrame(columns=[
        "id_pedido", "id_compra", "produto_id", "quantidade", "preco_unitario"
    ])
    produtos = pd.DataFrame(columns=["produto_id", "nome_produto", "categoria", "preco_unitario"])

# A tabela de inconsistências é recalculada com os dados atuais do Supabase.
validacao = pd.DataFrame(columns=["id_compra", "valor_total", "valor_calculado", "diferenca", "situacao"])


# Mantém tipos consistentes mesmo quando as tabelas estão vazias.
for coluna in ["id_compra", "cliente_id"]:
    if coluna in compras.columns:
        compras[coluna] = pd.to_numeric(compras[coluna], errors="coerce").astype("Int64")
if "valor_total" in compras.columns:
    compras["valor_total"] = pd.to_numeric(compras["valor_total"], errors="coerce")
if "data_compra" in compras.columns:
    compras["data_compra"] = pd.to_datetime(compras["data_compra"], errors="coerce")

for coluna in ["id_pedido", "id_compra", "quantidade"]:
    if coluna in pedidos.columns:
        pedidos[coluna] = pd.to_numeric(pedidos[coluna], errors="coerce").astype("Int64")
if "preco_unitario" in pedidos.columns:
    pedidos["preco_unitario"] = pd.to_numeric(pedidos["preco_unitario"], errors="coerce")
if "produto_id" not in pedidos.columns:
    pedidos["produto_id"] = pd.Series(dtype="object")

validacao["valor_total"] = pd.to_numeric(validacao.get("valor_total"), errors="coerce")
validacao["valor_calculado"] = pd.to_numeric(validacao.get("valor_calculado"), errors="coerce")
validacao["situacao"] = validacao.get("situacao", pd.Series(dtype="object")).fillna(
    "SITUAÇÃO NÃO INFORMADA"
)


# Preparação dos dados

compras["data_compra"] = pd.to_datetime(
    compras["data_compra"],
    errors="coerce"
)

compras["valor_total"] = pd.to_numeric(
    compras["valor_total"],
    errors="coerce"
)

compras["cliente_id"] = pd.to_numeric(
    compras["cliente_id"],
    errors="coerce"
).astype("Int64")

pedidos["quantidade"] = pd.to_numeric(
    pedidos["quantidade"],
    errors="coerce"
)

validacao["valor_total"] = pd.to_numeric(
    validacao["valor_total"],
    errors="coerce"
)

validacao["valor_calculado"] = pd.to_numeric(
    validacao["valor_calculado"],
    errors="coerce"
)

validacao["situacao"] = validacao["situacao"].fillna(
    "SITUAÇÃO NÃO INFORMADA"
)

# Reconciliação em tempo real: compara o total da compra com a soma dos itens dos pedidos.
if not compras.empty:
    if pedidos.empty:
        totais_pedidos = pd.DataFrame(columns=["id_compra", "valor_calculado"])
    else:
        pedidos_calc = pedidos.copy()
        pedidos_calc["quantidade"] = pd.to_numeric(pedidos_calc["quantidade"], errors="coerce").fillna(0)
        pedidos_calc["preco_unitario"] = pd.to_numeric(pedidos_calc["preco_unitario"], errors="coerce").fillna(0)
        pedidos_calc["subtotal"] = pedidos_calc["quantidade"] * pedidos_calc["preco_unitario"]
        totais_pedidos = pedidos_calc.groupby("id_compra", as_index=False)["subtotal"].sum().rename(columns={"subtotal": "valor_calculado"})
    validacao = compras[["id_compra", "valor_total"]].merge(totais_pedidos, on="id_compra", how="left")
    validacao["valor_calculado"] = validacao["valor_calculado"].fillna(0.0)
    validacao["diferenca"] = (validacao["valor_total"] - validacao["valor_calculado"]).round(2)
    validacao["situacao"] = validacao.apply(
        lambda r: "OK" if abs(float(r["diferenca"] or 0)) < 0.01 else ("Compra sem pedidos" if float(r["valor_calculado"] or 0) == 0 else "Valor divergente"), axis=1
    )
else:
    validacao = pd.DataFrame(columns=["id_compra", "valor_total", "valor_calculado", "diferenca", "situacao"])



def formatar_moeda(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def exibir_tabela(df, colunas_monetarias=()):
    """Exibe datas sem horário e valores monetários no padrão brasileiro."""
    if df is None or df.empty:
        st.info("Nenhum registro cadastrado.")
        return

    formatters = {
        c: (lambda v: formatar_moeda(float(v)) if pd.notna(v) else "—")
        for c in colunas_monetarias if c in df.columns
    }

    # Mantém a coluna como data para cálculos e gráficos; altera apenas a exibição.
    if "data_compra" in df.columns:
        formatters["data_compra"] = lambda v: (
            pd.to_datetime(v, errors="coerce").strftime("%d/%m/%Y")
            if pd.notna(v) and pd.notna(pd.to_datetime(v, errors="coerce"))
            else "—"
        )

    st.dataframe(
        df.style.format(formatters, na_rep="—"),
        use_container_width=True,
        hide_index=True,
    )


# Navegação e capa

st.markdown(
    """
    <nav class="kraken-nav">
        <span class="kraken-nav-brand">◉ KRAKEN HUB</span>
        <div class="kraken-nav-links">
            <a href="#inicio">Início</a>
            <a href="#compras">Compras</a>
            <a href="#produtos">Produtos</a>
            <a href="#qualidade">Qualidade</a>
            <a href="#gerenciamento">Gerenciar dados</a>
        </div>
    </nav>
    <div class="kraken-cover" id="inicio">
        <div class="kraken-cover-kicker">Atlética T.I. · UMC</div>
        <h1>Kraken Hub</h1>
        <p>O espaço da Atlética T.I. para organizar compras, acompanhar produtos e manter os dados em ordem.</p>
        <span class="kraken-cover-tag">GESTÃO · ORGANIZAÇÃO · CONTROLE</span>
    </div>
    """,
    unsafe_allow_html=True
)


# Indicadores

total_compras = len(compras)
valor_registrado = compras["valor_total"].sum()
total_clientes = compras["cliente_id"].nunique()
total_problemas = int((validacao["situacao"] != "OK").sum())

col1, col2, col3, col4 = st.columns(4)

indicadores = [
    (col1, "Compras", f"{total_compras:,}"),
    (col2, "Valor das compras", formatar_moeda(valor_registrado)),
    (col3, "Clientes", f"{total_clientes:,}"),
    (col4, "Para revisar", f"{total_problemas:,}")
]

for coluna, rotulo, valor in indicadores:
    with coluna:
        st.markdown(
            f"""
            <div class="dq-kpi">
                <div class="dq-kpi-label">{rotulo}</div>
                <div class="dq-kpi-value">{valor}</div>
                <div class="dq-kpi-accent"></div>
            </div>
            """,
            unsafe_allow_html=True
        )



# Filtros

st.markdown(' <div id="compras"></div> '.strip(), unsafe_allow_html=True)
st.markdown('<hr class="dq-rule">', unsafe_allow_html=True)

st.subheader("Compras")
st.caption("Consulte os registros.")

col_cliente, col_metodo, col_valor = st.columns(
    [1, 1.3, 1],
    gap="medium"
)

with col_cliente:
    clientes = sorted(
        compras["cliente_id"].dropna().unique().tolist()
    )

    cliente_selecionado = st.selectbox(
        "Cliente",
        options=["Todos"] + clientes,
        format_func=lambda x: (
            "Todos os clientes" if x == "Todos" else str(x)
        )
    )

with col_metodo:
    metodos = sorted(
        compras["metodo_pagamento"].dropna().unique().tolist()
    )

    metodo_selecionado = st.selectbox(
        "Pagamento",
        options=["Todos"] + metodos,
        format_func=lambda x: (
            "Todos os métodos" if x == "Todos" else str(x)
        )
    )

with col_valor:
    maior_valor = (
        float(compras["valor_total"].max())
        if not compras.empty and compras["valor_total"].notna().any()
        else 0.0
    )

    valor_minimo = st.number_input(
        "Valor mínimo (R$)",
        min_value=0.0,
        max_value=max(maior_valor, 0.0),
        value=0.0,
        step=50.0
    )

compras_filtradas = compras.copy()

if cliente_selecionado != "Todos":
    compras_filtradas = compras_filtradas[
        compras_filtradas["cliente_id"] == cliente_selecionado
    ]

if metodo_selecionado != "Todos":
    compras_filtradas = compras_filtradas[
        compras_filtradas["metodo_pagamento"] == metodo_selecionado
    ]

compras_filtradas = compras_filtradas[
    compras_filtradas["valor_total"] >= valor_minimo
]

st.caption(
    f"{len(compras_filtradas)} de {len(compras)} compras exibidas."
)


# Gráficos

st.markdown('<hr class="dq-rule">', unsafe_allow_html=True)

grafico1, grafico2 = st.columns(2, gap="large")

with grafico1:
    resumo_pagamentos = (
        compras_filtradas
        .groupby("metodo_pagamento")
        .size()
        .reset_index(name="quantidade")
        .sort_values("quantidade", ascending=True)
    )

    if resumo_pagamentos.empty:
        st.info("Nenhuma compra encontrada.")
    else:
        fig_pagamentos = px.bar(
            resumo_pagamentos,
            x="quantidade",
            y="metodo_pagamento",
            orientation="h",
            text="quantidade",
            color_discrete_sequence=[ROSA],
            title="Compras por pagamento",
            labels={
                "quantidade": "Compras",
                "metodo_pagamento": "Pagamento"
            }
        )

        fig_pagamentos.update_traces(
            textposition="outside",
            cliponaxis=False,
            marker_line_width=0
        )

        fig_pagamentos.update_layout(
            autosize=True,
            height=max(300, 100 + 55 * len(resumo_pagamentos)),
            showlegend=False,
            margin=dict(l=10, r=35, t=65, b=35),
            yaxis_title=None,
            xaxis_title=None,
            bargap=0.45,
            font=dict(
                family="Arial, sans-serif",
                color=TEXTO,
                size=12
            ),
            title_font=dict(size=16, color=TEXTO),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=True,
                gridcolor=LINHA,
                zeroline=False,
                automargin=True
            ),
            yaxis=dict(
                showgrid=False,
                automargin=True
            )
        )

        st.plotly_chart(
            fig_pagamentos,
            use_container_width=True,
            theme=None,
            config={"responsive": True, "displayModeBar": False}
        )

with grafico2:
    resumo_datas = (
        compras_filtradas
        .dropna(subset=["data_compra"])
        .groupby("data_compra", as_index=False)["valor_total"]
        .sum()
        .sort_values("data_compra")
    )

    if resumo_datas.empty:
        st.info("Nenhuma data disponível.")
    else:
        fig_valores = px.line(
            resumo_datas,
            x="data_compra",
            y="valor_total",
            markers=True,
            title="Valores por data",
            labels={
                "data_compra": "Data",
                "valor_total": "Valor registrado"
            }
        )

        fig_valores.update_traces(
            line=dict(color=ROSA, width=2.5),
            marker=dict(size=7, color=ROSA),
            fill="tozeroy",
            fillcolor="rgba(119,78,191,0.12)"
        )

        fig_valores.update_layout(
            autosize=True,
            height=355,
            margin=dict(l=15, r=20, t=65, b=35),
            xaxis_title=None,
            yaxis_title=None,
            font=dict(
                family="Arial, sans-serif",
                color=TEXTO,
                size=12
            ),
            title_font=dict(size=16, color=TEXTO),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                automargin=True
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=LINHA,
                zeroline=False,
                automargin=True
            ),
            hovermode="x unified"
        )

        st.plotly_chart(
            fig_valores,
            use_container_width=True,
            theme=None,
            config={"responsive": True, "displayModeBar": False}
        )


# Produtos

st.markdown(' <div id="produtos"></div> '.strip(), unsafe_allow_html=True)
st.markdown('<hr class="dq-rule">', unsafe_allow_html=True)

st.subheader("Produtos")

resumo_produtos = (
    pedidos
    .groupby("produto_id", as_index=False)["quantidade"]
    .sum()
    .sort_values("quantidade", ascending=True)
)

if resumo_produtos.empty:
    st.info("Nenhum produto encontrado.")
else:
    fig_produtos = px.bar(
        resumo_produtos,
        x="quantidade",
        y="produto_id",
        orientation="h",
        text="quantidade",
        color_discrete_sequence=[AMEIXA],
        labels={
            "produto_id": "Produto",
            "quantidade": "Unidades"
        }
    )

    fig_produtos.update_traces(
        textposition="outside",
        cliponaxis=False,
        marker_line_width=0
    )

    fig_produtos.update_layout(
        autosize=True,
        height=max(300, 100 + 55 * len(resumo_produtos)),
        showlegend=False,
        margin=dict(l=10, r=35, t=20, b=35),
        xaxis_title=None,
        yaxis_title=None,
        bargap=0.4,
        font=dict(
            family="Arial, sans-serif",
            color=TEXTO,
            size=12
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True,
            gridcolor=LINHA,
            zeroline=False,
            automargin=True
        ),
        yaxis=dict(
            showgrid=False,
            automargin=True
        )
    )

    st.plotly_chart(
        fig_produtos,
        use_container_width=True,
        theme=None,
        config={"responsive": True, "displayModeBar": False}
    )

# Validação

st.markdown(' <div id="qualidade"></div> '.strip(), unsafe_allow_html=True)
st.markdown('<hr class="dq-rule">', unsafe_allow_html=True)

st.subheader("Qualidade dos dados")

problemas = validacao[
    validacao["situacao"] != "OK"
].copy()

if problemas.empty:
    st.success("Nenhuma inconsistência identificada.")
else:
    st.markdown(
        f"""
        <div class="dq-status">
            <strong>{len(problemas)} registro(s)</strong>
            precisam ser conferidos.
        </div>
        """,
        unsafe_allow_html=True
    )

    exibir_tabela(problemas, ["valor_total", "valor_calculado", "diferenca"])

# GERENCIAMENTO DE DADOS - CRUD
st.markdown(' <div id="gerenciamento"></div> '.strip(), unsafe_allow_html=True)
st.divider()
st.header("Gerenciamento de dados")
st.write("Consulte e gerencie os registros armazenados no Supabase.")

# Importação opcional de um CSV escolhido pelo usuário.
with st.expander("Importar dados de um arquivo CSV"):
    st.caption(
        "Envie um CSV para adicionar registros diretamente ao Supabase. "
        "O arquivo precisa ter as colunas da tabela escolhida. "
        "Se o ID principal não estiver preenchido, ele será gerado automaticamente."
    )

    with st.form("form_importar_csv"):
        tabela_csv = st.selectbox(
            "Tabela de destino",
            options=["compras", "pedidos", "produtos"],
            format_func=lambda x: {"compras": "Compras", "pedidos": "Pedidos", "produtos": "Produtos"}[x],
            key="tabela_destino_csv",
        )
        arquivo_csv = st.file_uploader(
            "Selecione um arquivo CSV",
            type=["csv"],
            key="arquivo_csv_supabase",
        )
        importar_arquivo = st.form_submit_button("Importar CSV")

        if importar_arquivo:
            if arquivo_csv is None:
                st.warning("Selecione um arquivo CSV antes de importar.")
            else:
                try:
                    df_csv = pd.read_csv(arquivo_csv)
                    quantidade = importar_dataframe_para_supabase(df_csv, tabela_csv)
                    st.success(
                        f"Importação concluída. Registros adicionados: {quantidade}."
                    )
                    st.rerun()
                except Exception as erro:
                    st.error("Não foi possível importar o CSV. Confira os nomes das colunas, os valores numéricos e se os registros relacionados já existem.")
                    if isinstance(erro, ValueError):
                        st.caption(str(erro))
                    else:
                        st.caption(f"Detalhes técnicos: {type(erro).__name__}")

aba_compras, aba_pedidos, aba_produtos = st.tabs(["Compras", "Pedidos", "Produtos"])

METODOS_PAGAMENTO = ["Cartão de Crédito", "Cartão de Débito", "Boleto", "Pix"]

with aba_compras:
    st.subheader("Compras")

    try:
        dados_compras = compras.to_dict(orient="records")
        proximo_id_compra = max(
            (int(r["id_compra"]) for r in dados_compras), default=0
        ) + 1
        proximo_id_cliente = max(
            (int(r["cliente_id"]) for r in dados_compras if r.get("cliente_id") is not None),
            default=0,
        ) + 1
        clientes_existentes = sorted({
            int(r["cliente_id"])
            for r in dados_compras
            if r.get("cliente_id") is not None
        })

        # CADASTRAR COMPRA
        with st.expander("Cadastrar nova compra"):
            st.text_input("ID da compra (automático)", value=str(proximo_id_compra), disabled=True, key="id_compra_nova_visual")
            st.caption("O ID é gerado pelo sistema e não pode ser editado.")
            cliente_opcoes = ["Novo cliente (gerar ID)"] + clientes_existentes

            with st.form("form_cadastrar_compra_v2"):
                cliente_escolhido = st.selectbox(
                    "Cliente",
                    options=cliente_opcoes,
                    format_func=lambda x: x if isinstance(x, str) else f"Cliente {x}",
                    key="novo_cliente_escolhido_v2",
                )
                data_compra_nova = st.date_input(
                    "Data da compra",
                    key="nova_data_compra_v2",
                )
                valor_total_novo = st.number_input(
                    "Valor total (R$)",
                    min_value=0.01,
                    max_value=9_999_999_999.99,
                    value=10.0,
                    step=1.0,
                    format="%.2f",
                    key="novo_valor_total_v2",
                )
                metodo_novo = st.selectbox(
                    "Método de pagamento",
                    options=METODOS_PAGAMENTO,
                    key="novo_metodo_pagamento_v2",
                )
                cadastrar_compra = st.form_submit_button("Cadastrar compra")

                if cadastrar_compra:
                    try:
                        cliente_novo_id = (
                            proximo_id_cliente
                            if cliente_escolhido == "Novo cliente (gerar ID)"
                            else int(cliente_escolhido)
                        )
                        inserir_registro(
                            "compras",
                            {
                                "id_compra": proximo_id_compra,
                                "cliente_id": cliente_novo_id,
                                "data_compra": data_compra_nova,
                                "valor_total": float(valor_total_novo),
                                "metodo_pagamento": metodo_novo,
                            },
                        )
                        st.success(
                            f"Compra cadastrada! ID da compra: {proximo_id_compra}. "
                            f"ID do cliente: {cliente_novo_id}."
                        )
                        st.rerun()
                    except Exception as erro:
                        mensagem = str(erro).lower()
                        if "numeric field overflow" in mensagem or "numeric_value_out_of_range" in mensagem:
                            st.warning("Valor muito alto. Informe um valor menor que R$ 10.000.000.000,00, com até duas casas decimais.")
                        elif "check constraint" in mensagem or "metodo_pagamento" in mensagem:
                            st.warning("Esse método de pagamento não é aceito pela configuração atual do banco. Confira as opções permitidas no Supabase.")
                        else:
                            st.error("Não foi possível cadastrar a compra. Confira os campos e tente novamente.")

        # EDITAR COMPRA
        with st.expander("Editar compra existente"):
            if dados_compras:
                ids_compras = [int(r["id_compra"]) for r in dados_compras]
                id_editar = st.selectbox(
                    "Selecione a compra",
                    options=ids_compras,
                    format_func=lambda x: f"Compra {x}",
                    key="selecionar_compra_editar_" + "_".join(map(str, ids_compras)),
                )
                registro = next(r for r in dados_compras if int(r["id_compra"]) == id_editar)
                data_original = registro.get("data_compra")
                data_atual = (
                    pd.to_datetime(data_original).date()
                    if data_original is not None and pd.notna(data_original)
                    else pd.Timestamp.today().date()
                )
                metodo_original = registro.get("metodo_pagamento") or "Cartão de Crédito"
                # Normaliza o rótulo antigo "Cartão" para a opção válida de crédito.
                metodo_atual = "Cartão de Crédito" if metodo_original == "Cartão" else metodo_original
                if metodo_atual not in METODOS_PAGAMENTO:
                    metodo_atual = "Cartão de Crédito"

                with st.form(f"form_editar_compra_v2_{id_editar}"):
                    st.text_input("ID da compra (fixo)", value=str(id_editar), disabled=True, key=f"id_compra_fixo_{id_editar}")
                    cliente_editado = st.number_input(
                        "ID do cliente",
                        min_value=1,
                        value=max(1, int(registro.get("cliente_id") or 1)),
                        key=f"cliente_editado_v2_{id_editar}",
                    )
                    data_editada = st.date_input(
                        "Data da compra",
                        value=data_atual,
                        key=f"data_editada_v2_{id_editar}",
                    )
                    valor_original = registro.get("valor_total")
                    valor_editado = st.number_input(
                        "Valor total (R$)",
                        min_value=0.01,
                        max_value=9_999_999_999.99,
                        value=min(9_999_999_999.99, max(0.01, float(valor_original or 0.01))),
                        step=1.0,
                        format="%.2f",
                        key=f"valor_editado_v2_{id_editar}",
                    )
                    metodo_editado = st.selectbox(
                        "Método de pagamento",
                        options=METODOS_PAGAMENTO,
                        index=METODOS_PAGAMENTO.index(metodo_atual),
                        key=f"metodo_editado_v2_{id_editar}",
                    )
                    salvar_edicao_compra = st.form_submit_button("Salvar alterações")

                    if salvar_edicao_compra:
                        try:
                            atualizar_registro(
                                "compras",
                                id_editar,
                                {
                                    "cliente_id": int(cliente_editado),
                                    "data_compra": data_editada,
                                    "valor_total": float(valor_editado),
                                    "metodo_pagamento": metodo_editado,
                                },
                            )
                            st.success("Compra atualizada com sucesso!")
                            st.rerun()
                        except Exception as erro:
                            mensagem = str(erro).lower()
                            if "numeric field overflow" in mensagem or "numeric_value_out_of_range" in mensagem:
                                st.warning("Valor muito alto. Informe um valor menor que R$ 10.000.000.000,00, com até duas casas decimais.")
                            elif isinstance(erro, ValueError):
                                st.warning(str(erro))
                            else:
                                st.error("Não foi possível editar a compra. Confira os campos e tente novamente.")
            else:
                st.info("Não há compras para editar.")

        # EXCLUIR COMPRA
        with st.expander("Excluir compra"):
            if dados_compras:
                id_excluir_compra = st.selectbox(
                    "Selecione a compra para excluir",
                    options=[int(r["id_compra"]) for r in dados_compras],
                    format_func=lambda x: f"Compra {x}",
                    key="selecionar_compra_excluir_" + "_".join(str(int(r["id_compra"])) for r in dados_compras),
                )
                with st.form("form_excluir_compra"):
                    confirmar_exclusao_compra = st.checkbox(
                        "Confirmo que desejo excluir esta compra."
                    )
                    excluir_compra = st.form_submit_button("Excluir compra")
                    if excluir_compra:
                        if confirmar_exclusao_compra:
                            try:
                                excluidos = excluir_registro("compras", id_excluir_compra)
                                if excluidos:
                                    st.success("Compra excluída com sucesso!")
                                else:
                                    st.warning("A compra não foi encontrada.")
                                st.rerun()
                            except Exception as erro:
                                st.error(
                                    "Não foi possível excluir a compra. "
                                    "Verifique se existem pedidos vinculados a ela."
                                )
                                st.code(str(erro))
                        else:
                            st.warning("Marque a confirmação antes de excluir.")
            else:
                st.info("Não há compras para excluir.")

        # CONSULTAR COMPRAS
        st.divider()
        st.subheader("Tabela de compras")
        dados_compras = compras.to_dict(orient="records")
        if dados_compras:
            exibir_tabela(pd.DataFrame(dados_compras), ["valor_total"])
        else:
            st.info("Nenhuma compra cadastrada.")
        st.caption(f"Total de registros: {len(dados_compras)}")

    except Exception as erro:
        st.error("Não foi possível carregar o gerenciamento de compras.")
        st.code(str(erro))

with aba_pedidos:
    st.subheader("Pedidos")

    try:
        dados_pedidos = pedidos.to_dict(orient="records")
        proximo_id_pedido = max(
            (int(r["id_pedido"]) for r in dados_pedidos), default=0
        ) + 1
        compras_disponiveis = compras.to_dict(orient="records")
        ids_compras_disponiveis = sorted({
            int(r["id_compra"]) for r in compras_disponiveis
        })

        # CADASTRAR PEDIDO
        with st.expander("Cadastrar novo pedido"):
            st.text_input("ID do pedido (automático)", value=str(proximo_id_pedido), disabled=True, key="id_pedido_novo_visual")
            st.caption("O ID é gerado pelo sistema e não pode ser editado.")
            if ids_compras_disponiveis:
                with st.form("form_cadastrar_pedido_v2"):
                    compra_do_pedido = st.selectbox(
                        "Compra vinculada",
                        options=ids_compras_disponiveis,
                        format_func=lambda x: f"Compra {x}",
                        key="nova_compra_pedido_v2",
                    )
                    produtos_disponiveis = produtos.to_dict(orient="records")
                    ids_produtos = [str(r["produto_id"]) for r in produtos_disponiveis]
                    if ids_produtos:
                        produto_novo = st.selectbox(
                            "Produto", options=ids_produtos,
                            format_func=lambda x: next((f"{r['nome_produto']} ({r['produto_id']})" for r in produtos_disponiveis if str(r['produto_id']) == str(x)), str(x)),
                            key="novo_produto_id_v2",
                        )
                    else:
                        produto_novo = ""
                        st.info("Cadastre um produto na aba Produtos antes de criar um pedido.")
                    quantidade_nova = st.number_input(
                        "Quantidade",
                        min_value=1,
                        value=1,
                        step=1,
                        key="nova_quantidade_pedido_v2",
                    )
                    preco_novo = st.number_input(
                        "Preço unitário (R$)",
                        min_value=0.01,
                        max_value=9_999_999_999.99,
                        value=1.0,
                        step=1.0,
                        format="%.2f",
                        key="novo_preco_unitario_v2",
                    )
                    cadastrar_pedido = st.form_submit_button("Cadastrar pedido")
                    if cadastrar_pedido:
                        try:
                            if not produto_novo.strip():
                                st.warning("Informe o ID do produto.")
                            else:
                                inserir_registro(
                                    "pedidos",
                                    {
                                        "id_pedido": proximo_id_pedido,
                                        "id_compra": int(compra_do_pedido),
                                        "produto_id": produto_novo.strip(),
                                        "quantidade": int(quantidade_nova),
                                        "preco_unitario": float(preco_novo),
                                    },
                                )
                                st.success("Pedido cadastrado com sucesso!")
                                st.rerun()
                        except Exception as erro:
                            mensagem = str(erro).lower()
                            if "numeric field overflow" in mensagem or "numeric_value_out_of_range" in mensagem:
                                st.warning("Preço muito alto. Informe um valor menor que R$ 10.000.000.000,00, com até duas casas decimais.")
                            else:
                                st.error("Não foi possível cadastrar o pedido. Confira os campos e tente novamente.")
            else:
                st.info("Cadastre uma compra antes de adicionar um pedido.")

        # EDITAR PEDIDO
        with st.expander("Editar pedido existente"):
            if dados_pedidos:
                ids_pedidos = [int(r["id_pedido"]) for r in dados_pedidos]
                id_pedido_editar = st.selectbox(
                    "Selecione o pedido",
                    options=ids_pedidos,
                    format_func=lambda x: f"Pedido {x}",
                    key="selecionar_pedido_editar_" + "_".join(map(str, ids_pedidos)),
                )
                pedido = next(r for r in dados_pedidos if int(r["id_pedido"]) == id_pedido_editar)
                compra_atual = int(pedido["id_compra"])
                opcoes_compra_editar = list(ids_compras_disponiveis)
                if compra_atual not in opcoes_compra_editar:
                    opcoes_compra_editar.append(compra_atual)
                opcoes_compra_editar = sorted(opcoes_compra_editar)

                with st.form(f"form_editar_pedido_v2_{id_pedido_editar}"):
                    st.text_input("ID do pedido (fixo)", value=str(id_pedido_editar), disabled=True, key=f"id_pedido_fixo_{id_pedido_editar}")
                    compra_editada = st.selectbox(
                        "Compra vinculada",
                        options=opcoes_compra_editar,
                        index=opcoes_compra_editar.index(compra_atual),
                        format_func=lambda x: f"Compra {x}",
                        key=f"compra_editada_v2_{id_pedido_editar}",
                    )
                    produtos_edicao = produtos.to_dict(orient="records")
                    ids_produtos_edicao = [str(r["produto_id"]) for r in produtos_edicao]
                    produto_atual = str(pedido.get("produto_id") or "")
                    if produto_atual and produto_atual not in ids_produtos_edicao:
                        ids_produtos_edicao.append(produto_atual)
                    produto_editado = st.selectbox(
                        "Produto", options=ids_produtos_edicao,
                        index=ids_produtos_edicao.index(produto_atual) if produto_atual in ids_produtos_edicao else 0,
                        format_func=lambda x: next((f"{r['nome_produto']} ({r['produto_id']})" for r in produtos_edicao if str(r['produto_id']) == str(x)), str(x)),
                        key=f"produto_editado_v2_{id_pedido_editar}",
                    ) if ids_produtos_edicao else ""
                    quantidade_editada = st.number_input(
                        "Quantidade",
                        min_value=1,
                        value=max(1, int(pedido.get("quantidade") or 1)),
                        step=1,
                        key=f"quantidade_editada_v2_{id_pedido_editar}",
                    )
                    preco_editado = st.number_input(
                        "Preço unitário (R$)",
                        min_value=0.01,
                        max_value=9_999_999_999.99,
                        value=min(9_999_999_999.99, max(0.01, float(pedido.get("preco_unitario") or 0.01))),
                        step=1.0,
                        format="%.2f",
                        key=f"preco_editado_v2_{id_pedido_editar}",
                    )
                    salvar_edicao_pedido = st.form_submit_button("Salvar alterações")
                    if salvar_edicao_pedido:
                        try:
                            if not produto_editado.strip():
                                st.warning("Informe o ID do produto.")
                            else:
                                atualizar_registro(
                                    "pedidos",
                                    id_pedido_editar,
                                    {
                                        "id_compra": int(compra_editada),
                                        "produto_id": produto_editado.strip(),
                                        "quantidade": int(quantidade_editada),
                                        "preco_unitario": float(preco_editado),
                                    },
                                )
                                st.success("Pedido atualizado com sucesso!")
                                st.rerun()
                        except Exception as erro:
                            mensagem = str(erro).lower()
                            if "numeric field overflow" in mensagem or "numeric_value_out_of_range" in mensagem:
                                st.warning("Preço muito alto. Informe um valor menor que R$ 10.000.000.000,00, com até duas casas decimais.")
                            elif isinstance(erro, ValueError):
                                st.warning(str(erro))
                            else:
                                st.error("Não foi possível editar o pedido. Confira os campos e tente novamente.")
            else:
                st.info("Não há pedidos para editar.")

        # EXCLUIR PEDIDO
        with st.expander("Excluir pedido"):
            if dados_pedidos:
                id_pedido_excluir = st.selectbox(
                    "Selecione o pedido para excluir",
                    options=[int(r["id_pedido"]) for r in dados_pedidos],
                    format_func=lambda x: f"Pedido {x}",
                    key="selecionar_pedido_excluir_" + "_".join(str(int(r["id_pedido"])) for r in dados_pedidos),
                )
                with st.form("form_excluir_pedido"):
                    confirmar_exclusao_pedido = st.checkbox(
                        "Confirmo que desejo excluir este pedido."
                    )
                    excluir_pedido = st.form_submit_button("Excluir pedido")
                    if excluir_pedido:
                        if confirmar_exclusao_pedido:
                            try:
                                excluidos = excluir_registro("pedidos", id_pedido_excluir)
                                if excluidos:
                                    st.success("Pedido excluído com sucesso!")
                                else:
                                    st.warning("O pedido não foi encontrado.")
                                st.rerun()
                            except Exception as erro:
                                st.error("Não foi possível excluir o pedido.")
                                st.code(str(erro))
                        else:
                            st.warning("Marque a confirmação antes de excluir.")
            else:
                st.info("Não há pedidos para excluir.")

        # CONSULTAR PEDIDOS
        st.divider()
        st.subheader("Tabela de pedidos")
        dados_pedidos = pedidos.to_dict(orient="records")
        if dados_pedidos:
            exibir_tabela(pd.DataFrame(dados_pedidos), ["preco_unitario"])
        else:
            st.info("Nenhum pedido cadastrado.")
        st.caption(f"Total de registros: {len(dados_pedidos)}")

    except Exception as erro:
        st.error("Não foi possível carregar o gerenciamento de pedidos.")
        st.code(str(erro))


with aba_produtos:
    st.subheader("Produtos")
    st.caption("Cadastre o catálogo de produtos usado pelos pedidos. Os IDs são gerados automaticamente.")
    try:
        dados_produtos = produtos.to_dict(orient="records")
        numeros_produtos = [
            int(match.group(1))
            for registro_produto in dados_produtos
            if (match := re.fullmatch(r"P(\d+)", str(registro_produto.get("produto_id", ""))))
        ]
        proximo_codigo_produto = f"P{max(numeros_produtos, default=0) + 1:03d}"
        with st.expander("Cadastrar produto", expanded=False):
            st.caption(f"Próximo ID sugerido: {proximo_codigo_produto} (gerado automaticamente)")
            with st.form("form_cadastrar_produto"):
                nome_produto_novo = st.text_input("Nome do produto", max_chars=120)
                categoria_nova = st.text_input("Categoria", value="Geral", max_chars=80)
                preco_produto_novo = st.number_input("Preço unitário (R$)", min_value=0.0, max_value=9_999_999_999.99, value=10.0, step=1.0, format="%.2f", key="preco_produto_novo")
                cadastrar_produto = st.form_submit_button("Cadastrar produto")
                if cadastrar_produto:
                    if not nome_produto_novo.strip():
                        st.warning("Informe o nome do produto.")
                    else:
                        try:
                            novo_id_produto = proximo_codigo_produto
                            inserir_registro("produtos", {"produto_id": novo_id_produto, "nome_produto": nome_produto_novo.strip(), "categoria": categoria_nova.strip() or "Geral", "preco_unitario": float(preco_produto_novo)})
                            st.success(f"Produto {novo_id_produto} cadastrado.")
                            st.rerun()
                        except Exception as erro:
                            st.error("Não foi possível cadastrar o produto. Confira os campos e tente novamente.")
        with st.expander("Editar produto", expanded=False):
            if dados_produtos:
                ids_produtos = [str(r["produto_id"]) for r in dados_produtos]
                produto_escolhido = st.selectbox("Selecione o produto", ids_produtos, format_func=lambda x: next((f"{r['nome_produto']} ({r['produto_id']})" for r in dados_produtos if str(r['produto_id']) == str(x)), str(x)), key="produto_editar_selecao")
                produto_registro = next(r for r in dados_produtos if str(r["produto_id"]) == str(produto_escolhido))
                with st.form(f"form_editar_produto_{produto_escolhido}"):
                    st.caption(f"ID do produto: {produto_escolhido} (fixo; não pode ser alterado)")
                    nome_produto_editado = st.text_input("Nome do produto", value=str(produto_registro.get("nome_produto") or ""), key=f"nome_produto_{produto_escolhido}")
                    categoria_produto_editada = st.text_input("Categoria", value=str(produto_registro.get("categoria") or "Geral"), key=f"categoria_produto_{produto_escolhido}")
                    preco_produto_editado = st.number_input("Preço unitário (R$)", min_value=0.0, max_value=9_999_999_999.99, value=min(9_999_999_999.99, max(0.0, float(produto_registro.get("preco_unitario") or 0))), step=1.0, format="%.2f", key=f"preco_produto_{produto_escolhido}")
                    salvar_produto = st.form_submit_button("Salvar alterações")
                    if salvar_produto:
                        if not nome_produto_editado.strip():
                            st.warning("Informe o nome do produto.")
                        else:
                            try:
                                atualizar_registro("produtos", produto_escolhido, {"nome_produto": nome_produto_editado.strip(), "categoria": categoria_produto_editada.strip() or "Geral", "preco_unitario": float(preco_produto_editado)})
                                st.success("Produto atualizado com sucesso.")
                                st.rerun()
                            except Exception as erro:
                                st.error("Não foi possível editar o produto.")
            else:
                st.info("Nenhum produto cadastrado.")
        with st.expander("Excluir produto", expanded=False):
            if dados_produtos:
                produto_excluir = st.selectbox("Selecione o produto para excluir", [str(r["produto_id"]) for r in dados_produtos], format_func=lambda x: next((f"{r['nome_produto']} ({r['produto_id']})" for r in dados_produtos if str(r['produto_id']) == str(x)), str(x)), key="produto_excluir_selecao")
                with st.form("form_excluir_produto"):
                    confirmar_produto = st.checkbox("Confirmo que desejo excluir este produto.")
                    excluir_produto_btn = st.form_submit_button("Excluir produto")
                    if excluir_produto_btn:
                        if confirmar_produto:
                            # Impede apagar produtos ainda usados no histórico de pedidos.
                            ids_usados = {str(r["produto_id"]) for r in pedidos.to_dict(orient="records")}
                            if produto_excluir in ids_usados:
                                st.warning("Este produto aparece em pedidos existentes e não pode ser excluído. Você pode editar nome, categoria ou preço.")
                            else:
                                excluir_registro("produtos", produto_excluir)
                                st.success("Produto excluído.")
                                st.rerun()
                        else:
                            st.warning("Marque a confirmação antes de excluir.")
            else:
                st.info("Nenhum produto cadastrado para excluir.")
        st.divider()
        st.subheader("Catálogo de produtos")
        dados_produtos = produtos.to_dict(orient="records")
        exibir_tabela(pd.DataFrame(dados_produtos), ["preco_unitario"])
        st.caption(f"Total de produtos: {len(dados_produtos)}")
    except Exception as erro:
        st.error("Não foi possível carregar o gerenciamento de produtos.")
        st.caption(f"Detalhes técnicos: {type(erro).__name__}")


# Rodapé

st.markdown('<hr class="dq-rule">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="dq-footer"><strong>Feito por Bianca Ordine — Atlética T.I.</strong></div>
    """,
    unsafe_allow_html=True
)
