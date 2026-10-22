from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

from db import (
    listar_registros,
    inserir_registro,
    atualizar_registro,
    excluir_registro,
    proximo_id,
    proximo_cliente_id,
    importar_dataframe_para_supabase,
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
def carregar_validacao():
    return pd.read_csv(PASTA_DADOS / "validacao.csv")


# Compras e pedidos vêm diretamente do Supabase para refletir as alterações do CRUD.
try:
    compras = pd.DataFrame(listar_registros("compras"))
    pedidos = pd.DataFrame(listar_registros("pedidos"))
    if compras.empty and len(compras.columns) == 0:
        compras = pd.DataFrame(columns=[
            "id_compra", "cliente_id", "data_compra", "valor_total", "metodo_pagamento"
        ])
    if pedidos.empty and len(pedidos.columns) == 0:
        pedidos = pd.DataFrame(columns=[
            "id_pedido", "id_compra", "produto_id", "quantidade", "preco_unitario"
        ])
except Exception as erro:
    st.error("Não foi possível carregar os dados do banco de dados.")
    st.caption(f"Detalhes técnicos: {type(erro).__name__}")
    compras = pd.DataFrame(columns=[
        "id_compra", "cliente_id", "data_compra", "valor_total", "metodo_pagamento"
    ])
    pedidos = pd.DataFrame(columns=[
        "id_pedido", "id_compra", "produto_id", "quantidade", "preco_unitario"
    ])

validacao = carregar_validacao()

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

# GERENCIAMENTO DE DADOS - CRUD
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

    with st.form("form_importar_csv", clear_on_submit=True):
        tabela_csv = st.selectbox(
            "Tabela de destino",
            options=["compras", "pedidos"],
            format_func=lambda x: "Compras" if x == "compras" else "Pedidos",
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
                    st.error("Não foi possível importar o arquivo CSV.")
                    st.code(str(erro))

aba_compras, aba_pedidos = st.tabs(["Compras", "Pedidos"])

METODOS_PAGAMENTO = ["Cartão de Crédito", "Cartão de Débito", "Boleto", "Pix"]

with aba_compras:
    st.subheader("Compras")

    try:
        dados_compras = listar_registros("compras")
        clientes_existentes = sorted({
            int(r["cliente_id"])
            for r in dados_compras
            if r.get("cliente_id") is not None
        })

        # CADASTRAR COMPRA
        with st.expander("Cadastrar nova compra"):
            st.caption(f"ID da próxima compra: {proximo_id('compras')} (gerado automaticamente)")
            cliente_opcoes = ["Novo cliente (gerar ID)"] + clientes_existentes

            with st.form("form_cadastrar_compra", clear_on_submit=True):
                cliente_escolhido = st.selectbox(
                    "Cliente",
                    options=cliente_opcoes,
                    format_func=lambda x: x if isinstance(x, str) else f"Cliente {x}",
                    key="novo_cliente_escolhido",
                )
                data_compra_nova = st.date_input(
                    "Data da compra",
                    key="nova_data_compra",
                )
                valor_total_novo = st.number_input(
                    "Valor total (R$)",
                    min_value=0.01,
                    value=10.0,
                    step=10.0,
                    format="%.2f",
                    key="novo_valor_total",
                )
                metodo_novo = st.selectbox(
                    "Método de pagamento",
                    options=METODOS_PAGAMENTO,
                    key="novo_metodo_pagamento",
                )
                cadastrar_compra = st.form_submit_button("Cadastrar compra")

                if cadastrar_compra:
                    try:
                        cliente_novo_id = (
                            proximo_cliente_id()
                            if cliente_escolhido == "Novo cliente (gerar ID)"
                            else int(cliente_escolhido)
                        )
                        inserir_registro(
                            "compras",
                            {
                                "id_compra": proximo_id("compras"),
                                "cliente_id": cliente_novo_id,
                                "data_compra": data_compra_nova,
                                "valor_total": float(valor_total_novo),
                                "metodo_pagamento": metodo_novo,
                            },
                        )
                        st.success(
                            f"Compra cadastrada! ID da compra: {proximo_id('compras') - 1}. "
                            f"ID do cliente: {cliente_novo_id}."
                        )
                        st.rerun()
                    except Exception as erro:
                        st.error("Não foi possível cadastrar a compra.")
                        st.code(str(erro))

        # EDITAR COMPRA
        with st.expander("Editar compra existente"):
            if dados_compras:
                ids_compras = [int(r["id_compra"]) for r in dados_compras]
                id_editar = st.selectbox(
                    "Selecione a compra",
                    options=ids_compras,
                    format_func=lambda x: f"Compra {x}",
                    key="selecionar_compra_editar",
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

                with st.form(f"form_editar_compra_{id_editar}", clear_on_submit=True):
                    st.caption(f"ID da compra: {id_editar} (não pode ser alterado)")
                    cliente_editado = st.number_input(
                        "ID do cliente",
                        min_value=1,
                        value=max(1, int(registro.get("cliente_id") or 1)),
                        key=f"cliente_editado_{id_editar}",
                    )
                    data_editada = st.date_input(
                        "Data da compra",
                        value=data_atual,
                        key=f"data_editada_{id_editar}",
                    )
                    valor_original = registro.get("valor_total")
                    valor_editado = st.number_input(
                        "Valor total (R$)",
                        min_value=0.01,
                        value=max(0.01, float(valor_original or 0.01)),
                        step=10.0,
                        format="%.2f",
                        key=f"valor_editado_{id_editar}",
                    )
                    metodo_editado = st.selectbox(
                        "Método de pagamento",
                        options=METODOS_PAGAMENTO,
                        index=METODOS_PAGAMENTO.index(metodo_atual),
                        key=f"metodo_editado_{id_editar}",
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
                            st.error("Não foi possível editar a compra.")
                            st.code(str(erro))
            else:
                st.info("Não há compras para editar.")

        # EXCLUIR COMPRA
        with st.expander("Excluir compra"):
            if dados_compras:
                id_excluir_compra = st.selectbox(
                    "Selecione a compra para excluir",
                    options=[int(r["id_compra"]) for r in dados_compras],
                    format_func=lambda x: f"Compra {x}",
                    key="selecionar_compra_excluir",
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
        dados_compras = listar_registros("compras")
        if dados_compras:
            st.dataframe(pd.DataFrame(dados_compras), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma compra cadastrada.")
        st.caption(f"Total de registros: {len(dados_compras)}")

    except Exception as erro:
        st.error("Não foi possível carregar o gerenciamento de compras.")
        st.code(str(erro))

with aba_pedidos:
    st.subheader("Pedidos")

    try:
        dados_pedidos = listar_registros("pedidos")
        compras_disponiveis = listar_registros("compras")
        ids_compras_disponiveis = sorted({
            int(r["id_compra"]) for r in compras_disponiveis
        })

        # CADASTRAR PEDIDO
        with st.expander("Cadastrar novo pedido"):
            st.caption(f"ID do próximo pedido: {proximo_id('pedidos')} (gerado automaticamente)")
            if ids_compras_disponiveis:
                with st.form("form_cadastrar_pedido", clear_on_submit=True):
                    compra_do_pedido = st.selectbox(
                        "Compra vinculada",
                        options=ids_compras_disponiveis,
                        format_func=lambda x: f"Compra {x}",
                        key="nova_compra_pedido",
                    )
                    produto_novo = st.text_input(
                        "ID do produto",
                        key="novo_produto_id",
                    )
                    quantidade_nova = st.number_input(
                        "Quantidade",
                        min_value=1,
                        value=1,
                        step=1,
                        key="nova_quantidade_pedido",
                    )
                    preco_novo = st.number_input(
                        "Preço unitário (R$)",
                        min_value=0.01,
                        value=1.0,
                        step=1.0,
                        format="%.2f",
                        key="novo_preco_unitario",
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
                                        "id_pedido": proximo_id("pedidos"),
                                        "id_compra": int(compra_do_pedido),
                                        "produto_id": produto_novo.strip(),
                                        "quantidade": int(quantidade_nova),
                                        "preco_unitario": float(preco_novo),
                                    },
                                )
                                st.success("Pedido cadastrado com sucesso!")
                                st.rerun()
                        except Exception as erro:
                            st.error("Não foi possível cadastrar o pedido.")
                            st.code(str(erro))
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
                    key="selecionar_pedido_editar",
                )
                pedido = next(r for r in dados_pedidos if int(r["id_pedido"]) == id_pedido_editar)
                compra_atual = int(pedido["id_compra"])
                opcoes_compra_editar = list(ids_compras_disponiveis)
                if compra_atual not in opcoes_compra_editar:
                    opcoes_compra_editar.append(compra_atual)
                opcoes_compra_editar = sorted(opcoes_compra_editar)

                with st.form(f"form_editar_pedido_{id_pedido_editar}", clear_on_submit=True):
                    st.caption(f"ID do pedido: {id_pedido_editar} (não pode ser alterado)")
                    compra_editada = st.selectbox(
                        "Compra vinculada",
                        options=opcoes_compra_editar,
                        index=opcoes_compra_editar.index(compra_atual),
                        format_func=lambda x: f"Compra {x}",
                        key=f"compra_editada_{id_pedido_editar}",
                    )
                    produto_editado = st.text_input(
                        "ID do produto",
                        value=str(pedido.get("produto_id") or ""),
                        key=f"produto_editado_{id_pedido_editar}",
                    )
                    quantidade_editada = st.number_input(
                        "Quantidade",
                        min_value=1,
                        value=max(1, int(pedido.get("quantidade") or 1)),
                        step=1,
                        key=f"quantidade_editada_{id_pedido_editar}",
                    )
                    preco_editado = st.number_input(
                        "Preço unitário (R$)",
                        min_value=0.01,
                        value=max(0.01, float(pedido.get("preco_unitario") or 0.01)),
                        step=1.0,
                        format="%.2f",
                        key=f"preco_editado_{id_pedido_editar}",
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
                            st.error("Não foi possível editar o pedido.")
                            st.code(str(erro))
            else:
                st.info("Não há pedidos para editar.")

        # EXCLUIR PEDIDO
        with st.expander("Excluir pedido"):
            if dados_pedidos:
                id_pedido_excluir = st.selectbox(
                    "Selecione o pedido para excluir",
                    options=[int(r["id_pedido"]) for r in dados_pedidos],
                    format_func=lambda x: f"Pedido {x}",
                    key="selecionar_pedido_excluir",
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
        dados_pedidos = listar_registros("pedidos")
        if dados_pedidos:
            st.dataframe(pd.DataFrame(dados_pedidos), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum pedido cadastrado.")
        st.caption(f"Total de registros: {len(dados_pedidos)}")

    except Exception as erro:
        st.error("Não foi possível carregar o gerenciamento de pedidos.")
        st.code(str(erro))


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
