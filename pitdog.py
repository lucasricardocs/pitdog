import streamlit as st
import pandas as pd
import random
import time
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

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

def calculate_combination_value(combination, item_prices):
    """Calculates the total value of a combination based on item prices."""
    return sum(item_prices.get(name, 0) * quantity for name, quantity in combination.items())

def round_to_50_or_00(value):
    """Arredonda para o múltiplo de 0.50 mais próximo"""
    return round(value * 2) / 2

def generate_initial_combination(item_prices, combination_size):
    """Generates a random initial combination for the local search."""
    combination = {}
    item_names = list(item_prices.keys())
    if not item_names:
        return combination
    size = min(combination_size, len(item_names))
    chosen_names = random.sample(item_names, size)
    for name in chosen_names:
        combination[name] = round_to_50_or_00(random.uniform(1, 10))
    return combination

def adjust_with_onions(combination, item_prices, target_value):
    """
    Ajusta a combinação adicionando cebolas se o valor for menor que o target.
    Retorna a combinação modificada e o valor final.
    Limita a quantidade máxima de cebolas a 20 unidades.
    """
    current_value = calculate_combination_value(combination, item_prices)
    difference = target_value - current_value
    
    if difference <= 0 or "Cebola" not in item_prices:
        return combination, current_value
    
    onion_price = item_prices["Cebola"]
    num_onions = min(int(round(difference / onion_price)), 20)  # Limite de 20 cebolas
    
    if num_onions > 0:
        current_onions = combination.get("Cebola", 0)
        total_onions = current_onions + num_onions
        if total_onions > 20:
            num_onions = 20 - current_onions
            if num_onions <= 0:
                return combination, current_value
        
        combination["Cebola"] = current_onions + num_onions
    
    final_value = calculate_combination_value(combination, item_prices)
    return combination, final_value

def local_search_optimization(item_prices, target_value, combination_size, max_iterations):
    """
    Versão modificada para:
    - Valores terminarem em ,00 ou ,50
    - Nunca ultrapassar o target_value
    """
    if not item_prices or target_value <= 0:
        return {}

    best_combination = generate_initial_combination(item_prices, combination_size)
    best_combination = {k: round_to_50_or_00(v) for k, v in best_combination.items()}
    current_value = calculate_combination_value(best_combination, item_prices)
    
    best_diff = abs(target_value - current_value) + (1000 if current_value > target_value else 0)
    current_items = list(best_combination.keys())

    for _ in range(max_iterations):
        if not current_items: break

        neighbor = best_combination.copy()
        item_to_modify = random.choice(current_items)

        change = random.choice([-0.50, 0.50, -1.00, 1.00])
        neighbor[item_to_modify] = round_to_50_or_00(neighbor[item_to_modify] + change)
        neighbor[item_to_modify] = max(0.50, neighbor[item_to_modify])

        neighbor_value = calculate_combination_value(neighbor, item_prices)
        neighbor_diff = abs(target_value - neighbor_value) + (1000 if neighbor_value > target_value else 0)

        if neighbor_diff < best_diff:
            best_diff = neighbor_diff
            best_combination = neighbor

    return best_combination

def format_currency(value):
    """Formats a number as Brazilian Real currency."""
    if pd.isna(value):
        return "R$ -"
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ Inválido"

def plot_daily_sales(df):
    """Gráfico de vendas por dia"""
    df['Data'] = pd.to_datetime(df['Data'])
    daily_sales = df.groupby(df['Data'].dt.date)['Valor_Numeric'].sum()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    daily_sales.plot(kind='line', marker='o', ax=ax)
    ax.set_title('Vendas Diárias')
    ax.set_xlabel('Data')
    ax.set_ylabel('Valor (R$)')
    ax.grid(True)
    st.pyplot(fig)

def plot_payment_methods(df):
    """Gráfico de formas de pagamento"""
    payment_methods = df.groupby('Forma Nomeada')['Valor_Numeric'].sum().sort_values(ascending=False)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    payment_methods.plot(kind='bar', ax=ax)
    ax.set_title('Vendas por Forma de Pagamento')
    ax.set_xlabel('Forma de Pagamento')
    ax.set_ylabel('Valor (R$)')
    plt.xticks(rotation=45)
    st.pyplot(fig)

def plot_hourly_sales(df):
    """Gráfico de vendas por hora do dia"""
    if 'Hora' not in df.columns:
        return
    
    df['Hora'] = pd.to_datetime(df['Hora'], format='%H:%M').dt.hour
    hourly_sales = df.groupby('Hora')['Valor_Numeric'].sum()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    hourly_sales.plot(kind='bar', ax=ax)
    ax.set_title('Vendas por Hora do Dia')
    ax.set_xlabel('Hora')
    ax.set_ylabel('Valor (R$)')
    st.pyplot(fig)

