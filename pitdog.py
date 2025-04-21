import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import random
import os

# --- CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA CHAMADA STREAMLIT) ---
st.set_page_config(page_title="Análise de Vendas & Combinações", layout="wide", initial_sidebar_state="expanded")

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

# Função para carregar os dados do CSV (se existir) ou inicializar um DataFrame vazio
def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # Converter a coluna 'Data' para datetime se não estiver no formato correto
            if 'Data' in df.columns:
                try:
                    df['Data'] = pd.to_datetime(df['Data'])
                except Exception as e:
                    st.warning(f"Aviso: Erro ao converter a coluna 'Data' do CSV: {e}. Certifique-se de que as datas estejam em um formato reconhecível.")
            return df
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo CSV: {e}")
            return pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])
    else:
        return pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])

# Função para salvar os dados no CSV
def save_data(df):
    try:
        # Converter a coluna 'Data' para string no formato adequado para salvar no CSV
        df['Data'] = df['Data'].dt.strftime('%Y-%m-%d')
        df.to_csv(CSV_FILE, index=False)
        st.success(f"Dados salvos com sucesso em '{CSV_FILE}'!")
    except Exception as e:
        st.error(f"Erro ao salvar os dados no arquivo CSV: {e}")

# Carregar os dados
df_receipts = load_data()

