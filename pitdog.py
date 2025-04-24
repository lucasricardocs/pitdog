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
    st.header("💰 Cadastro e Análise de Recebimentos Diários")
    
    # Seção 1: Formulário de cadastro manual
    with st.expander("➕ Adicionar Novo Registro de Caixa", expanded=True):
        with st.form("novo_recebimento_form"):
            cols = st.columns([1, 1, 1, 1])
            with cols[0]:
                data = st.date_input("Data da Operação*", value=datetime.now())
            
            st.markdown("**Valores Recebidos por Forma de Pagamento**")
            cols = st.columns(3)
            with cols[0]:
                dinheiro = st.number_input("Dinheiro (R$)*", 
                                        min_value=0.0, 
                                        step=50.0,
                                        help="Valores recebidos em espécie")
            with cols[1]:
                cartao = st.number_input("Cartão (R$)*", 
                                       min_value=0.0, 
                                       step=50.0,
                                       help="Somatório de todas as transações com cartão")
            with cols[2]:
                pix = st.number_input("PIX (R$)*", 
                                     min_value=0.0, 
                                     step=50.0,
                                     help="Transações realizadas via PIX")
            
            total_dia = dinheiro + cartao + pix
            st.markdown(f"**Total do Dia:** {format_currency(total_dia)}")
            
            submitted = st.form_submit_button("💾 Salvar Registro")
            
            if submitted:
                if total_dia <= 0:
                    st.error("❌ O total do dia deve ser maior que zero!")
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
                        st.success("✅ Registro salvo com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Erro crítico: {str(e)}")

    # Seção 2: Visualização de dados históricos
    if not st.session_state.df_receipts.empty:
        st.divider()
        
        # Filtros temporais
        st.subheader("🔍 Filtros de Período")
        filtro_tipo = st.radio("Selecione o tipo de filtro:", 
                             ["Intervalo Livre", "Análise Mensal"], 
                             horizontal=True,
                             index=0)
        
        df = st.session_state.df_receipts.copy()
        df['Data'] = pd.to_datetime(df['Data'])
        df['Mês/Ano'] = df['Data'].dt.strftime('%Y-%m')
        
        if filtro_tipo == "Intervalo Livre":
            cols = st.columns(2)
            with cols[0]:
                start_date = st.date_input("Data inicial", 
                                         value=df['Data'].min(),
                                         min_value=df['Data'].min(),
                                         max_value=df['Data'].max())
            with cols[1]:
                end_date = st.date_input("Data final", 
                                      value=df['Data'].max(),
                                      min_value=df['Data'].min(),
                                      max_value=df['Data'].max())
        else:
            meses = df['Mês/Ano'].unique()
            mes_selecionado = st.selectbox("Selecione o mês:", 
                                         sorted(meses, reverse=True),
                                         format_func=lambda x: pd.to_datetime(x).strftime('%B/%Y'))
            start_date = pd.to_datetime(mes_selecionado)
            end_date = start_date + pd.offsets.MonthEnd(1)
        
        # Aplicar filtros
        mask = (df['Data'] >= pd.to_datetime(start_date)) & (df['Data'] <= pd.to_datetime(end_date))
        df_filtrado = df.loc[mask]
        df_filtrado['Total'] = df_filtrado['Dinheiro'] + df_filtrado['Cartao'] + df_filtrado['Pix']
        
        if not df_filtrado.empty:
            # Métricas-chave
            st.subheader("📊 Indicadores Financeiros")
            
            cols = st.columns(4)
            metric_style = """
            <style>
                div[data-testid="stMetric"] {
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 15px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                div[data-testid="stMetricLabel"] {
                    color: #6c757d;
                    font-size: 0.9rem !important;
                }
                div[data-testid="stMetricValue"] {
                    color: #2c3e50;
                    font-size: 1.4rem !important;
                    font-weight: 700 !important;
                }
            </style>
            """
            st.markdown(metric_style, unsafe_allow_html=True)
            
            with cols[0]:
                st.metric("Total em Dinheiro", format_currency(df_filtrado['Dinheiro'].sum()))
            with cols[1]:
                st.metric("Total em Cartão", format_currency(df_filtrado['Cartao'].sum()))
            with cols[2]:
                st.metric("Total em PIX", format_currency(df_filtrado['Pix'].sum()))
            with cols[3]:
                st.metric("Receita Total", 
                        format_currency(df_filtrado['Total'].sum()),
                        delta=format_currency(df_filtrado['Total'].sum() - df_filtrado['Total'].mean()),
                        delta_color="normal")

            # Visualizações gráficas
            st.subheader("📈 Análise Visual")
            
            tab1, tab2, tab3 = st.tabs(["Distribuição", "Evolução Temporal", "Comparativo Mensal"])
            
            with tab1:
                # Gráfico de pizza interativo
                source = pd.DataFrame({
                    'Forma de Pagamento': ['Dinheiro', 'Cartão', 'PIX'],
                    'Valor': [
                        df_filtrado['Dinheiro'].sum(),
                        df_filtrado['Cartao'].sum(),
                        df_filtrado['Pix'].sum()
                    ]
                })
                
                pie = alt.Chart(source).mark_arc().encode(
                    theta='Valor:Q',
                    color=alt.Color('Forma de Pagamento:N', legend=alt.Legend(title="Forma de Pagamento")),
                    tooltip=['Forma de Pagamento', 'Valor']
                ).properties(
                    width=600,
                    height=400,
                    title='Distribuição Percentual das Formas de Pagamento'
                )
                
                st.altair_chart(pie, use_container_width=True)
            
            with tab2:
                # Gráfico de linhas temporal
                line_chart = alt.Chart(df_filtrado).mark_line(point=True).encode(
                    x=alt.X('yearmonthdate(Data):T', title='Data'),
                    y=alt.Y('Total:Q', title='Valor (R$)'),
                    color=alt.value('#2ecc71'),
                    tooltip=['Data', 'Dinheiro', 'Cartao', 'Pix', 'Total']
                ).properties(
                    width=800,
                    height=400,
                    title='Evolução Diária da Receita'
                )
                
                st.altair_chart(line_chart, use_container_width=True)
            
            with tab3:
                # Gráfico de barras comparativo mensal
                if filtro_tipo == "Intervalo Livre":
                    df_mensal = df_filtrado.resample('M', on='Data').sum().reset_index()
                    bar_chart = alt.Chart(df_mensal).mark_bar().encode(
                        x=alt.X('yearmonth(Data):O', title='Mês'),
                        y=alt.Y('Total:Q', title='Receita Total'),
                        color=alt.Color('Total:Q', scale=alt.Scale(scheme='greens')),
                        tooltip=['yearmonth(Data)', 'Total']
                    ).properties(
                        width=800,
                        height=400,
                        title='Comparativo Mensal de Receitas'
                    )
                    st.altair_chart(bar_chart, use_container_width=True)
                else:
                    st.info("Selecione 'Intervalo Livre' para comparação entre meses")

            # Tabela detalhada
            st.subheader("📋 Detalhamento dos Registros")
            
            df_exibicao = df_filtrado.sort_values('Data', ascending=False).copy()
            df_exibicao['Data'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
            
            st.dataframe(
                df_exibicao.style
                    .format({
                        'Dinheiro': lambda x: format_currency(x),
                        'Cartao': lambda x: format_currency(x),
                        'Pix': lambda x: format_currency(x),
                        'Total': lambda x: format_currency(x)
                    })
                    .applymap(lambda x: 'color: #27ae60' if isinstance(x, (int, float)) and x > 0 else ''),
                column_config={
                    "Dinheiro": "Dinheiro (R$)",
                    "Cartao": "Cartão (R$)",
                    "Pix": "PIX (R$)",
                    "Total": "Total do Dia"
                },
                use_container_width=True,
                height=400
            )
            
            # Opção de exportação
            st.download_button(
                label="⬇️ Exportar Dados Filtrados (CSV)",
                data=df_filtrado.to_csv(index=False).encode('utf-8'),
                file_name=f'recebimentos_{start_date}_{end_date}.csv',
                mime='text/csv'
            )
            
        else:
            st.warning("⚠️ Nenhum registro encontrado no período selecionado")
    else:
        st.info("ℹ️ Nenhum dado cadastrado ainda. Utilize o formulário acima para adicionar seu primeiro registro.")

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
