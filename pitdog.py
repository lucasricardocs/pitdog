import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import random
import os
# --- CONSTANTES E CONFIGURAÇÕES ---
CONFIG = {
    "page_title": "Gestão - Clips Burger",
    "layout": "centered",
    "sidebar_state": "expanded",
    "excel_file": "recebimentos.xlsx",
    "logo_path": "logo.png"
}
CARDAPIOS = {
    "sanduiches": {
        "X Salada Simples": 18.00,
        "X Salada Especial": 20.00,
        "X Especial Duplo": 24.00,
        "X Bacon Simples": 22.00,
        "X Bacon Especial": 24.00,
        "X Bacon Duplo": 28.00,
        "X Hamburgão": 35.00,
        "X Mata-Fome": 39.00,
        "X Frango Simples": 22.00,
        "X Frango Especial": 24.00,
        "X Frango Bacon": 27.00,
        "X Frango Tudo": 30.00,
        "X Lombo Simples": 23.00,
        "X Lombo Especial": 25.00,
        "X Lombo Bacon": 28.00,
        "X Lombo Tudo": 31.00,
        "X Filé Simples": 28.00,
        "X Filé Especial": 30.00,
        "X Filé Bacon": 33.00,
        "X Filé Tudo": 36.00
    },
    "bebidas": {
        "Suco": 10.00,
        "Creme": 15.00,
        "Refri caçula": 3.50,
        "Refri Lata": 7.00,
        "Refri 600": 8.00,
        "Refri 1L": 10.00,
        "Refri 2L": 15.00,
        "Água": 3.00,
        "Água com Gas": 4.00
    }
}
FORMAS_PAGAMENTO = {
    'crédito à vista elo': 'Crédito Elo',
    'crédito à vista mastercard': 'Crédito MasterCard',
    'crédito à vista visa': 'Crédito Visa',
    'crédito à vista american express': 'Crédito Amex',
    'débito elo': 'Débito Elo',
    'débito mastercard': 'Débito MasterCard',
    'débito visa': 'Débito Visa',
    'pix': 'PIX'
}
# --- FUNÇÕES UTILITÁRIAS ---
def format_currency(value):
    """Formata um valor como moeda brasileira."""
    if pd.isna(value) or value is None:
        return "R$ -"
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def init_data_file():
    """Inicializa o arquivo de dados se não existir."""
    if not os.path.exists(CONFIG["excel_file"]):
        pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix']).to_excel(
            CONFIG["excel_file"], index=False)
def load_data():
    """Carrega os dados do arquivo Excel."""
    try:
        if os.path.exists(CONFIG["excel_file"]):
            df = pd.read_excel(CONFIG["excel_file"])
            if not df.empty:
                df['Data'] = pd.to_datetime(df['Data'])
                return df.sort_values('Data', ascending=False)
        return pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])
def save_data(df):
    """Salva os dados no arquivo Excel."""
    try:
        df['Data'] = pd.to_datetime(df['Data'])
        df.to_excel(CONFIG["excel_file"], index=False)
        st.success("Dados salvos com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
def round_to_50_or_00(value):
    """Arredonda para o múltiplo de 0.50 mais próximo."""
    return round(value * 2) / 2
def calculate_combination_value(combination, item_prices):
    """Calcula o valor total de uma combinação."""
    return sum(item_prices.get(name, 0) * quantity for name, quantity in combination.items())
def generate_initial_combination(item_prices, combination_size):
    """Gera uma combinação inicial aleatória."""
    if not item_prices:
        return {}

    items = list(item_prices.keys())
    size = min(combination_size, len(items))
    return {
        name: round_to_50_or_00(random.uniform(1, 10))
        for name in random.sample(items, size)
    }
def optimize_combination(item_prices, target_value, combination_size, max_iterations):
    """Otimiza combinações de produtos para atingir um valor alvo."""
    if not item_prices or target_value <= 0:
        return {}
    best_combination = generate_initial_combination(item_prices, combination_size)
    best_diff = abs(target_value - calculate_combination_value(best_combination, item_prices))
    best_diff += 10000 if calculate_combination_value(best_combination, item_prices) > target_value else 0
    for _ in range(max * iterations):
        if not best_combination:
            break
        neighbor = best_combination.copy()
        item = random.choice(list(best_combination.keys()))
        change = random.choice([-0.50, 0.50, -1.00, 1.00])

        neighbor[item] = max(0.50, round_to_50_or_00(neighbor[item] + change))
        neighbor_value = calculate_combination_value(neighbor, item_prices)
        neighbor_diff = abs(target_value - neighbor_value)
        neighbor_diff += 10000 if neighbor_value > target_value else 0
        if neighbor_diff < best_diff:
            best_diff = neighbor_diff
            best_combination = neighbor
    return best_combination
def create_altair_chart(data, chart_type, x_col, y_col, color_col=None, title=None, interactive=True):
    """Cria gráficos Altair com configuração padronizada."""
    if chart_type == 'line':
        chart = alt.Chart(data).mark_line(point=True).encode(
            x=alt.X(f'{x_col}:T', title=x_col),
            y=alt.Y(f'{y_col}:Q', title=y_col),
            tooltip=[x_col, y_col]
        )
    elif chart_type == 'bar':
        chart = alt.Chart(data).mark_bar().encode(
            x=alt.X(f'{x_col}:N', title=x_col),
            y=alt.Y(f'{y_col}:Q', title=y_col),
            color=alt.Color(f'{color_col}:N') if color_col else alt.value('steelblue'),
            tooltip=[x_col, y_col]
        )
    elif chart_type == 'pie':
        chart = alt.Chart(data).mark_arc().encode(
            theta=alt.Theta(f'{y_col}:Q', stack=True),
            color=alt.Color(f'{x_col}:N', legend=alt.Legend(title=x_col)),
            tooltip=[x_col, y_col]
        )

    chart = chart.properties(
        title=title if title else f'{y_col} por {x_col}',
        width=700,
        height=400
    )

    return chart.interactive() if interactive else chart
# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title=CONFIG["page_title"],
    layout=CONFIG["layout"],
    initial_sidebar_state=CONFIG["sidebar_state"]
)
# --- INICIALIZAÇÃO ---
init_data_file()
if 'df_receipts' not in st.session_state:
    st.session_state.df_receipts = load_data()
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'vendas_data' not in st.session_state:
    st.session_state.vendas_data = None
# --- INTERFACE PRINCIPAL ---
col_title1, col_title2 = st.columns([0.30, 0.70])
with col_title1:
    try:
        st.image(CONFIG["logo_path"], width=1000)
    except FileNotFoundError:
        st.warning("Logo não encontrada")
with col_title2:
    st.title("Sistema de Gestão")
    st.markdown("<p style='font-weight:bold; font-size:30px; margin-top:-15px'>Clip's Burger</p>", 
               unsafe_allow_html=True)