# ----- Funções para visualização -----
def plot_daily_receipts(df, date_column, value_column, title):
    if not df.empty:
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(date_column, axis=alt.Axis(title='Data')),
            y=alt.Y(value_column, axis=alt.Axis(title='Valor (R$)')),
            tooltip=[date_column, value_column]
        ).properties(
            title=title
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir no gráfico.")

def display_receipts_table(df):
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado de recebimento cadastrado.")

# ----- Interface Streamlit -----

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
1. Ajuste as configurações na barra lateral (para análise do arquivo)
2. Faça o upload do seu arquivo de transações (.csv ou .xlsx) na aba "📈 Resumo das Vendas"
3. Cadastre os valores recebidos diariamente na aba "💰 Cadastro de Recebimentos"
4. Explore os resultados nas abas abaixo
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

# --- Abas ---
tab1, tab2, tab3 = st.tabs(["📈 Resumo das Vendas", "🧩 Detalhes das Combinações", "💰 Cadastro de Recebimentos"])

# --- Tab 1: Resumo das Vendas ---
with tab1:
    st.header("📈 Resumo das Vendas")
    arquivo = st.file_uploader("📤 Envie o arquivo de transações (.csv ou .xlsx)", type=["csv", "xlsx"])

    # Inicialize 'vendas' com um dicionário vazio
    vendas = {}

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

                vendas = df_filtered.groupby('Forma Nomeada')['Valor_Numeric'].sum().to_dict()

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

                # Gráfico de vendas por forma de pagamento
                st.subheader("Vendas por Forma de Pagamento")
                if vendas:  # Verificação correta para dicionário vazio
                    df_vendas = pd.DataFrame(list(vendas.items()), columns=['Forma de Pagamento', 'Valor Total'])
                    df_vendas['Valor Formatado'] = df_vendas['Valor Total'].apply(format_currency)
                    st.bar_chart(df_vendas.set_index('Forma de Pagamento')['Valor Total'])
                    st.dataframe(df_vendas[['Forma de Pagamento', 'Valor Formatado']], use_container_width=True)
                else:
                    st.warning("Nenhum dado de venda para exibir.")

            except Exception as e:
                st.error(f"Erro no processamento do arquivo: {str(e)}")
    else:
        st.info("✨ Aguardando o envio do arquivo de transações para iniciar a análise...")

# --- Tab 2: Detalhes das Combinações ---
with tab2:
    st.header("🧩 Detalhes das Combinações Geradas")
    st.caption(f"Alocação: {drink_percentage}% bebidas | {sandwich_percentage}% sanduíches")

    ordem_formas = [
        'Débito Visa', 'Débito MasterCard', 'Débito Elo',
        'Crédito Visa', 'Crédito MasterCard', 'Crédito Elo', 'PIX'
    ]
    vendas_ordenadas = {forma: vendas.get(forma, 0) for forma in ordem_formas}
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

            total_bebidas_inicial = calculate_combination_value(comb_bebidas_rounded, bebidas_precos)
            total_sanduiches_inicial = calculate_combination_value(comb_sanduiches_rounded, sanduiches_precos)
            total_geral_inicial = total_bebidas_inicial + total_sanduiches_inicial

            comb_sanduiches_final, total_sanduiches_final = comb_sanduiches_rounded.copy(), total_sanduiches_inicial

            if total_geral_inicial < total_pagamento and "Cebola" in sanduiches_precos:
                diferenca = total_pagamento - total_geral_inicial
                preco_cebola = sanduiches_precos["Cebola"]
                cebolas_adicionar = min(int(round(diferenca / preco_cebola)), 20)
                if cebolas_adicionar > 0:
                    comb_sanduiches_final["Cebola"] = comb_sanduiches_final.get("Cebola", 0) + cebolas_adicionar
                    total_sanduiches_final = calculate_combination_value(comb_sanduiches_final, sanduiches_precos)

            total_bebidas_final = calculate_combination_value(comb_bebidas_rounded, bebidas_precos)
            total_geral_final = total_bebidas_final + total_sanduiches_final

            with st.expander(f"**{forma}** (Total: {format_currency(total_pagamento)})", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader(f"🍹 Bebidas: {format_currency(target_bebidas)}")
                    if comb_bebidas_rounded:
                        for nome, qtt in comb_bebidas_rounded.items():
                            val_item = bebidas_precos[nome] * qtt
                            st.markdown(f"- **{qtt}** **{nome}:** {format_currency(val_item)}")
                        st.divider()
                        st.metric("Total Calculado", format_currency(total_bebidas_final))
                    else:
                        st.info("Nenhuma bebida na combinação")

                with col2:
                    st.subheader(f"🍔 Sanduíches: {format_currency(target_sanduiches)}")
                    if comb_sanduiches_final:
                        original_sandwich_value = calculate_combination_value(comb_sanduiches_rounded, sanduiches_precos)
                        has_onion_adjustment = "Cebola" in comb_sanduiches_final and comb_sanduiches_final.get("Cebola", 0) > comb_sanduiches_rounded.get("Cebola", 0)

                        for nome, qtt in comb_sanduiches_final.items():
                            display_name = nome
                            prefix = ""

                            if nome == "Cebola" and has_onion_adjustment:
                                display_name = "Cebola (Ajuste)"
                                prefix = "🔹 "

                            val_item = sanduiches_precos[nome] * qtt
                            st.markdown(f"- {prefix}**{qtt}** **{display_name}:** {format_currency(val_item)}")

                        st.divider()
                        st.metric("Total Calculado", format_currency(total_sanduiches_final))
                    else:
                        st.info("Nenhum sanduíche na combinação")

                st.divider()
                diff = total_geral_final - total_pagamento
                st.metric(
                    "💰 TOTAL GERAL (Calculado)",
                    format_currency(total_geral_final),
                    delta=f"{format_currency(diff)} vs Meta",
                    delta_color="normal" if diff <= 0 else "inverse"
                )

# --- Tab 3: Cadastro de Recebimentos ---

# --- Tab 3: Cadastro de Recebimentos (Versão Integrada) ---
with tab3:
    # Configuração de estilo
    st.markdown("""
    <style>
        .receipt-card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .metric-card {
            background-color: #f8f9fa;
            border-left: 4px solid #2e86ab;
            border-radius: 5px;
            padding: 10px;
        }
        .header-icon {
            font-size: 1.5em;
            vertical-align: middle;
            margin-right: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Layout principal
    col1, col2 = st.columns([1, 1.5], gap="large")

    with col1:
        # Card de Cadastro
        with st.container(border=True):
            st.markdown('<h2><span class="header-icon">💰</span>Cadastro</h2>', unsafe_allow_html=True)
            
            with st.form("receipt_form", clear_on_submit=True):
                data = st.date_input("**Data**", datetime.now().date(), key="receipt_date")
                
                cols = st.columns(3)
                with cols[0]:
                    cash = st.number_input("**Dinheiro**", min_value=0.0, value=0.0, step=10.0, format="%.2f", key="cash_input")
                with cols[1]:
                    card = st.number_input("**Cartão**", min_value=0.0, value=0.0, step=10.0, format="%.2f", key="card_input")
                with cols[2]:
                    pix = st.number_input("**Pix**", min_value=0.0, value=0.0, step=10.0, format="%.2f", key="pix_input")
                
                submitted = st.form_submit_button("💾 Salvar Recebimento", use_container_width=True)
                
                if submitted:
                    if data > datetime.now().date():
                        st.error("Data não pode ser futura!")
                    elif cash == 0 and card == 0 and pix == 0:
                        st.warning("Insira pelo menos um valor positivo!")
                    else:
                        new_entry = {
                            'Data': pd.to_datetime(data),
                            'Dinheiro': cash,
                            'Cartao': card,
                            'Pix': pix
                        }
                        df_receipts = pd.concat([df_receipts, pd.DataFrame([new_entry])], ignore_index=True)
                        save_data(df_receipts)
                        st.success(f"Recebimento de {data.strftime('%d/%m/%Y')} salvo!")
                        time.sleep(1)
                        st.rerun()

    with col2:
        # Seção de Visualização
        if not df_receipts.empty:
            # Pré-processamento dos dados
            df = df_receipts.copy()
            df['Data'] = pd.to_datetime(df['Data'])
            df['Total'] = df['Dinheiro'] + df['Cartao'] + df['Pix']
            df['Ano'] = df['Data'].dt.year
            df['Mes'] = df['Data'].dt.month
            df['Dia'] = df['Data'].dt.day
            df['Data_Formatada'] = df['Data'].dt.strftime('%d/%m/%Y')
            
            # Filtros
            with st.expander("🔍 Filtros", expanded=True):
                cols = st.columns(3)
                with cols[0]:
                    year = st.selectbox("Ano", sorted(df['Ano'].unique(), index=0)
                    df = df[df['Ano'] == year]
                with cols[1]:
                    month = st.selectbox("Mês", sorted(df['Mes'].unique()), format_func=lambda x: [
                        'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                        'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
                    ][x-1]
                    df = df[df['Mes'] == month]
                with cols[2]:
                    day_options = ['Todos'] + sorted(df['Dia'].unique())
                    day = st.selectbox("Dia", day_options)
                    if day != 'Todos':
                        df = df[df['Dia'] == day]

            # Métricas
            with st.container(border=True):
                cols = st.columns(4)
                with cols[0]:
                    st.markdown('<div class="metric-card"><b>Total</b><br>R$ {:.2f}</div>'.format(df['Total'].sum()), unsafe_allow_html=True)
                with cols[1]:
                    st.markdown('<div class="metric-card"><b>Dinheiro</b><br>R$ {:.2f}</div>'.format(df['Dinheiro'].sum()), unsafe_allow_html=True)
                with cols[2]:
                    st.markdown('<div class="metric-card"><b>Cartão</b><br>R$ {:.2f}</div>'.format(df['Cartao'].sum()), unsafe_allow_html=True)
                with cols[3]:
                    st.markdown('<div class="metric-card"><b>Pix</b><br>R$ {:.2f}</div>'.format(df['Pix'].sum()), unsafe_allow_html=True)

            # Abas de visualização
            tab_graph, tab_table, tab_export = st.tabs(["📊 Gráficos", "📋 Tabela", "💾 Exportar"])

            with tab_graph:
                st.markdown("**Totais Diários**")
                st.bar_chart(df.set_index('Data_Formatada')['Total'], color="#2e86ab")
                
                st.markdown("**Distribuição por Tipo**")
                df_melted = df.melt(id_vars=['Data_Formatada'], value_vars=['Dinheiro', 'Cartao', 'Pix'])
                st.altair_chart(
                    alt.Chart(df_melted).mark_bar().encode(
                        x='Data_Formatada:N',
                        y='value:Q',
                        color='variable:N',
                        tooltip=['Data_Formatada', 'variable', 'value']
                    ).properties(height=300),
                    use_container_width=True
                )

            with tab_table:
                edit = st.toggle("Habilitar Edição", False)
                if edit:
                    edited_df = st.data_editor(
                        df[['Data_Formatada', 'Dinheiro', 'Cartao', 'Pix', 'Total']],
                        column_config={
                            "Data_Formatada": "Data",
                            "Total": st.column_config.NumberColumn("Total", format="R$ %.2f", disabled=True)
                        },
                        num_rows="dynamic"
                    )
                    
                    if st.button("Salvar Alterações"):
                        # Lógica para atualizar os dados originais
                        st.success("Dados atualizados!")
                else:
                    st.dataframe(
                        df[['Data_Formatada', 'Dinheiro', 'Cartao', 'Pix', 'Total']].rename(
                            columns={'Data_Formatada': 'Data'}
                        ).style.format({
                            'Dinheiro': 'R$ {:.2f}',
                            'Cartao': 'R$ {:.2f}',
                            'Pix': 'R$ {:.2f}',
                            'Total': 'R$ {:.2f}'
                        }),
                        hide_index=True
                    )

            with tab_export:
                format_type = st.radio("Formato", ["CSV", "Excel"])
                
                if format_type == "CSV":
                    st.download_button(
                        "Baixar CSV",
                        df.to_csv(index=False).encode('utf-8'),
                        f"recebimentos_{year}_{month}.csv",
                        "text/csv"
                    )
                else:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                    st.download_button(
                        "Baixar Excel",
                        output.getvalue(),
                        f"recebimentos_{year}_{month}.xlsx",
                        "application/vnd.ms-excel"
                    )

        else:
            st.info("Nenhum recebimento cadastrado ainda.")
            st.image("https://cdn-icons-png.flaticon.com/512/4076/4076478.png", width=150)

if __name__ == '__main__':
    pass
