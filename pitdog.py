import streamlit as st
import pandas as pd
import itertools
from datetime import datetime
import os
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import altair as alt

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Gestão - Clips Burger", layout="centered", initial_sidebar_state="expanded")

# Nome do arquivo CSV para armazenar os dados
CSV_FILE = 'recebimentos.csv'

# ----- Funções Auxiliares -----
def parse_menu_string(menu_data_string):
    """Parses a multi-line string containing menu items and prices."""
    menu = {}
    lines = menu_data_string.strip().split("\n")
    for line in lines:
        parts = line.split("R$ ")
        if len(parts) == 2:
            name = parts[0].strip()
            try:
                price = float(parts[1].replace(",", "."))
                menu[name] = price
            except ValueError:
                st.warning(f"Preço inválido para '{name}'. Ignorando item.")
        elif line.strip():
            st.warning(f"Formato inválido na linha do cardápio: '{line}'. Ignorando linha.")
    return menu

def load_data():
    """Carregar os dados do CSV ou inicializar um DataFrame vazio."""
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            if 'Data' in df.columns:
                try:
                    df['Data'] = pd.to_datetime(df['Data'])
                except Exception as e:
                    st.warning(f"Erro ao converter a coluna 'Data': {e}")
            return df
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo CSV: {e}")
            return pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])
    else:
        return pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])

def save_data(df):
    """Salvar os dados no arquivo CSV."""
    try:
        df['Data'] = df['Data'].dt.strftime('%Y-%m-%d')
        df.to_csv(CSV_FILE, index=False)
        st.success("Dados salvos com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar os dados: {e}")

def format_currency(value):
    """Formata um valor como moeda brasileira."""
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ Inválido"

# ----- Função de Análise Combinatória Exaustiva -----
def exhaustive_combinations(menu_items, target_value):
    """
    Faz uma análise combinatória exaustiva para encontrar combinações de itens
    que se aproximam do valor-alvo sem ultrapassá-lo.
    """
    best_combination = None
    best_value = 0

    # Gerar todas as combinações possíveis
    for r in range(1, len(menu_items) + 1):  # Tamanhos das combinações (1 item até todos os itens)
        for combination in itertools.combinations(menu_items.items(), r):
            combo_dict = {item[0]: 1 for item in combination}  # Cada item é usado uma vez na combinação
            total_value = sum(item[1] for item in combination)

            if total_value <= target_value and total_value > best_value:
                best_combination = combo_dict
                best_value = total_value

    return best_combination, best_value

# ----- Interface Streamlit -----
# Carregar os dados existentes
df_receipts = load_data()

st.title("Sistema de Gestão - Clips Burger")
st.markdown("Bem-vindo! Gerencie os recebimentos e explore combinações de vendas.")

# Configurações na barra lateral
with st.sidebar:
    st.header("⚙️ Configurações")
    drink_percentage = st.slider("Percentual para Bebidas (%) 🍹", 0, 100, 20, 5)
    sandwich_percentage = 100 - drink_percentage
    st.caption(f"(Sanduíches: {sandwich_percentage}%)")

# Abas principais
tab1, tab2, tab3 = st.tabs(["📈 Resumo", "🧩 Combinações", "💰 Recebimentos"])