st.markdown("""
Bem-vindo(a)! Esta ferramenta ajuda a visualizar suas vendas por forma de pagamento
e tenta encontrar combinações hipotéticas de produtos que poderiam corresponder a esses totais.
""")
st.divider()
# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurações")
    drink_percentage = st.slider(
        "Percentual para Bebidas (%) 🍹",
        min_value=0, max_value=100, value=20, step=5
    )
    st.caption(f"({100 - drink_percentage}% será alocado para Sanduíches 🍔)")
    tamanho_combinacao_bebidas = st.slider(
        "Número de tipos de Bebidas", 1, 10, 5, 1)
    tamanho_combinacao_sanduiches = st.slider(
        "Número de tipos de Sanduíches", 1, 10, 5, 1)
    max_iterations = st.select_slider(
        "Qualidade da Otimização ✨",
        options=[1000, 5000, 10000, 20000, 50000],
        value=10000
    )
    st.info("Lembre-se: As combinações são aproximações heurísticas.")
# --- ABAS PRINCIPAIS ---
tab1, tab2, tab3 = st.tabs(["📈 Resumo das Vendas", "🧩 Detalhes das Combinações", "💰 Cadastro de Recebimentos"])
with tab1:
    # Seção de upload de arquivo
    st.header("📤 Upload de Dados")
    arquivo = st.file_uploader("Envie o arquivo de transações (.csv ou .xlsx)", 
                             type=["csv", "xlsx"])

    if arquivo:
        try:
            # Processamento do arquivo
            with st.spinner("Processando arquivo..."):
                # Verificar o tipo de arquivo
                if arquivo.name.endswith(".csv"):
                    try:
                        df = pd.read_csv(arquivo, sep=';', encoding='utf-8', dtype=str)
                    except pd.errors.ParserError:
                        arquivo.seek(0)
                        try:
                            df = pd.read_csv(arquivo, sep=',', encoding='utf-8', dtype=str)
                        except:
                            arquivo.seek(0)
                            df = pd.read_csv(arquivo, engine='python', dtype=str)
                else:
                    df = pd.read_excel(arquivo, dtype=str)

                # Verificar colunas obrigatórias
                required_cols = ['Tipo', 'Bandeira', 'Valor']
                if not all(col in df.columns for col in required_cols):
                    st.error(f"Erro: O arquivo precisa conter as colunas: {', '.join(required_cols)}")
                    st.stop()
                # Processamento dos dados
                df['Tipo'] = df['Tipo'].str.lower().str.strip().fillna('desconhecido')
                df['Bandeira'] = df['Bandeira'].str.lower().str.strip().fillna('desconhecida')
                df['Valor'] = pd.to_numeric(
                    df['Valor'].str.replace('.', '').str.replace(',', '.'), 
                    errors='coerce')
                df = df.dropna(subset=['Valor'])

                df['Forma'] = (df['Tipo'] + ' ' + df['Bandeira']).map(FORMAS_PAGAMENTO)
                df = df.dropna(subset=['Forma'])

                if df.empty:
                    st.warning("Nenhuma transação válida encontrada.")
                    st.stop()
                vendas = df.groupby('Forma')['Valor'].sum().reset_index()
                total_vendas = vendas['Valor'].sum()

                # Salva os dados no session state
                st.session_state.uploaded_data = df
                st.session_state.vendas_data = vendas
                st.session_state.total_vendas = total_vendas

            # Seção de Visualização de Dados
            st.header("📊 Visualização de Dados")

            # Gráfico de Barras
            st.subheader("Total de Vendas por Forma de Pagamento")
            bar_chart = create_altair_chart(
                vendas, 'bar', 'Forma', 'Valor', 'Forma',
                title=''
            ).properties(
                width=800,
                height=500
            )
            st.altair_chart(bar_chart, use_container_width=True)

            # Seção de Parâmetros Financeiros
            st.header("⚙️ Parâmetros Financeiros")
            col1, col2 = st.columns(2)
            with col1:
                salario_minimo = st.number_input("Salário Mínimo (R$)", value=1518.0, step=50.0)
            with col2:
                custo_contadora = st.number_input("Custo com Contadora (R$)", value=316.0, step=10.0)

            # Seção de Resultados
            st.header("💰 Resultados Financeiros")

            # Métricas Principais
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Faturamento Bruto", format_currency(total_vendas))
            with col2:
                imposto_simples = total_vendas * 0.06
                st.metric("Imposto Simples (6%)", format_currency(imposto_simples))
            with col3:
                fgts = salario_minimo * 0.08
                ferias = (salario_minimo / 12) * (4/3)
                decimo_terceiro = salario_minimo / 12
                custo_funcionario = salario_minimo + fgts + ferias + decimo_terceiro
                st.metric("Custo Funcionário CLT", format_currency(custo_funcionario))

            # Cálculo do Total de Custos
            total_custos = imposto_simples + custo_funcionario + custo_contadora
            lucro_estimado = total_vendas - total_custos

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total de Custos", format_currency(total_custos))
            with col2:
                st.metric("Lucro Estimado", format_currency(lucro_estimado))

            # Seção de Detalhamento
            st.header("🔍 Detalhamento")

            tab_detalhes1, tab_detalhes2, tab_detalhes3 = st.tabs([
                "📝 Composição de Custos", 
                "📚 Explicação dos Cálculos",
                "🍰 Gráfico de Composição"
            ])

            with tab_detalhes1:
                st.subheader("Composição dos Custos")
                st.markdown(f"""
                - Imposto Simples Nacional (6%): {format_currency(imposto_simples)}
                - Custo Funcionário CLT: {format_currency(custo_funcionario)}
                - Custo Contadora: {format_currency(custo_contadora)}
                """)

            with tab_detalhes2:
                st.subheader("Fórmulas Utilizadas")
                st.markdown("""
                1. Imposto Simples Nacional  
                Faturamento Bruto × 6%  

                2. Custo Funcionário CLT  
                Salário + FGTS (8%) + Férias (1 mês + 1/3) + 13º Salário  

                3. Total de Custos  
                Imposto + Funcionário + Contadora  

                4. Lucro Estimado  
                Faturamento Bruto - Total de Custos
                """)

            with tab_detalhes3:
                st.subheader("Composição dos Custos")
                custos_df = pd.DataFrame({
                    'Item': ['Impostos', 'Funcionário', 'Contadora'],
                    'Valor': [imposto_simples, custo_funcionario, custo_contadora]
                })

                graf_composicao = alt.Chart(custos_df).mark_arc().encode(
                    theta='Valor',
                    color='Item',
                    tooltip=['Item', alt.Tooltip('Valor', format='$.2f')]
                ).properties(
                    width=600,
                    height=500
                )

                st.altair_chart(graf_composicao, use_container_width=True)

        except Exception as e:
            st.error(f"Erro no processamento: {str(e)}")
    else:
        st.info("Por favor, envie um arquivo de transações para análise.")