# ----- Interface Streamlit -----
st.set_page_config(page_title="Análise de Vendas & Combinações", layout="wide", initial_sidebar_state="expanded")

# Colunas para Título e Emoji
col_title1, col_title2 = st.columns([0.9, 0.1])
with col_title1:
    st.title("📊 Análise de Vendas e Geração de Combinações")
with col_title2:
    st.image("https://cdn-icons-png.flaticon.com/128/1041/1041880.png", width=70)

st.markdown("""
Bem-vindo(a)! Esta ferramenta ajuda a visualizar suas vendas por forma de pagamento
e tenta encontrar combinações *hipotéticas* de produtos que poderiam corresponder a esses totais.

**Como usar:**
1. Ajuste as configurações na barra lateral
2. Faça o upload do seu arquivo de transações (.csv ou .xlsx)
3. Explore os resultados nas abas abaixo
""")
st.divider()

# --- Configuration Sidebar ---
with st.sidebar:
    st.header("⚙️ Configurações")
    drink_percentage = st.slider(
        "Percentual para Bebidas (%) 🍹",
        min_value=0, max_value=100, value=20, step=5
    )
    sandwich_percentage = 100 - drink_percentage
    st.caption(f"({sandwich_percentage}% será alocado para Sanduíches 🍔)")

    tamanho_combinacao_bebidas = st.slider(
        "Número de tipos de Bebidas",
        min_value=1, max_value=10, value=5, step=1
    )
    tamanho_combinacao_sanduiches = st.slider(
        "Número de tipos de Sanduíches",
        min_value=1, max_value=10, value=5, step=1
    )
    max_iterations = st.select_slider(
        "Qualidade da Otimização ✨",
        options=[1000, 5000, 10000, 20000, 50000],
        value=10000
    )
    st.info("Lembre-se: As combinações são aproximações heurísticas.")

# --- File Upload ---
arquivo = st.file_uploader("📤 Envie o arquivo de transações (.csv ou .xlsx)", type=["csv", "xlsx"])