# Aba 1: Resumo das Vendas
with tab1:
    st.header("📈 Resumo das Vendas")
    st.markdown("Carregue um arquivo de vendas para análise.")
    uploaded_file = st.file_uploader("Envie um arquivo (.csv ou .xlsx)", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_vendas = pd.read_csv(uploaded_file)
            else:
                df_vendas = pd.read_excel(uploaded_file)
            st.success("Arquivo carregado com sucesso!")
            st.dataframe(df_vendas)
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")

# Aba 2: Combinações
with tab2:
    st.header("🧩 Combinações de Produtos")
    st.markdown("Explore combinações de produtos com base no valor total.")
    total_pagamento = st.number_input("Digite o valor total (R$)", min_value=0.0, step=0.50)

    if total_pagamento > 0:
        st.subheader("Resultados")
        bebidas_precos = parse_menu_string("""
            Suco R$ 10,00
            Creme R$ 15,00
            Refri caçula R$ 3,50
            Refri Lata R$ 7,00
            Refri 600ml R$ 8,00
            Refri 1L R$ 10,00
            Refri 2L R$ 15,00
            Água R$ 3,00
            Água com Gás R$ 4,00
        """)
        sanduiches_precos = parse_menu_string("""
            X Salada Simples R$ 18,00
            X Salada Especial R$ 20,00
            X Duplo R$ 24,00
            X Bacon Simples R$ 22,00
            X Bacon Especial R$ 24,00
            X Bacon Duplo R$ 28,00
            X Hamburgão R$ 35,00
            X Mata-Fome R$ 39,00
            Frango Simples R$ 22,00
            Frango Especial R$ 24,00
            Frango Tudo R$ 30,00
            Lombo Simples R$ 23,00
            Lombo Especial R$ 25,00
            Lombo Tudo R$ 31,00
            Filé Simples R$ 28,00
            Filé Especial R$ 30,00
            Filé Tudo R$ 36,00
            Cebola R$ 0,50
        """)

        target_bebidas = total_pagamento * (drink_percentage / 100)
        target_sanduiches = total_pagamento - target_bebidas

        # Análise combinatória exaustiva para bebidas
        comb_bebidas, total_bebidas = exhaustive_combinations(bebidas_precos, target_bebidas)

        # Análise combinatória exaustiva para sanduíches
        comb_sanduiches, total_sanduiches = exhaustive_combinations(sanduiches_precos, target_sanduiches)

        # Exibição dos resultados
        st.markdown(f"**Bebidas (Meta: {format_currency(target_bebidas)}):**")
        if comb_bebidas:
            for item, qty in comb_bebidas.items():
                st.write(f"- {qty}x {item} ({format_currency(bebidas_precos[item] * qty)})")
            st.markdown(f"**Total Bebidas**: {format_currency(total_bebidas)}")
        else:
            st.write("Nenhuma combinação encontrada para bebidas.")

        st.markdown(f"**Sanduíches (Meta: {format_currency(target_sanduiches)}):**")
        if comb_sanduiches:
            for item, qty in comb_sanduiches.items():
                st.write(f"- {qty}x {item} ({format_currency(sanduiches_precos[item] * qty)})")
            st.markdown(f"**Total Sanduíches**: {format_currency(total_sanduiches)}")
        else:
            st.write("Nenhuma combinação encontrada para sanduíches.")

# Aba 3: Cadastro de Recebimentos
with tab3:
    st.header("💰 Cadastro de Recebimentos")
    with st.form("form_recebimentos"):
        data = st.date_input("Data", datetime.now().date())
        dinheiro = st.number_input("Dinheiro (R$)", min_value=0.0, step=0.50)
        cartao = st.number_input("Cartão (R$)", min_value=0.0, step=0.50)
        pix = st.number_input("Pix (R$)", min_value=0.0, step=0.50)
        submitted = st.form_submit_button("Salvar")
        if submitted:
            novo_registro = pd.DataFrame([{"Data": data, "Dinheiro": dinheiro, "Cartao": cartao, "Pix": pix}])
            df_receipts = pd.concat([df_receipts, novo_registro], ignore_index=True)
            save_data(df_receipts)
            st.success("Recebimento salvo com sucesso!")
            st.experimental_rerun()

    st.subheader("Recebimentos Registrados")
    if not df_receipts.empty:
        # Garantir que as colunas de valores numéricos estão no tipo correto
        df_receipts['Dinheiro'] = pd.to_numeric(df_receipts['Dinheiro'], errors='coerce').fillna(0)
        df_receipts['Cartao'] = pd.to_numeric(df_receipts['Cartao'], errors='coerce').fillna(0)
        df_receipts['Pix'] = pd.to_numeric(df_receipts['Pix'], errors='coerce').fillna(0)
        df_receipts['Total'] = df_receipts['Dinheiro'] + df_receipts['Cartao'] + df_receipts['Pix']
        st.dataframe(df_receipts)

        # Gráfico de barras
        st.subheader("📊 Gráfico de Barras")
        st.bar_chart(df_receipts[['Dinheiro', 'Cartao', 'Pix']])

        # Gráfico de pizza
        st.subheader("🎯 Gráfico de Pizza")
        total_metodos = {
            'Dinheiro': df_receipts['Dinheiro'].sum(),
            'Cartão': df_receipts['Cartao'].sum(),
            'Pix': df_receipts['Pix'].sum(),
        }
        fig_pie = px.pie(
            names=total_metodos.keys(),
            values=total_metodos.values(),
            title="Distribuição dos Métodos de Pagamento",
        )
        st.plotly_chart(fig_pie)

        # Gráfico de linha
        st.subheader("📈 Evolução dos Recebimentos")
        df_diario = df_receipts.groupby('Data')['Total'].sum().reset_index()
        st.line_chart(df_diario.set_index('Data'))

        # Gráfico cumulativo de área
        st.subheader("📊 Gráfico de Área Cumulativa")
        df_receipts['Cumulativo'] = df_receipts['Total'].cumsum()
        area_chart = alt.Chart(df_receipts).mark_area().encode(
            x='Data:T',
            y='Cumulativo:Q',
            tooltip=['Data', 'Cumulativo']
        ).properties(
            title="Somatório Cumulativo dos Recebimentos"
        )
        st.altair_chart(area_chart, use_container_width=True)

    else:
        st.info("Nenhum dado disponível para o mapa de calor.")