with tab2:
    st.header("🧩 Detalhes das Combinações Geradas")

    if st.session_state.vendas_data is None:
        st.warning("Por favor, carregue os dados de vendas na aba 'Resumo das Vendas' primeiro.")
        st.stop()

    vendas = st.session_state.vendas_data
    sandwich_percentage = 100 - drink_percentage
    st.caption(f"Alocação: {drink_percentage}% bebidas | {sandwich_percentage}% sanduíches")
    bebidas_precos = CARDAPIOS['bebidas']
    sanduiches_precos = CARDAPIOS['sanduiches']

    ordem_formas = [
        'Débito Visa', 'Débito MasterCard', 'Débito Elo',
        'Crédito Visa', 'Crédito MasterCard', 'Crédito Elo',
        'Crédito Amex', 'PIX'
    ]

    for forma in ordem_formas:
        if forma not in vendas['Forma'].values:
            continue

        total_pagamento = vendas.loc[vendas['Forma'] == forma, 'Valor'].values[0]
        if total_pagamento <= 0:
            continue
        with st.expander(f"{forma} (Total: {format_currency(total_pagamento)})", expanded=False):
            target_bebidas = round_to_50_or_00(total_pagamento * (drink_percentage / 100.0))
            target_sanduiches = round_to_50_or_00(total_pagamento - target_bebidas)
            comb_bebidas = optimize_combination(
                bebidas_precos, target_bebidas, tamanho_combinacao_bebidas, max_iterations
            )
            comb_sanduiches = optimize_combination(
                sanduiches_precos, target_sanduiches, tamanho_combinacao_sanduiches, max_iterations
            )
            comb_bebidas_rounded = {k: round(v) for k, v in comb_bebidas.items() if round(v) > 0}
            comb_sanduiches_rounded = {k: round(v) for k, v in comb_sanduiches.items() if round(v) > 0}
            total_bebidas = calculate_combination_value(comb_bebidas_rounded, bebidas_precos)
            total_sanduiches = calculate_combination_value(comb_sanduiches_rounded, sanduiches_precos)
            total_geral = total_bebidas + total_sanduiches
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(f"🍹 Bebidas: {format_currency(target_bebidas)}")
                if comb_bebidas_rounded:
                    for nome, qtd in comb_bebidas_rounded.items():
                        val = bebidas_precos[nome] * qtd
                        st.markdown(f"- {qtd} {nome}: {format_currency(val)}")
                    st.divider()
                    st.metric("Total Bebidas", format_currency(total_bebidas))
                else:
                    st.info("Nenhuma bebida na combinação")
            with col2:
                st.subheader(f"🍔 Sanduíches: {format_currency(target_sanduiches)}")
                if comb_sanduiches_rounded:
                    for nome, qtd in comb_sanduiches_rounded.items():
                        val = sanduiches_precos[nome] * qtd
                        st.markdown(f"- {qtd} {nome}: {format_currency(val)}")
                    st.divider()
                    st.metric("Total Sanduíches", format_currency(total_sanduiches))
                else:
                    st.info("Nenhum sanduíche na combinação")
            st.divider()
            diff = total_geral - total_pagamento
            st.metric(
                "💰 TOTAL GERAL",
                format_currency(total_geral),
                delta=f"{format_currency(abs(diff))} {'a menos' if diff < 0 else 'a mais'} que o total",
                delta_color="normal" if diff <= 0 else "inverse"
            )
with tab3:
    st.header("💰 Cadastro e Análise de Recebimentos")

    # Seção 1: Formulário para adicionar novos dados
    with st.expander("➕ Adicionar Novo Registro", expanded=True):
        with st.form("add_receipt_form"):
            cols = st.columns([1, 1, 1, 1])
            with cols[0]:
                data = st.date_input("Data*", value=datetime.now())

            st.write("Valores por Forma de Pagamento")
            cols = st.columns(3)
            with cols[0]:
                dinheiro = st.number_input("Dinheiro (R$)", min_value=0.0, step=10.0)
            with cols[1]:
                cartao = st.number_input("Cartão (R$)", min_value=0.0, step=10.0)
            with cols[2]:
                pix = st.number_input("PIX (R$)*", min_value=0.0, step=10.0)

            total_dia = dinheiro + cartao + pix
            st.metric("Total do Dia", format_currency(total_dia))

            submitted = st.form_submit_button("✅ Salvar Registro")

            if submitted:
                if total_dia <= 0:
                    st.error("O total do dia deve ser maior que zero!")
                else:
                    try:
                        new_record = pd.DataFrame({
                            'Data': [data],
                            'Dinheiro': [dinheiro],
                            'Cartao': [cartao],
                            'Pix': [pix]
                        })
                        st.session_state.df_receipts = pd.concat(
                            [st.session_state.df_receipts, new_record], 
                            ignore_index=True
                        )
                        save_data(st.session_state.df_receipts)
                        st.success("Registro salvo com sucesso!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {str(e)}")
    # Seção 2: Visualização dos dados e gráficos
    if not st.session_state.df_receipts.empty:
        # Filtros de data
        st.subheader("📅 Filtros de Período")

        # Opções de filtro
        filtro_tipo = st.radio("Tipo de Filtro:", 
                             ["Intervalo de Datas", "Mês Específico"], 
                             horizontal=True)

        if filtro_tipo == "Intervalo de Datas":
            cols = st.columns(2)
            with cols[0]:
                inicio = st.date_input("Data inicial", 
                                     value=st.session_state.df_receipts['Data'].min())
            with cols[1]:
                fim = st.date_input("Data final", 
                                  value=st.session_state.df_receipts['Data'].max())
        else:
            # Filtro por mês
            meses_disponiveis = sorted(st.session_state.df_receipts['Data'].dt.to_period('M').unique(), reverse=True)
            mes_selecionado = st.selectbox("Selecione o mês:", 
                                         options=meses_disponiveis,
                                         format_func=lambda x: x.strftime('%B/%Y'))

            inicio = pd.to_datetime(mes_selecionado.start_time)
            fim = pd.to_datetime(mes_selecionado.end_time)

        # Aplica filtros
        df_filtered = st.session_state.df_receipts[
            (st.session_state.df_receipts['Data'] >= pd.to_datetime(inicio)) & 
            (st.session_state.df_receipts['Data'] <= pd.to_datetime(fim))
        ].copy()

        if not df_filtered.empty:
            # Adiciona coluna de Total
            df_filtered['Total'] = df_filtered['Dinheiro'] + df_filtered['Cartao'] + df_filtered['Pix']

            # Calcula totais por forma de pagamento
            totais = {
                'Dinheiro': df_filtered['Dinheiro'].sum(),
                'Cartão': df_filtered['Cartao'].sum(),
                'PIX': df_filtered['Pix'].sum()
            }
            total_periodo = sum(totais.values())

            # Seção 3: Métricas Resumo
            st.subheader("📊 Resumo do Período")

            # CSS para ajustar o tamanho das métricas
            st.markdown("""
            <style>
                div[data-testid="stMetric"] {
                    padding: 5px 10px;
                }
                div[data-testid="stMetric"] > div {
                    gap: 2px;
                }
                div[data-testid="stMetric"] label {
                    font-size: 14px !important;
                    font-weight: 500 !important;
                    color: #6b7280 !important;
                }
                div[data-testid="stMetric"] > div > div {
                    font-size: 18px !important;
                    font-weight: 600 !important;
                }
            </style>
            """, unsafe_allow_html=True)

            # Layout compacto em 2 linhas de 4 colunas
            cols1 = st.columns(4)
            cols2 = st.columns(4)

            with cols1[0]:
                st.metric("Dinheiro", format_currency(totais['Dinheiro']), 
                         help="Total em recebimentos de dinheiro")
            with cols1[1]:
                st.metric("Cartão", format_currency(totais['Cartão']),
                         help="Total em recebimentos por cartão")
            with cols1[2]:
                st.metric("PIX", format_currency(totais['PIX']),
                         help="Total em recebimentos por PIX")
            with cols1[3]:
                st.metric("Total Geral", format_currency(total_periodo),
                         help="Soma de todas as formas de pagamento")

            with cols2[0]:
                st.metric("Média Diária", format_currency(df_filtered['Total'].mean()),
                         help="Média de vendas por dia")
            with cols2[1]:
                st.metric("Maior Venda", format_currency(df_filtered['Total'].max()),
                         help=f"Dia: {df_filtered.loc[df_filtered['Total'].idxmax(), 'Data'].strftime('%d/%m')}")
            with cols2[2]:
                st.metric("Dias Registrados", len(df_filtered),
                         help="Total de dias com vendas registradas")
            with cols2[3]:
                st.metric("Dias sem Registro", (fim - inicio).days + 1 - len(df_filtered),
                         help="Dias do período sem vendas registradas")

            # Seção 4: Gráficos
            st.subheader("📈 Visualizações Gráficas")

            tab_graficos1, tab_graficos2, tab_graficos3 = st.tabs(["Distribuição", "Comparação", "Acumulado"])

            with tab_graficos1:
                # Gráfico de Pizza
                df_pie = pd.DataFrame({
                    'Forma': list(totais.keys()),
                    'Valor': list(totais.values())
                })

                pie_chart = alt.Chart(df_pie).mark_arc().encode(
                    theta='Valor',
                    color=alt.Color('Forma', legend=alt.Legend(title="Forma de Pagamento")),
                    tooltip=['Forma', 'Valor']
                ).properties(
                    height=400,
                    title='Distribuição dos Recebimentos'
                )
                st.altair_chart(pie_chart, use_container_width=True)

            with tab_graficos2:
                # Gráfico de Barras
                df_bar = df_filtered.melt(id_vars=['Data'], 
                                        value_vars=['Dinheiro', 'Cartao', 'Pix'],
                                        var_name='Forma', 
                                        value_name='Valor')

                bar_chart = alt.Chart(df_bar).mark_bar().encode(
                    x='monthdate(Data):O',
                    y='sum(Valor):Q',
                    color='Forma',
                    tooltip=['Forma', 'sum(Valor)']
                ).properties(
                    height=400,
                    title='Vendas por Forma de Pagamento'
                )
                st.altair_chart(bar_chart, use_container_width=True)

            with tab_graficos3:
                # Gráfico Acumulado
                df_acumulado = df_filtered.sort_values('Data').copy()
                df_acumulado['Acumulado'] = df_acumulado['Total'].cumsum()

                line_chart = alt.Chart(df_acumulado).mark_line(
                    point=True,
                    strokeWidth=3,
                    color='red'
                ).encode(
                    x='Data:T',
                    y='Acumulado:Q',
                    tooltip=['Data', 'Acumulado']
                ).properties(
                    height=400,
                    title='Receita Total Acumulada'
                )

                st.altair_chart(line_chart, use_container_width=True)

            # Seção 5: Tabela de Dados
            st.subheader("📋 Dados Detalhados")
            st.dataframe(
                df_filtered.sort_values('Data', ascending=False).style.format({
                    'Dinheiro': lambda x: format_currency(x),
                    'Cartao': lambda x: format_currency(x),
                    'Pix': lambda x: format_currency(x),
                    'Total': lambda x: format_currency(x)
                }),
                use_container_width=True,
                height=400
            )

        else:
            st.warning("Nenhum registro encontrado no período selecionado")
    else:
        st.info("Nenhum dado cadastrado ainda. Adicione seu primeiro registro acima.")