if arquivo:
    with st.spinner(f'Processando "{arquivo.name}"...'):
        try:
            if arquivo.name.endswith(".csv"):
                try:
                    df = pd.read_csv(arquivo, sep=';', encoding='utf-8', dtype=str)
                except Exception:
                    arquivo.seek(0)
                    try:
                        df = pd.read_csv(arquivo, sep=',', encoding='utf-8', dtype=str)
                    except Exception as e:
                        st.error(f"Não foi possível ler o CSV. Erro: {e}")
                        st.stop()
            else:
                df = pd.read_excel(arquivo, dtype=str)

            st.success(f"Arquivo '{arquivo.name}' carregado com sucesso!")

            # Processamento dos dados
            required_columns = ['Tipo', 'Bandeira', 'Valor']
            if not all(col in df.columns for col in required_columns):
                st.error(f"Erro: O arquivo precisa conter as colunas: {', '.join(required_columns)}")
                st.stop()

            df_processed = df.copy()
            df_processed['Tipo'] = df_processed['Tipo'].str.lower().str.strip().fillna('desconhecido')
            df_processed['Bandeira'] = df_processed['Bandeira'].str.lower().str.strip().fillna('desconhecida')
            df_processed['Valor_Numeric'] = pd.to_numeric(
                df_processed['Valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
                errors='coerce'
            )
            df_processed.dropna(subset=['Valor_Numeric'], inplace=True)

            # Adicionando coluna de data se existir no arquivo
            if 'Data' in df_processed.columns:
                try:
                    df_processed['Data'] = pd.to_datetime(df_processed['Data'])
                except:
                    st.warning("Não foi possível converter a coluna 'Data' para formato de data")

            df_processed['Categoria'] = df_processed['Tipo'] + ' ' + df_processed['Bandeira']
            categorias_desejadas = {
                'crédito à vista elo': 'Crédito Elo',
                'crédito à vista mastercard': 'Crédito MasterCard',
                'crédito à vista visa': 'Crédito Visa',
                'débito elo': 'Débito Elo',
                'débito mastercard': 'Débito MasterCard',
                'débito visa': 'Débito Visa',
                'pix': 'PIX'
            }
            df_processed['Forma Nomeada'] = df_processed['Categoria'].map(categorias_desejadas)
            df_filtered = df_processed.dropna(subset=['Forma Nomeada']).copy()

            if df_filtered.empty:
                st.warning("Nenhuma transação encontrada para as formas de pagamento mapeadas.")
                st.stop()

            vendas = df_filtered.groupby('Forma Nomeada')['Valor_Numeric'].sum()

            # Definição dos Cardápios
            dados_sanduiches = """
            X Salada Simples R$ 18,00
            X Salada Especial R$ 20,00
            X Especial Duplo R$ 24,00
            X Bacon Simples R$ 22,00
            X Bacon Especial R$ 24,00
            X Bacon Duplo R$ 28,00
            X Hamburgão R$ 35,00
            X Mata-Fome R$ 39,00
            X Frango Simples R$ 22,00
            X Frango Especial R$ 24,00
            X Frango Bacon R$ 27,00
            X Frango Tudo R$ 30,00
            X Lombo Simples R$ 23,00
            X Lombo Especial R$ 25,00
            X Lombo Bacon R$ 28,00
            X Lombo Tudo R$ 31,00
            X Filé Simples R$ 28,00
            X Filé Especial R$ 30,00
            X Filé Bacon R$ 33,00
            X Filé Tudo R$ 36,00
            Cebola R$ 0.50
            """
            dados_bebidas = """
            Suco R$ 10,00
            Creme R$ 15,00
            Refri caçula R$ 3.50
            Refri Lata R$ 7,00
            Refri 600 R$ 8,00
            Refri 1L R$ 10,00
            Refri 2L R$ 15,00
            Água R$ 3,00
            Água com Gas R$ 4,00
            """
            sanduiches_precos = parse_menu_string(dados_sanduiches)
            bebidas_precos = parse_menu_string(dados_bebidas)

            if not sanduiches_precos or not bebidas_precos:
                st.error("Erro ao carregar cardápios. Verifique os dados no código.")
                st.stop()

            # Abas de resultados
            tab1, tab2, tab3 = st.tabs(["📈 Resumo das Vendas", "🧩 Detalhes das Combinações", "📄 Dados Processados"])

            with tab1:
                st.header("📈 Resumo das Vendas")
                
                # Gráfico de vendas por forma de pagamento
                st.subheader("Vendas por Forma de Pagamento")
                if not vendas.empty:
                    df_vendas = vendas.reset_index()
                    df_vendas.columns = ['Forma de Pagamento', 'Valor Total']
                    df_vendas['Valor Formatado'] = df_vendas['Valor Total'].apply(format_currency)
                    st.bar_chart(df_vendas.set_index('Forma de Pagamento')['Valor Total'])
                    st.dataframe(df_vendas[['Forma de Pagamento', 'Valor Formatado']], use_container_width=True)
                else:
                    st.warning("Nenhum dado de venda para exibir.")
                
                # Novos gráficos adicionados
                if 'Data' in df_processed.columns:
                    st.subheader("Vendas Diárias")
                    plot_daily_sales(df_processed)
                
                st.subheader("Distribuição por Forma de Pagamento")
                plot_payment_methods(df_filtered)
                
                if 'Hora' in df_processed.columns:
                    st.subheader("Vendas por Hora do Dia")
                    plot_hourly_sales(df_processed)
                
                # Heatmap de vendas por dia da semana e hora (se dados disponíveis)
                if 'Data' in df_processed.columns and 'Hora' in df_processed.columns:
                    try:
                        st.subheader("Heatmap de Vendas (Dia da Semana x Hora)")
                        df_heatmap = df_processed.copy()
                        df_heatmap['Dia da Semana'] = df_heatmap['Data'].dt.day_name()
                        df_heatmap['Hora'] = pd.to_datetime(df_heatmap['Hora'], format='%H:%M').dt.hour
                        
                        heatmap_data = df_heatmap.pivot_table(
                            index='Dia da Semana',
                            columns='Hora',
                            values='Valor_Numeric',
                            aggfunc='sum',
                            fill_value=0
                        )
                        
                        # Ordenar dias da semana
                        dias_ordenados = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        heatmap_data = heatmap_data.reindex(dias_ordenados)
                        
                        fig, ax = plt.subplots(figsize=(12, 6))
                        sns.heatmap(heatmap_data, cmap='YlGnBu', ax=ax)
                        ax.set_title('Vendas por Dia da Semana e Hora')
                        ax.set_xlabel('Hora do Dia')
                        ax.set_ylabel('Dia da Semana')
                        st.pyplot(fig)
                    except Exception as e:
                        st.warning(f"Não foi possível gerar o heatmap: {str(e)}")

            with tab2:
                st.header("🧩 Detalhes das Combinações Geradas")
                st.caption(f"Alocação: {drink_percentage}% bebidas | {sandwich_percentage}% sanduíches")

                ordem_formas = [
                    'Débito Visa', 'Débito MasterCard', 'Débito Elo',
                    'Crédito Visa', 'Crédito MasterCard', 'Crédito Elo', 'PIX'
                ]
                vendas_ordenadas = {forma: vendas[forma] for forma in ordem_formas if forma in vendas}
                for forma, total in vendas.items():
                    if forma not in vendas_ordenadas:
                        vendas_ordenadas[forma] = total

                for forma, total_pagamento in vendas_ordenadas.items():
                    if total_pagamento <= 0:
                        continue

                    with st.spinner(f"Gerando combinação para {forma}..."):
                        target_bebidas = round_to_50_or_00(total_pagamento * (drink_percentage / 100.0))
                        target_sanduiches = round_to_50_or_00(total_pagamento - target_bebidas)

                        comb_bebidas = local_search_optimization(
                            bebidas_precos, target_bebidas, tamanho_combinacao_bebidas, max_iterations
                        )
                        comb_sanduiches = local_search_optimization(
                            sanduiches_precos, target_sanduiches, tamanho_combinacao_sanduiches, max_iterations
                        )

                        comb_bebidas_rounded = {name: round(qty) for name, qty in comb_bebidas.items() if round(qty) > 0}
                        comb_sanduiches_rounded = {name: round(qty) for name, qty in comb_sanduiches.items() if round(qty) > 0}

                        comb_sanduiches_final, total_sanduiches = adjust_with_onions(
                            comb_sanduiches_rounded, sanduiches_precos, target_sanduiches
                        )
                        total_bebidas = calculate_combination_value(comb_bebidas_rounded, bebidas_precos)
                        total_geral = total_bebidas + total_sanduiches

                    with st.expander(f"**{forma}** (Total: {format_currency(total_pagamento)})", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader(f"🍹 Bebidas: {format_currency(target_bebidas)}")
                            if comb_bebidas_rounded:
                                for nome, qtt in comb_bebidas_rounded.items():
                                    val_item = bebidas_precos[nome] * qtt
                                    st.markdown(f"- **{qtt}** **{nome}:** {format_currency(val_item)}")
                                st.divider()
                                st.metric("Total Calculado", format_currency(total_bebidas))
                            else:
                                st.info("Nenhuma bebida na combinação")

                        with col2:
                            st.subheader(f"🍔 Sanduíches: {format_currency(target_sanduiches)}")
                            if comb_sanduiches_final:
                                # Calcula se as cebolas foram adicionadas para ajuste
                                original_sandwich_value = calculate_combination_value(comb_sanduiches_rounded, sanduiches_precos)
                                has_onion_adjustment = "Cebola" in comb_sanduiches_final and comb_sanduiches_final["Cebola"] > comb_sanduiches_rounded.get("Cebola", 0)
                                
                                for nome, qtt in comb_sanduiches_final.items():
                                    display_name = nome
                                    prefix = ""
                                    
                                    if nome == "Cebola" and has_onion_adjustment:
                                        display_name = "Cebola (Ajuste)"
                                        prefix = "🔹 "
                                    
                                    val_item = sanduiches_precos[nome] * qtt
                                    st.markdown(f"- {prefix}**{qtt}** **{display_name}:** {format_currency(val_item)}")
                                
                                st.divider()
                                st.metric("Total Calculado", format_currency(total_sanduiches))
                            else:
                                st.info("Nenhum sanduíche na combinação")

                        st.divider()
                        diff = total_geral - total_pagamento
                        st.metric(
                            "💰 TOTAL GERAL (Calculado)",
                            format_currency(total_geral),
                            delta=f"{format_currency(diff)} vs Meta",
                            delta_color="normal" if diff <= 0 else "inverse"
                        )

            with tab3:
                st.header("📄 Tabela de Dados Processados")
                cols_to_show = ['Tipo', 'Bandeira', 'Valor', 'Categoria', 'Forma Nomeada', 'Valor_Numeric']
                if 'Data' in df_processed.columns:
                    cols_to_show.insert(0, 'Data')
                if 'Hora' in df_processed.columns:
                    cols_to_show.insert(1, 'Hora')
                st.dataframe(df_filtered[cols_to_show], use_container_width=True)

        except Exception as e:
            st.error(f"Erro no processamento: {str(e)}")
else:
    st.info("✨ Aguardando o envio do arquivo de transações para iniciar a análise...")
