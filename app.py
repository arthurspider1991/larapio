import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(layout="wide")

# =====================================================
# CONEXÃO COM O BANCO DE DADOS
# =====================================================
# check_same_thread=False permite usar a conexão
# dentro do fluxo do Streamlit
conn = sqlite3.connect("financeiro.db", check_same_thread=False)
cursor = conn.cursor()

# Cria a tabela se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT,
    descricao TEXT,
    valor REAL,
    categoria TEXT,
    data TEXT
)
""")
conn.commit()

# =====================================================
# CATEGORIAS FIXAS (MENU)
# =====================================================
CATEGORIAS = [
    "Alimentação",
    "Transporte",
    "Moradia",
    "Lazer",
    "Saúde",
    "Educação",
    "Investimentos",
    "Outros"
]

# =====================================================
# TÍTULO
# =====================================================
st.title("💰 Meu Controle Financeiro")

# =====================================================
# FORMULÁRIO DE NOVA MOVIMENTAÇÃO
# =====================================================
st.subheader("Nova Movimentação")

with st.form("form_mov"):

    col1, col2, col3 = st.columns(3)

    # Tipo: Receita ou Despesa
    tipo = col1.selectbox("Tipo", ["Receita", "Despesa"])

    # Descrição
    descricao = col2.text_input("Descrição")

    # Valor
    valor = col3.number_input("Valor", min_value=0.0, format="%.2f")

    col4, col5 = st.columns(2)

    # Categoria via menu
    categoria = col4.selectbox("Categoria", CATEGORIAS)

    # Data
    data = col5.date_input("Data", datetime.today())

    submitted = st.form_submit_button("Salvar")

    if submitted:
        cursor.execute("""
            INSERT INTO movimentacoes (tipo, descricao, valor, categoria, data)
            VALUES (?, ?, ?, ?, ?)
        """, (tipo, descricao, valor, categoria, str(data)))
        conn.commit()
        st.success("Movimentação salva!")
        st.rerun()

# =====================================================
# CARREGAR DADOS
# =====================================================
df = pd.read_sql_query(
    "SELECT * FROM movimentacoes ORDER BY data DESC",
    conn
)

# =====================================================
# RESUMO FINANCEIRO
# =====================================================
if not df.empty:

    receitas = df[df["tipo"] == "Receita"]["valor"].sum()
    despesas = df[df["tipo"] == "Despesa"]["valor"].sum()
    saldo = receitas - despesas

    col1, col2, col3 = st.columns(3)

    col1.metric("Receitas", f"R$ {receitas:.2f}")
    col2.metric("Despesas", f"R$ {despesas:.2f}")
    col3.metric("Saldo", f"R$ {saldo:.2f}")

    st.divider()

    # =================================================
    # LISTAGEM DE MOVIMENTAÇÕES
    # =================================================
    st.subheader("Movimentações")

    for index, row in df.iterrows():

        col1, col2, col3, col4, col5, col6 = st.columns([1.2, 2, 1, 1, 0.8, 0.8])

        # Data
        col1.write(row["data"])

        # Descrição + Categoria
        col2.write(f"{row['descricao']} ({row['categoria']})")

        # Valor
        col3.write(f"R$ {row['valor']:.2f}")

        # Tipo
        col4.write(row["tipo"])

        # Botão Editar
        if col5.button("✏️", key=f"edit_{row['id']}"):
            st.session_state["editar_id"] = row["id"]

        # Botão Deletar (na mesma linha)
        if col6.button("🗑️", key=f"del_{row['id']}"):
            cursor.execute(
                "DELETE FROM movimentacoes WHERE id=?",
                (row["id"],)
            )
            conn.commit()
            st.rerun()

    # =================================================
    # EDIÇÃO DE MOVIMENTAÇÃO
    # =================================================
    if "editar_id" in st.session_state:

        editar_id = st.session_state["editar_id"]
        registro = df[df["id"] == editar_id].iloc[0]

        st.divider()
        st.subheader("Editar Movimentação")

        with st.form("form_edit"):

            tipo_edit = st.selectbox(
                "Tipo",
                ["Receita", "Despesa"],
                index=0 if registro["tipo"] == "Receita" else 1
            )

            descricao_edit = st.text_input(
                "Descrição",
                registro["descricao"]
            )

            valor_edit = st.number_input(
                "Valor",
                value=float(registro["valor"]),
                format="%.2f"
            )

            categoria_edit = st.selectbox(
                "Categoria",
                CATEGORIAS,
                index=CATEGORIAS.index(registro["categoria"])
            )

            data_edit = st.date_input(
                "Data",
                datetime.strptime(registro["data"], "%Y-%m-%d")
            )

            salvar_edit = st.form_submit_button("Salvar Alterações")

            if salvar_edit:
                cursor.execute("""
                    UPDATE movimentacoes
                    SET tipo=?, descricao=?, valor=?, categoria=?, data=?
                    WHERE id=?
                """, (
                    tipo_edit,
                    descricao_edit,
                    valor_edit,
                    categoria_edit,
                    str(data_edit),
                    editar_id
                ))

                conn.commit()

                # Remove modo edição
                del st.session_state["editar_id"]

                st.success("Atualizado com sucesso!")
                st.rerun()

    st.divider()

    # =================================================
    # GRÁFICO DE DESPESAS POR CATEGORIA
    # =================================================
    st.subheader("Despesas por Categoria")

    despesas_cat = (
        df[df["tipo"] == "Despesa"]
        .groupby("categoria")["valor"]
        .sum()
    )

    st.bar_chart(despesas_cat)

else:
    st.info("Nenhuma movimentação cadastrada ainda.")