# Adicionar rodapé
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: small;'>
        © 2025 Clips Burger - Sistema de Gestão | Desenvolvido com ❤️ e Streamlit
    </div>
    """, 
    unsafe_allow_html=True
)
Editar
Análise e Implementação de Melhorias para o Aplicativo Streamlit
Análise dos Erros

O principal problema é que a tab3 ("💰 Cadastro e Análise de Recebimentos") não mostra dados quando o arquivo CSV não foi carregado na tab1 ("📈 Resumo das Vendas"). Isso acontece porque:

    Na tab3, você está exibindo dados de receitas que são independentes do upload na tab1, mas o código não está tratando corretamente esse fluxo separado.
    O sistema tem duas fontes de dados independentes:
        Arquivo CSV/Excel de transações (carregado na tab1)
        Registros de recebimentos armazenados no arquivo "recebimentos.xlsx" (tab3)
    A tab3 não depende diretamente do upload da tab1, mas o código não está tratando essa independência adequadamente.

Implementação do Gerador de PDF para tab1

Vou adicionar um gerador de PDF que explica os dados apresentados na tab1. O PDF incluirá:

    Resumo das vendas por forma de pagamento
    Resultados financeiros (faturamento, impostos, custos)
    Explicação dos cálculos utilizados
    Gráficos relevantes

Continuar
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import random
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import numpy as np

# --- CONSTANTES E CONFIGURAÇÕES ---
CONFIG = {
    "page_title": "Gestão - Clips Burger",
    "layout": "centered",
    "sidebar_state": "expanded",
    "excel_file": "recebimentos.xlsx",
    "logo_path": "logo.png"
}
CARDAPIOS = {
    "sanduiches": {
        "X Salada Simples": 18.00,
        "X Salada Especial": 20.00,
        "X Especial Duplo": 24.00,
        "X Bacon Simples": 22.00,
        "X Bacon Especial": 24.00,
        "X Bacon Duplo": 28.00,
        "X Hamburgão": 35.00,
        "X Mata-Fome": 39.00,
        "X Frango Simples": 22.00,
        "X Frango Especial": 24.00,
        "X Frango Bacon": 27.00,
        "X Frango Tudo": 30.00,
        "X Lombo Simples": 23.00,
        "X Lombo Especial": 25.00,
        "X Lombo Bacon": 28.00,
        "X Lombo Tudo": 31.00,
        "X Filé Simples": 28.00,
        "X Filé Especial": 30.00,
        "X Filé Bacon": 33.00,
        "X Filé Tudo": 36.00
    },
    "bebidas": {
        "Suco": 10.00,
        "Creme": 15.00,
        "Refri caçula": 3.50,
        "Refri Lata": 7.00,
        "Refri 600": 8.00,
        "Refri 1L": 10.00,
        "Refri 2L": 15.00,
        "Água": 3.00,
        "Água com Gas": 4.00
    }
}
FORMAS_PAGAMENTO = {
    'crédito à vista elo': 'Crédito Elo',
    'crédito à vista mastercard': 'Crédito MasterCard',
    'crédito à vista visa': 'Crédito Visa',
    'crédito à vista american express': 'Crédito Amex',
    'débito elo': 'Débito Elo',
    'débito mastercard': 'Débito MasterCard',
    'débito visa': 'Débito Visa',
    'pix': 'PIX'
}

# --- FUNÇÕES UTILITÁRIAS ---
def format_currency(value):
    """Formata um valor como moeda brasileira."""
    if pd.isna(value) or value is None:
        return "R$ -"
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def init_data_file():
    """Inicializa o arquivo de dados se não existir."""
    if not os.path.exists(CONFIG["excel_file"]):
        pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix']).to_excel(
            CONFIG["excel_file"], index=False)

def load_data():
    """Carrega os dados do arquivo Excel."""
    try:
        if os.path.exists(CONFIG["excel_file"]):
            df = pd.read_excel(CONFIG["excel_file"])
            if not df.empty:
                df['Data'] = pd.to_datetime(df['Data'])
                return df.sort_values('Data', ascending=False)
        return pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])

def save_data(df):
    """Salva os dados no arquivo Excel."""
    try:
        df['Data'] = pd.to_datetime(df['Data'])
        df.to_excel(CONFIG["excel_file"], index=False)
        st.success("Dados salvos com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")

def round_to_50_or_00(value):
    """Arredonda para o múltiplo de 0.50 mais próximo."""
    return round(value * 2) / 2

def calculate_combination_value(combination, item_prices):
    """Calcula o valor total de uma combinação."""
    return sum(item_prices.get(name, 0) * quantity for name, quantity in combination.items())

def generate_initial_combination(item_prices, combination_size):
    """Gera uma combinação inicial aleatória."""
    if not item_prices:
        return {}
    
    items = list(item_prices.keys())
    size = min(combination_size, len(items))
    return {
        name: round_to_50_or_00(random.uniform(1, 10))
        for name in random.sample(items, size)
    }

def optimize_combination(item_prices, target_value, combination_size, max_iterations):
    """Otimiza combinações de produtos para atingir um valor alvo."""
    if not item_prices or target_value <= 0:
        return {}
    best_combination = generate_initial_combination(item_prices, combination_size)
    best_diff = abs(target_value - calculate_combination_value(best_combination, item_prices))
    best_diff += 10000 if calculate_combination_value(best_combination, item_prices) > target_value else 0
    
    # Corrigindo o bug no for loop (loop * substituído por correto)
    for _ in range(max_iterations):
        if not best_combination:
            break
        neighbor = best_combination.copy()
        item = random.choice(list(best_combination.keys()))
        change = random.choice([-0.50, 0.50, -1.00, 1.00])
        
        neighbor[item] = max(0.50, round_to_50_or_00(neighbor[item] + change))
        neighbor_value = calculate_combination_value(neighbor, item_prices)
        neighbor_diff = abs(target_value - neighbor_value)
        neighbor_diff += 10000 if neighbor_value > target_value else 0
        if neighbor_diff < best_diff:
            best_diff = neighbor_diff
            best_combination = neighbor
    return best_combination

def create_altair_chart(data, chart_type, x_col, y_col, color_col=None, title=None, interactive=True):
    """Cria gráficos Altair com configuração padronizada."""
    if chart_type == 'line':
        chart = alt.Chart(data).mark_line(point=True).encode(
            x=alt.X(f'{x_col}:T', title=x_col),
            y=alt.Y(f'{y_col}:Q', title=y_col),
            tooltip=[x_col, y_col]
        )
    elif chart_type == 'bar':
        chart = alt.Chart(data).mark_bar().encode(
            x=alt.X(f'{x_col}:N', title=x_col),
            y=alt.Y(f'{y_col}:Q', title=y_col),
            color=alt.Color(f'{color_col}:N') if color_col else alt.value('steelblue'),
            tooltip=[x_col, y_col]
        )
    elif chart_type == 'pie':
        chart = alt.Chart(data).mark_arc().encode(
            theta=alt.Theta(f'{y_col}:Q', stack=True),
            color=alt.Color(f'{x_col}:N', legend=alt.Legend(title=x_col)),
            tooltip=[x_col, y_col]
        )
    
    chart = chart.properties(
        title=title if title else f'{y_col} por {x_col}',
        width=700,
        height=400
    )
    
    return chart.interactive() if interactive else chart

# --- FUNÇÃO PARA CRIAR PDF ---
def create_pdf_report(vendas_data, total_vendas, imposto_simples, custo_funcionario, custo_contadora, total_custos, lucro_estimado):
    """Cria um relatório em PDF dos dados de vendas"""
    buffer = BytesIO()
    
    # Configuração do documento
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Adicionando título
    title_style = styles["Heading1"]
    title_style.alignment = 1  # Centralizado
    elements.append(Paragraph("Clip's Burger - Relatório de Vendas", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Data do relatório
    date_style = styles["Normal"]
    date_style.alignment = 1
    elements.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Resumo financeiro
    elements.append(Paragraph("Resumo Financeiro", styles["Heading2"]))
    
    # Tabela de resumo financeiro
    financial_data = [
        ["Descrição", "Valor"],
        ["Faturamento Bruto", format_currency(total_vendas)],
        ["Imposto Simples (6%)", format_currency(imposto_simples)],
        ["Custo Funcionário CLT", format_currency(custo_funcionario)],
        ["Custo Contadora", format_currency(custo_contadora)],
        ["Total de Custos", format_currency(total_custos)],
        ["Lucro Estimado", format_currency(lucro_estimado)]
    ]
    
    financial_table = Table(financial_data, colWidths=[4*inch, 2*inch])
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, -1), (1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
    ]))
    elements.append(financial_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Detalhe das vendas por forma de pagamento
    elements.append(Paragraph("Vendas por Forma de Pagamento", styles["Heading2"]))
    payment_data = [["Forma de Pagamento", "Valor"]]
    
    for _, row in vendas_data.iterrows():
        payment_data.append([row['Forma'], format_currency(row['Valor'])])
    
    payment_table = Table(payment_data, colWidths=[4*inch, 2*inch])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
    ]))
    elements.append(payment_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Explicação dos cálculos
    elements.append(Paragraph("Explicação dos Cálculos", styles["Heading2"]))
    calc_style = styles["BodyText"]
    elements.append(Paragraph("1. Imposto Simples Nacional: 6% do faturamento bruto", calc_style))
    elements.append(Paragraph("2. Custo Funcionário CLT: Salário + FGTS (8%) + Férias (1/12) + 13º (1/12)", calc_style))
    elements.append(Paragraph("3. Total de Custos: Impostos + Funcionário + Contadora", calc_style))
    elements.append(Paragraph("4. Lucro Estimado: Faturamento Bruto - Total de Custos", calc_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Gráfico de composição de custos (usando matplotlib)
    elements.append(Paragraph("Composição dos Custos", styles["Heading2"]))
    
    # Criar gráfico matplotlib
    fig, ax = plt.figure(figsize=(7, 5)), plt.axes()
    custos = [imposto_simples, custo_funcionario, custo_contadora]
    labels = ['Impostos', 'Funcionário', 'Contadora']
    ax.pie(custos, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.title('Distribuição dos Custos')
    
    # Salvar em buffer temporário
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.close()
    
    # Adicionar imagem
    img = Image(img_buffer, width=6*inch, height=4*inch)
    elements.append(img)
    
    # Gráfico de barras para formas de pagamento
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Vendas por Forma de Pagamento", styles["Heading2"]))
    
    # Criar gráfico de barras
    fig, ax = plt.figure(figsize=(7, 5)), plt.axes()
    formas = vendas_data['Forma'].tolist()
    valores = vendas_data['Valor'].tolist()
    ax.bar(formas, valores)
    ax.set_ylabel('Valor (R$)')
    ax.set_title('Vendas por Forma de Pagamento')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Salvar em buffer temporário
    img_buffer2 = BytesIO()
    plt.savefig(img_buffer2, format='png')
    img_buffer2.seek(0)
    plt.close()
    
    # Adicionar imagem
    img2 = Image(img_buffer2, width=6*inch, height=4*inch)
    elements.append(img2)
    
    # Rodapé
    elements.append(Spacer(1, 1*inch))
    footer = Paragraph("© 2025 Clips Burger - Sistema de Gestão", styles["Normal"])
    elements.append(footer)
    
    # Construir o PDF
    doc.build(elements)
    
    # Retornar o PDF como base64 para download
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title=CONFIG["page_title"],
    layout=CONFIG["layout"],
    initial_sidebar_state=CONFIG["sidebar_state"]
)

# --- INICIALIZAÇÃO ---
init_data_file()
if 'df_receipts' not in st.session_state:
    st.session_state.df_receipts = load_data()
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'vendas_data' not in st.session_state:
    st.session_state.vendas_data = None

# --- INTERFACE PRINCIPAL ---
col_title1, col_title2 = st.columns([0.30, 0.70])
with col_title1:
    try:
        st.image(CONFIG["logo_path"], width=1000)
    except FileNotFoundError:
        st.warning("Logo não encontrada")
with col_title2:
    st.title("Sistema de Gestão")
    st.markdown("<p style='font-weight:bold; font-size:30px; margin-top:-15px'>Clip's Burger</p>", 
               unsafe_allow_html=True)
st.markdown("""
Bem-vindo(a)! Esta ferramenta ajuda a visualizar suas vendas por forma de pagamento
e tenta encontrar combinações *hipotéticas* de produtos que poderiam corresponder a esses totais.
""")
st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurações")
    drink_percentage = st.slider(
        "Percentual para Bebidas (%) 🍹",
        min_value=0, max_value=100, value=20, step=5
    )
    st.caption(f"({100 - drink_percentage}% será alocado para Sanduíches 🍔)")
    tamanho_combinacao_bebidas = st.slider(
        "Número de tipos de Bebidas", 1, 10, 5, 1)
    tamanho_combinacao_sanduiches = st.slider(
        "Número de tipos de Sanduíches", 1, 10, 5, 1)
    max_iterations = st.select_slider(
        "Qualidade da Otimização ✨",
        options=[1000, 5000, 10000, 20000, 50000],
        value=10000
    )
    st.info("Lembre-se: As combinações são aproximações heurísticas.")

# --- ABAS PRINCIPAIS ---
tab1, tab2, tab3 = st.tabs(["📈 Resumo das Vendas", "🧩 Detalhes das Combinações", "💰 Cadastro de Recebimentos"])

with tab1:
    # Seção de upload de arquivo
    st.header("📤 Upload de Dados")
    arquivo = st.file_uploader("Envie o arquivo de transações (.csv ou .xlsx)", 
                             type=["csv", "xlsx"])
    
    if arquivo:
        try:
            # Processamento do arquivo
            with st.spinner("Processando arquivo..."):
                # Verificar o tipo de arquivo
                if arquivo.name.endswith(".csv"):
                    try:
                        df = pd.read_csv(arquivo, sep=';', encoding='utf-8', dtype=str)
                    except pd.errors.ParserError:
                        arquivo.seek(0)
                        try:
                            df = pd.read_csv(arquivo, sep=',', encoding='utf-8', dtype=str)
                        except:
                            arquivo.seek(0)
                            df = pd.read_csv(arquivo, engine='python', dtype=str)
                else:
                    df = pd.read_excel(arquivo, dtype=str)
                
                # Verificar colunas obrigatórias
                required_cols = ['Tipo', 'Bandeira', 'Valor']
                if not all(col in df.columns for col in required_cols):
                    st.error(f"Erro: O arquivo precisa conter as colunas: {', '.join(required_cols)}")
                    st.stop()
                # Processamento dos dados
                df['Tipo'] = df['Tipo'].str.lower().str.strip().fillna('desconhecido')
                df['Bandeira'] = df['Bandeira'].str.lower().str.strip().fillna('desconhecida')
                df['Valor'] = pd.to_numeric(
                    df['Valor'].str.replace('.', '').str.replace(',', '.'), 
                    errors='coerce')
                df = df.dropna(subset=['Valor'])
                
                df['Forma'] = (df['Tipo'] + ' ' + df['Bandeira']).map(FORMAS_PAGAMENTO)
                df = df.dropna(subset=['Forma'])
                
                if df.empty:
                    st.warning("Nenhuma transação válida encontrada.")
                    st.stop()
                vendas = df.groupby('Forma')['Valor'].sum().reset_index()
                total_vendas = vendas['Valor'].sum()
                
                # Salva os dados no session state
                st.session_state.uploaded_data = df
                st.session_state.vendas_data = vendas
                st.session_state.total_vendas = total_vendas
            
            # Seção de Visualização de Dados
            st.header("📊 Visualização de Dados")
            
            # Gráfico de Barras
            st.subheader("Total de Vendas por Forma de Pagamento")
            bar_chart = create_altair_chart(
                vendas, 'bar', 'Forma', 'Valor', 'Forma',
                title=''
            ).properties(
                width=800,
                height=500
            )
            st.altair_chart(bar_chart, use_container_width=True)
            
            # Seção de Parâmetros Financeiros
            st.header("⚙️ Parâmetros Financeiros")
            col1, col2 = st.columns(2)
            with col1:
                salario_minimo = st.number_input("Salário Mínimo (R$)", value=1518.0, step=50.0)
            with col2:
                custo_contadora = st.number_input("Custo com Contadora (R$)", value=316.0, step=10.0)
            
            # Seção de Resultados
            st.header("💰 Resultados Financeiros")
            
            # Métricas Principais
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Faturamento Bruto", format_currency(total_vendas))
            with col2:
                imposto_simples = total_vendas * 0.06
                st.metric("Imposto Simples (6%)", format_currency(imposto_simples))
            with col3:
                fgts = salario_minimo * 0.08
                ferias = (salario_minimo / 12) * (4/3)
                decimo_terceiro = salario_minimo / 12
                custo_funcionario = salario_minimo + fgts + ferias + decimo_terceiro
                st.metric("Custo Funcionário CLT", format_currency(custo_funcionario))
            
            # Cálculo do Total de Custos
            total_custos = imposto_simples + custo_funcionario + custo_contadora
            lucro_estimado = total_vendas - total_custos
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total de Custos", format_currency(total_custos))
            with col2:
                st.metric("Lucro Estimado", format_currency(lucro_estimado))
            
            # Seção de Detalhamento
            st.header("🔍 Detalhamento")
            
            tab_detalhes1, tab_detalhes2, tab_detalhes3 = st.tabs([
                "📝 Composição de Custos", 
                "📚 Explicação dos Cálculos",
                "🍰 Gráfico de Composição"
            ])
            
            with tab_detalhes1:
                st.subheader("Composição dos Custos")
                st.markdown(f"""
                - **Imposto Simples Nacional (6%)**: {format_currency(imposto_simples)}
                - **Custo Funcionário CLT**: {format_currency(custo_funcionario)}
                - **Custo Contadora**: {format_currency(custo_contadora)}
                """)
            
            with tab_detalhes2:
                st.subheader("Fórmulas Utilizadas")
                st.markdown("""
                **1. Imposto Simples Nacional**  
                `Faturamento Bruto × 6%`  
                
                **2. Custo Funcionário CLT**  
                `Salário + FGTS (8%) + Férias (1 mês + 1/3) + 13º Salário`  
                
                **3. Total de Custos**  
                `Imposto + Funcionário + Contadora`  
                
                **4. Lucro Estimado**  
                `Faturamento Bruto - Total de Custos`
                """)
            
            with tab_detalhes3:
                st.subheader("Composição dos Custos")
                custos_df = pd.DataFrame({
                    'Item': ['Impostos', 'Funcionário', 'Contadora'],
                    'Valor': [imposto_simples, custo_funcionario, custo_contadora]
                })
                
                graf_composicao = alt.Chart(custos_df).mark_arc().encode(
                    theta='Valor',
                    color='Item',
                    tooltip=['Item', alt.Tooltip('Valor', format='$.2f')]
                ).properties(
                    width=600,
                    height=500
                )
                
                st.altair_chart(graf_composicao, use_container_width=True)
            
            # NOVA SEÇÃO: Gerador de PDF
            st.header("📄 Gerar Relatório em PDF")
            st.write("Gere um relatório completo com os dados analisados acima.")
            
            if st.button("🔄 Gerar PDF"):
                with st.spinner("Gerando relatório em PDF..."):
                    pdf_data = create_pdf_report(
                        vendas,
                        total_vendas,
                        imposto_simples,
                        custo_funcionario,
                        custo_contadora,
                        total_custos,
                        lucro_estimado
                    )
                    
                    # Cria link para download
                    href = f'<a href="data:application/pdf;base64,{pdf_data}" download="relatorio_clips_burger.pdf">📥 Clique aqui para baixar o relatório em PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success("Relatório gerado com sucesso!")
            
        except Exception as e:
            st.error(f"Erro no processamento: {str(e)}")
    else:
        st.info("Por favor, envie um arquivo de transações para análise.")

with tab2:
    st.header("🧩 Detalhes das Combinações Geradas")
    
    if st.session_state.vendas_data is None:
        st.warning("Por favor, carregue os dados de vendas na aba 'Resumo das Vendas' primeiro.")
        st.stop()
    
    vendas = st.session_state.vendas_data
    sandwich_percentage = 100 - drink_percentage
    st.caption(f"Alocação: {drink_percentage}% bebidas | {sandwich_percentage}% sanduíches")

    bebidas_precos = CARDAPIOS['bebidas']
    sanduiches_precos = CARDAPIOS['sanduiches']
    
    ordem_formas = [
        'Débito Visa', 'Débito MasterCard', 'Débito Elo',
        'Crédito Visa', 'Crédito MasterCard', 'Crédito Elo',
        'Crédito Amex', 'PIX'
    ]
    
    for forma in ordem_formas:
        if forma not in vendas['Forma'].values:
            continue
            
        total_pagamento = vendas.loc[vendas['Forma'] == forma, 'Valor'].values[0]
        if total_pagamento <= 0:
            continue

        with st.expander(f"**{forma}** (Total: {format_currency(total_pagamento)})", expanded=False):
            target_bebidas = round_to_50_or_00(total_pagamento * (drink_percentage / 100.0))
            target_sanduiches = round_to_50_or_00(total_pagamento - target_bebidas)

            comb_bebidas = optimize_combination(
                bebidas_precos, target_bebidas, tamanho_combinacao_bebidas, max_iterations
            )
            comb_sanduiches = optimize_combination(
                sanduiches_precos, target_sanduiches, tamanho_combinacao_sanduiches, max_iterations
            )

            comb_bebidas_rounded = {k: round(v) for k, v in comb_bebidas.items() if round(v) > 0}
            comb_sanduiches_rounded = {k: round(v) for k, v in comb_sanduiches.items() if round(v) > 0}

            total_bebidas = calculate_combination_value(comb_bebidas_rounded, bebidas_precos)
            total_sanduiches = calculate_combination_value(comb_sanduiches_rounded, sanduiches_precos)
            total_geral = total_bebidas + total_sanduiches

            col1, col2 = st.columns(2)

            with col1:
                st.subheader(f"🍹 Bebidas: {format_currency(target_bebidas)}")
                if comb_bebidas_rounded:
                    for nome, qtd in comb_bebidas_rounded.items():
                        val = bebidas_precos[nome] * qtd
                        st.markdown(f"- **{qtd}** {nome}: {format_currency(val)}")
                    st.divider()
                    st.metric("Total Bebidas", format_currency(total_bebidas))
                else:
                    st.info("Nenhuma bebida na combinação")

            with col2:
                st.subheader(f"🍔 Sanduíches: {format_currency(target_sanduiches)}")
                if comb_sanduiches_rounded:
                    for nome, qtd in comb_sanduiches_rounded.items():
                        val = sanduiches_precos[nome] * qtd
                        st.markdown(f"- **{qtd}** {nome}: {format_currency(val)}")
                    st.divider()
                    st.metric("Total Sanduíches", format_currency(total_sanduiches))
                else:
                    st.info("Nenhum sanduíche na combinação")

            st.divider()
            diff = total_geral - total_pagamento
            st.metric(
                "💰 TOTAL GERAL",
                format_currency(total_geral),
                delta=f"{format_currency(abs(diff))} {'a menos' if diff < 0 else 'a mais'} que o total",
                delta_color="normal" if diff <= 0 else "inverse"
            )

with tab3:
    st.header("💰 Cadastro e Análise de Recebimentos")
    
    # Seção 1: Formulário para adicionar novos dados
    with st.expander("➕ Adicionar Novo Registro", expanded=True):
        with st.form("add_receipt_form"):
            cols = st.columns([1, 1, 1, 1])
            with cols[0]:
                data = st.date_input("Data*", value=datetime.now())
            
            st.write("**Valores por Forma de Pagamento**")
            cols = st.columns(3)
            with cols[0]:
                dinheiro = st.number_input("Dinheiro (R$)*", min_value=0.0, step=10.0)
            with cols[1]:
                cartao = st.number_input("Cartão (R$)*", min_value=0.0, step=10.0)
            with cols[2]:
                pix = st.number_input("PIX (R$)*", min_value=0.0, step=10.0)
            
            total_dia = dinheiro + cartao + pix
            st.metric("Total do Dia", format_currency(total_dia))
            
            submitted = st.form_submit_button("✅ Salvar Registro")
            
            if submitted:
                if total_dia <= 0:
                    st.error("O total do dia deve ser maior que zero!")
                else:
                    try:
                        new_record = pd.DataFrame({
                            'Data': [data],
                            'Dinheiro': [dinheiro],
                            'Cartao': [cartao],
                            'Pix': [pix]
                        })
                        st.session_state.df_receipts = pd.concat(
                            [st.session_state.df_receipts, new_record], 
                            ignore_index=True
                        )
                        save_data(st.session_state.df_receipts)
                        st.success("Registro salvo com sucesso!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {str(e)}")

    # Seção 2: Visualização dos dados e gráficos
    if not st.session_state.df_receipts.empty:
        # Filtros de data
        st.subheader("📅 Filtros de Período")
        
        # Opções de filtro
        filtro_tipo = st.radio("Tipo de Filtro:", 
                             ["Intervalo de Datas", "Mês Específico"], 
                             horizontal=True)
        
        if filtro_tipo == "Intervalo de Datas":
            cols = st.columns(2)
            with cols[0]:
                inicio = st.date_input("Data inicial", 
                                     value=st.session_state.df_receipts['Data'].min())
            with cols[1]:
                fim = st.date_input("Data final", 
                                  value=st.session_state.df_receipts['Data'].max())
        else:
            # Filtro por mês
            meses_disponiveis = sorted(st.session_state.df_receipts['Data'].dt.to_period('M').unique(), reverse=True)
            mes_selecionado = st.selectbox("Selecione o mês:", 
                                         options=meses_disponiveis,
                                         format_func=lambda x: x.strftime('%B/%Y'))
            
            inicio = pd.to_datetime(mes_selecionado.start_time)
            fim = pd.to_datetime(mes_selecionado.end_time)
        
        # Aplica filtros
        df_filtered = st.session_state.df_receipts[
            (st.session_state.df_receipts['Data'] >= pd.to_datetime(inicio)) & 
            (st.session_state.df_receipts['Data'] <= pd.to_datetime(fim))
        ].copy()
        
        if not df_filtered.empty:
            # Adiciona coluna de Total
            df_filtered['Total'] = df_filtered['Dinheiro'] + df_filtered['Cartao'] + df_filtered['Pix']
            
            # Calcula totais por forma de pagamento
            totais = {
                'Dinheiro': df_filtered['Dinheiro'].sum(),
                'Cartão': df_filtered['Cartao'].sum(),
                'PIX': df_filtered['Pix'].sum()
            }
            total_periodo = sum(totais.values())
            
            # Seção 3: Métricas Resumo
            st.subheader("📊 Resumo do Período")
            
            # CSS para ajustar o tamanho das métricas
            st.markdown("""
            <style>
                div[data-testid="stMetric"] {
                    padding: 5px 10px;
                }
                div[data-testid="stMetric"] > div {
                    gap: 2px;
                }
                div[data-testid="stMetric"] label {
                    font-size: 14px !important;
                    font-weight: 500 !important;
                    color: #6b7280 !important;
                }
                div[data-testid="stMetric"] > div > div {
                    font-size: 18px !important;
                    font-weight: 600 !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            # Layout compacto em 2 linhas de 4 colunas
            cols1 = st.columns(4)
            cols2 = st.columns(4)
            
            with cols1[0]:
                st.metric("Dinheiro", format_currency(totais['Dinheiro']), 
                         help="Total em recebimentos de dinheiro")
            with cols1[1]:
                st.metric("Cartão", format_currency(totais['Cartão']),
                         help="Total em recebimentos por cartão")
            with cols1[2]:
                st.metric("PIX", format_currency(totais['PIX']),
                         help="Total em recebimentos por PIX")
            with cols1[3]:
                st.metric("Total Geral", format_currency(total_periodo),
                         help="Soma de todas as formas de pagamento")
            
            with cols2[0]:
                st.metric("Média Diária", format_currency(df_filtered['Total'].mean()),
                         help="Média de vendas por dia")
            with cols2[1]:
                st.metric("Maior Venda", format_currency(df_filtered['Total'].max()),
                         help=f"Dia: {df_filtered.loc[df_filtered['Total'].idxmax(), 'Data'].strftime('%d/%m')}")
            with cols2[2]:
                st.metric("Dias Registrados", len(df_filtered),
                         help="Total de dias com vendas registradas")
            with cols2[3]:
                st.metric("Dias sem Registro", (fim - inicio).days + 1 - len(df_filtered),
                         help="Dias do período sem vendas registradas")
            
            # Seção 4: Gráficos
            st.subheader("📈 Visualizações Gráficas")
            
            tab_graficos1, tab_graficos2, tab_graficos3 = st.tabs(["Distribuição", "Comparação", "Acumulado"])
            
            with tab_graficos1:
                # Gráfico de Pizza
                df_pie = pd.DataFrame({
                    'Forma': list(totais.keys()),
                    'Valor': list(totais.values())
                })
                
                pie_chart = alt.Chart(df_pie).mark_arc().encode(
                    theta='Valor',
                    color=alt.Color('Forma', legend=alt.Legend(title="Forma de Pagamento")),
                    tooltip=['Forma', 'Valor']
                ).properties(
                    height=400,
                    title='Distribuição dos Recebimentos'
                )
                st.altair_chart(pie_chart, use_container_width=True)
            
            with tab_graficos2:
                # Gráfico de Barras
                df_bar = df_filtered.melt(id_vars=['Data'], 
                                        value_vars=['Dinheiro', 'Cartao', 'Pix'],
                                        var_name='Forma', 
                                        value_name='Valor')
                
                bar_chart = alt.Chart(df_bar).mark_bar().encode(
                    x='monthdate(Data):O',
                    y='sum(Valor):Q',
                    color='Forma',
                    tooltip=['Forma', 'sum(Valor)']
                ).properties(
                    height=400,
                    title='Vendas por Forma de Pagamento'
                )
                st.altair_chart(bar_chart, use_container_width=True)
            
            with tab_graficos3:
                # Gráfico Acumulado
                df_acumulado = df_filtered.sort_values('Data').copy()
                df_acumulado['Acumulado'] = df_acumulado['Total'].cumsum()
                
                line_chart = alt.Chart(df_acumulado).mark_line(
                    point=True,
                    strokeWidth=3,
                    color='red'
                ).encode(
                    x='Data:T',
                    y='Acumulado:Q',
                    tooltip=['Data', 'Acumulado']
                ).properties(
                    height=400,
                    title='Receita Total Acumulada'
                )
                
                st.altair_chart(line_chart, use_container_width=True)
            
            # Seção 5: Tabela de Dados
            st.subheader("📋 Dados Detalhados")
            st.dataframe(
                df_filtered.sort_values('Data', ascending=False).style.format({
                    'Dinheiro': lambda x: format_currency(x),
                    'Cartao': lambda x: format_currency(x),
                    'Pix': lambda x: format_currency(x),
                    'Total': lambda x: format_currency(x)
                }),
                use_container_width=True,
                height=400
            )
            
        else:
            st.warning("Nenhum registro encontrado no período selecionado")
    else:
        st.info("Nenhum dado cadastrado ainda. Adicione seu primeiro registro acima.")

# Adicionar rodapé
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: small;'>
        © 2025 Clips Burger - Sistema de Gestão | Desenvolvido com ❤️ e Streamlit
    </div>
    """, 
    unsafe_allow_html=True
)
