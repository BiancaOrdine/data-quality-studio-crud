from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

from db import (
    testar_conexao,
    listar_registros,
    inserir_registro,
    atualizar_registro,
    excluir_registro,
    importar_csv_para_supabase,
)


PASTA_PROJETO = Path(__file__).parent
PASTA_DADOS = PASTA_PROJETO / "dados_processados"

ROSA = "#B85D7B"
ROSA_CLARO = "#E8C3CE"
AMEIXA = "#765064"
FUNDO = "#FBF8F5"
BRANCO = "#FFFFFF"
TEXTO = "#35313A"
TEXTO_SECUNDARIO = "#655965"
LINHA = "#E9E1E2"


st.set_page_config(
    page_title="Data Quality Studio",
    page_icon="◌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

try:
    if testar_conexao():
        st.success("Conexão com o Supabase estabelecida!")
    else:
        st.error("Não foi possível confirmar a conexão.")
except Exception as erro:
    st.error("Falha ao conectar ao banco de dados.")
    st.caption(f"Detalhes técnicos: {type(erro).__name__}")
    
# Estilos

st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        --dq-rose: #B85D7B;
        --dq-plum: #765064;
        --dq-pink: #E8C3CE;
        --dq-line: #E9E1E2;
        --dq-bg: #FBF8F5;
        --dq-text: #35313A;
        --dq-muted: #655965;
    }

    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"] {
        background: #FBF8F5 !important;
        color: #35313A !important;
    }

    .stApp {
        background: #FBF8F5 !important;
        color: #35313A !important;
    }

    [data-testid="stHeader"] {
        background: #FBF8F5 !important;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1500px;
        padding: 2.2rem 2.5rem 1.5rem;
    }

    h1, h2, h3, h4 {
        color: #35313A !important;
        letter-spacing: -0.035em !important;
    }

    h1 {
        font-size: clamp(2.1rem, 4vw, 3.2rem) !important;
        font-weight: 650 !important;
        line-height: 1.12 !important;
    }

    h2 {
        font-size: 1.35rem !important;
        font-weight: 600 !important;
    }

    h3 {
        font-size: 1.02rem !important;
        font-weight: 600 !important;
    }

    p, label {
        color: #655965;
    }

    .dq-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #35313A;
        font-size: 1.05rem;
        font-weight: 600;
        letter-spacing: -0.025em;
        padding: 0.25rem 0 1.8rem;
    }

    .dq-mark {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: #F0DCE2;
        color: #96506A;
        font-size: 1.4rem;
    }

    .dq-brand-accent {
        color: #B85D7B;
    }

    .dq-eyebrow {
        font-size: 0.7rem;
        font-weight: 650;
        letter-spacing: 0.15em;
        color: #765064;
        margin-bottom: 0.65rem;
    }

    .dq-intro {
        font-size: 0.98rem;
        line-height: 1.7;
        color: #655965 !important;
        max-width: 650px;
        margin-top: 0.8rem;
    }

    .dq-rule {
        border: none;
        border-top: 1px solid #E9E1E2;
        margin: 1.65rem 0;
    }

    .dq-kpi {
        height: 100%;
        min-height: 112px;
        padding: 1.1rem 1.15rem;
        border: 1px solid #E9E1E2;
        border-radius: 12px;
        background: #FFFFFF;
    }

    .dq-kpi-label {
        font-size: 0.8rem;
        color: #655965 !important;
        margin-bottom: 0.65rem;
    }

    .dq-kpi-value {
        font-size: clamp(1.3rem, 2vw, 1.9rem);
        font-weight: 650;
        letter-spacing: -0.045em;
        color: #35313A !important;
        overflow-wrap: anywhere;
        line-height: 1.2;
    }

    .dq-kpi-accent {
        width: 27px;
        height: 3px;
        background: #B85D7B;
        border-radius: 5px;
        margin-top: 0.9rem;
    }

    .dq-status {
        padding: 0.85rem 1rem;
        border: 1px solid #EED6DC;
        border-radius: 9px;
        background: #F9EAE9;
        color: #80515C;
        font-size: 0.88rem;
        line-height: 1.6;
        margin: 0.5rem 0 1rem;
    }

    .dq-footer {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.5rem;
        color: #655965 !important;
        font-size: 0.78rem;
        line-height: 1.6;
        padding: 0.2rem 0 0.8rem;
    }

    .dq-footer span {
        color: #655965 !important;
    }

    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {
        color: #655965 !important;
        opacity: 1 !important;
        font-size: 0.8rem;
    }

    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p,
    [data-testid="stSelectbox"] label,
    [data-testid="stNumberInput"] label {
        color: #625563 !important;
        font-size: 0.82rem;
    }

    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background: #FFFFFF !important;
        border-color: #DCCDD4 !important;
        color: #35313A !important;
        border-radius: 8px !important;
    }

    [data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #35313A !important;
    }

    [data-testid="stNumberInput"] input {
        background: #FFFFFF !important;
        border-color: #DCCDD4 !important;
        color: #35313A !important;
        border-radius: 8px !important;
        -webkit-text-fill-color: #35313A !important;
    }

    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"] {
        background: #FFFFFF !important;
        color: #35313A !important;
    }

    [role="option"] {
        background: #FFFFFF !important;
        color: #35313A !important;
    }

    [role="option"]:hover {
        background: #F2E5E9 !important;
    }

    [data-testid="stDataFrame"] {
        background: #FFFFFF !important;
        border: 1px solid #E2D7DD !important;
        border-radius: 9px !important;
        overflow: hidden;
    }

    [data-testid="stDataFrame"] iframe {
        background: #FFFFFF !important;
    }

    [data-testid="stPlotlyChart"] {
        width: 100% !important;
        min-width: 0 !important;
        background: transparent !important;
    }

    [data-testid="stHorizontalBlock"] {
        min-width: 0;
        gap: 1rem;
    }

    [data-testid="stAlert"] {
        border-radius: 9px !important;
    }

    .stButton button {
        border-radius: 8px;
    }

    @media (max-width: 900px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1.25rem 1rem !important;
        }

        h1 {
            font-size: 2.15rem !important;
        }

        .dq-kpi {
            min-height: 95px;
            padding: 0.9rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Leitura dos dados

@st.cache_data
def carregar_dados():
    compras = pd.read_csv(PASTA_DADOS / "compras_limpo.csv")
    pedidos = pd.read_csv(PASTA_DADOS / "pedidos_limpo.csv")
    validacao = pd.read_csv(PASTA_DADOS / "validacao.csv")

    return compras, pedidos, validacao


compras, pedidos, validacao = carregar_dados()


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


def formatar_moeda(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# Cabeçalho

st.markdown(
    """
    <div class="dq-brand">
        <span class="dq-mark">◌</span>
        <span>Data Quality <span class="dq-brand-accent">Studio</span></span>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dq-eyebrow">CONSULTA · ANÁLISE · DADOS</div>',
    unsafe_allow_html=True
)

st.title("Data Quality Studio")

st.markdown(
    '<p class="dq-intro">'
    'Consulta e análise de dados de compras e pedidos.'
    '</p>',
    unsafe_allow_html=True
)

st.markdown(
    '<hr class="dq-rule">',
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

st.caption("Soma dos valores informados nas compras.")


# Filtros

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
            fillcolor="rgba(184,93,123,0.08)"
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


# Tabela de compras

st.markdown('<hr class="dq-rule">', unsafe_allow_html=True)

st.subheader("Registros de compras")

tabela_compras = compras_filtradas.copy()

tabela_compras["data_compra"] = (
    tabela_compras["data_compra"].dt.strftime("%d/%m/%Y")
)

tabela_compras["valor_total"] = tabela_compras["valor_total"].map(
    lambda x: formatar_moeda(x) if pd.notna(x) else "Não informado"
)

st.dataframe(
    tabela_compras,
    use_container_width=True,
    hide_index=True
)


# Validação

st.markdown('<hr class="dq-rule">', unsafe_allow_html=True)

st.subheader("Inconsistências")

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

    st.dataframe(
        problemas,
        use_container_width=True,
        hide_index=True
    )


# Rodapé

st.markdown('<hr class="dq-rule">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="dq-footer">
        <span>Data Quality Studio · Python e PySpark</span>
        <span>Dados fictícios para fins de demonstração.</span>
    </div>
    """,
    unsafe_allow_html=True
)

# GERENCIAMENTO DE DADOS - CRUD
st.divider()
st.header("Gerenciamento de dados")
st.write("Consulte e gerencie os registros armazenados no Supabase.")


from pathlib import Path

PASTA_DADOS = Path(__file__).parent / "dados_processados"

st.warning(
    "Importe os CSVs apenas se as tabelas estiverem vazias "
    "ou se quiser adicionar registros que ainda não existem."
)

if st.button("Importar CSVs para o Supabase"):
    try:
        compras_csv = PASTA_DADOS / "compras_limpo.csv"
        pedidos_csv = PASTA_DADOS / "pedidos_limpo.csv"

        if not compras_csv.exists() or not pedidos_csv.exists():
            st.error("Não encontrei os dois arquivos CSV.")
        else:
            quantidade_compras = importar_csv_para_supabase(
                str(compras_csv), "compras"
            )

            quantidade_pedidos = importar_csv_para_supabase(
                str(pedidos_csv), "pedidos"
            )

            st.success(
                f"Importação concluída! "
                f"Compras inseridas: {quantidade_compras}. "
                f"Pedidos inseridos: {quantidade_pedidos}."
            )

            st.rerun()

    except Exception as erro:
        st.error(f"Erro na importação: {erro}")

aba_compras, aba_pedidos = st.tabs(["Compras", "Pedidos"])

with aba_compras:
    st.subheader("Registros de compras")

    try:
        dados_compras = listar_registros("compras")
        st.dataframe(dados_compras, use_container_width=True)
        st.caption(f"Total de registros: {len(dados_compras)}")
    except Exception as erro:
        st.error(f"Não foi possível consultar compras: {erro}")

with aba_pedidos:
    st.subheader("Registros de pedidos")

    try:
        dados_pedidos = listar_registros("pedidos")
        st.dataframe(dados_pedidos, use_container_width=True)
        st.caption(f"Total de registros: {len(dados_pedidos)}")
    except Exception as erro:
        st.error(f"Não foi possível consultar pedidos: {erro}")
