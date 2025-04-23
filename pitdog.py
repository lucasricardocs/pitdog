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
    st.session_state['df_receipts'] = load_data()

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
    st.header("📈 Resumo das Vendas")
    arquivo = st.file_uploader("📤 Envie o arquivo de transações (.csv ou .xlsx)", 
                             type=["csv", "xlsx"])

    if arquivo:
        try:
            # Verificar o tipo de arquivo
            if arquivo.name.endswith(".csv"):
                # Tentar ler com diferentes delimitadores
                try:
                    df = pd.read_csv(arquivo, sep=';', encoding='utf-8', dtype=str)
                except pd.errors.ParserError:
                    arquivo.seek(0)  # Resetar o ponteiro do arquivo
                    try:
                        df = pd.read_csv(arquivo, sep=',', encoding='utf-8', dtype=str)
                    except:
                        arquivo.seek(0)
                        # Tentar ler automaticamente se ainda falhar
                        df = pd.read_csv(arquivo, engine='python', dtype=str)
            else:
                df = pd.read_excel(arquivo, dtype=str)
            
            # Verificar colunas obrigatórias
            required_cols = ['Tipo', 'Bandeira', 'Valor']
            if not all(col in df.columns for col in required_cols):
                st.error(f"Erro: O arquivo precisa conter as colunas: {', '.join(required_cols)}")
                st.stop()

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
            
            # Gráfico de Barras
            bar_chart = create_altair_chart(
                vendas, 'bar', 'Forma', 'Valor', 'Forma',
                title='Total de Vendas por Forma de Pagamento'
            )
            st.altair_chart(bar_chart, use_container_width=True)
            
            # Resumo Financeiro
            # --- DENTRO DA TAB1, NA SEÇÃO DE RESUMO FINANCEIRO ---

    st.subheader("💰 Resumo Financeiro")
    
    # Inputs básicos
    salario_minimo = st.number_input("💼 Salário Mínimo (R$)", value=1518.0, step=50.0)
    custo_contadora = st.number_input("📋 Custo com Contadora (R$)", value=316.0, step=10.0)
    
    # Cálculos (agora com variáveis explicativas)
    with st.expander("🔍 Detalhamento dos Cálculos", expanded=False):
        st.markdown("""
        **Fórmulas Utilizadas:**
        
        1. **Imposto Simples Nacional** = Faturamento Bruto × 6%
        2. **Custo Funcionário CLT** = Salário + FGTS + Férias + 13º
        3. **Total de Custos** = Imposto + Funcionário + Contadora
        4. **Lucro Estimado** = Faturamento Bruto - Total de Custos
        """)
    
    # Container principal para métricas
    col1, col2 = st.columns(2)
    
    with col1:
        # Faturamento Bruto
        st.metric("💵 Faturamento Bruto", format_currency(total_vendas))
        
        # Imposto Simples
        imposto_simples = total_vendas * 0.06
        with st.expander("📊 Simples Nacional (6%)", expanded=False):
            st.markdown(f"""
            - **Cálculo**: R$ {total_vendas:,.2f} × 6%  
            - **Valor**: {format_currency(imposto_simples)}
            """.replace(",", "X").replace(".", ",").replace("X", "."))
    
    with col2:
        # Custo Funcionário
        fgts = salario_minimo * 0.08
        ferias = (salario_minimo / 12) * (4/3)  # 1 mês + 1/3 constitucional
        decimo_terceiro = salario_minimo / 12
        custo_funcionario = salario_minimo + fgts + ferias + decimo_terceiro
        
        with st.expander("👷‍♂️ Custo Funcionário CLT", expanded=False):
            st.markdown(f"""
            - **Salário Bruto**: {format_currency(salario_minimo)}  
            - **FGTS (8%)**: {format_currency(fgts)}  
            - **Férias + 1/3**: {format_currency(ferias)}  
            - **13º Salário**: {format_currency(decimo_terceiro)}  
            - **Total**: {format_currency(custo_funcionario)}
            """)
        
        # Custo Contadora
        with st.expander("📋 Custo Contadora", expanded=False):
            st.markdown(f"Valor fixo mensal: {format_currency(custo_contadora)}")
    
    # Linha de totais
    st.divider()
    
    # Cálculo do total de custos (agora com explicação)
    total_custos = imposto_simples + custo_funcionario + custo_contadora
    with st.expander("🧮 TOTAL DE CUSTOS (Como Calculado)", expanded=True):
        st.markdown(f"""
        - **Imposto Simples**: {format_currency(imposto_simples)}  
        - **Custo Funcionário**: {format_currency(custo_funcionario)}  
        - **Custo Contadora**: {format_currency(custo_contadora)}  
        
        **Fórmula**:  
        `Imposto + Funcionário + Contadora = {format_currency(imposto_simples)} + {format_currency(custo_funcionario)} + {format_currency(custo_contadora)}`  
        
        **Total de Custos**: {format_currency(total_custos)}
        """)
    
    # Lucro Estimado
    lucro_estimado = total_vendas - total_custos
    with st.expander("💡 LUCRO ESTIMADO (Como Calculado)", expanded=True):
        st.markdown(f"""
        **Fórmula**:  
        `Faturamento Bruto - Total de Custos = {format_currency(total_vendas)} - {format_currency(total_custos)}`  
        
        **Lucro Estimado**: {format_currency(lucro_estimado)}  
        
        *Obs: Valores aproximados, não considerando outros custos operacionais*
        """)
    
    # Gráfico de composição (novo)
    custos_df = pd.DataFrame({
        'Item': ['Impostos', 'Funcionário', 'Contadora'],
        'Valor': [imposto_simples, custo_funcionario, custo_contadora]
    })
    
    graf_composicao = alt.Chart(custos_df).mark_arc().encode(
        theta='Valor',
        color='Item',
        tooltip=['Item', alt.Tooltip('Valor', format='$.2f')]
    ).properties(
        title='Composição dos Custos',
        width=400,
        height=400
    )
    
    st.altair_chart(graf_composicao, use_container_width=True)

        except Exception as e:
            st.error(f"Erro no processamento: {str(e)}")
    else:
        st.info("✨ Aguardando envio do arquivo de transações...")

# ... (o código anterior permanece igual até a definição das abas)

# --- ABAS PRINCIPAIS ---
tab1, tab2, tab3 = st.tabs(["📈 Resumo das Vendas", "🧩 Detalhes das Combinações", "💰 Cadastro de Recebimentos"])

with tab1:
    # ... (o conteúdo da Tab1 permanece igual)

with tab2:
    st.header("🧩 Detalhes das Combinações")
    
    if 'vendas' in locals() and vendas:  # Verifica se existem dados de vendas
        total_vendas = sum(vendas['Valor'])
        st.subheader(f"Total de Vendas: {format_currency(total_vendas)}")
        
        # Calcula valores alvo para sanduíches e bebidas
        valor_sanduiches = total_vendas * (100 - drink_percentage) / 100
        valor_bebidas = total_vendas * drink_percentage / 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Valor para Sanduíches", format_currency(valor_sanduiches))
        with col2:
            st.metric("Valor para Bebidas", format_currency(valor_bebidas))
        
        # Otimização para sanduíches
        st.subheader("🍔 Combinações de Sanduíches")
        comb_sanduiches = optimize_combination(
            CARDAPIOS['sanduiches'],
            valor_sanduiches,
            tamanho_combinacao_sanduiches,
            max_iterations
        )
        
        if comb_sanduiches:
            df_sanduiches = pd.DataFrame.from_dict(comb_sanduiches, orient='index', columns=['Quantidade'])
            df_sanduiches['Preço Unitário'] = df_sanduiches.index.map(CARDAPIOS['sanduiches'].get)
            df_sanduiches['Subtotal'] = df_sanduiches['Quantidade'] * df_sanduiches['Preço Unitário']
            
            # Gráfico de barras para sanduíches
            chart_sanduiches = alt.Chart(df_sanduiches.reset_index()).mark_bar().encode(
                x=alt.X('index:N', title='Sanduíche', sort='-y'),
                y=alt.Y('Subtotal:Q', title='Valor (R$)'),
                color=alt.Color('index:N', legend=None),
                tooltip=['index', 'Quantidade', 'Preço Unitário', 'Subtotal']
            ).properties(
                title=f"Combinação sugerida (Total: {format_currency(df_sanduiches['Subtotal'].sum())})",
                height=400
            )
            st.altair_chart(chart_sanduiches, use_container_width=True)
            
            st.dataframe(df_sanduiches.style.format({
                'Preço Unitário': format_currency,
                'Subtotal': format_currency
            }))
        
        # Otimização para bebidas
        st.subheader("🍹 Combinações de Bebidas")
        comb_bebidas = optimize_combination(
            CARDAPIOS['bebidas'],
            valor_bebidas,
            tamanho_combinacao_bebidas,
            max_iterations
        )
        
        if comb_bebidas:
            df_bebidas = pd.DataFrame.from_dict(comb_bebidas, orient='index', columns=['Quantidade'])
            df_bebidas['Preço Unitário'] = df_bebidas.index.map(CARDAPIOS['bebidas'].get)
            df_bebidas['Subtotal'] = df_bebidas['Quantidade'] * df_bebidas['Preço Unitário']
            
            # Gráfico de barras para bebidas
            chart_bebidas = alt.Chart(df_bebidas.reset_index()).mark_bar().encode(
                x=alt.X('index:N', title='Bebida', sort='-y'),
                y=alt.Y('Subtotal:Q', title='Valor (R$)'),
                color=alt.Color('index:N', legend=None),
                tooltip=['index', 'Quantidade', 'Preço Unitário', 'Subtotal']
            ).properties(
                title=f"Combinação sugerida (Total: {format_currency(df_bebidas['Subtotal'].sum())})",
                height=400
            )
            st.altair_chart(chart_bebidas, use_container_width=True)
            
            st.dataframe(df_bebidas.style.format({
                'Preço Unitário': format_currency,
                'Subtotal': format_currency
            }))
    else:
        st.warning("Por favor, carregue os dados de vendas na aba 'Resumo das Vendas' primeiro.")

with tab3:
    st.header("💰 Cadastro de Recebimentos Diários")
    
    with st.form("receipt_form", clear_on_submit=True):
        data = st.date_input("Data", datetime.now().date())
        dinheiro = st.number_input("Dinheiro (R$)", min_value=0.0, format="%.2f")
        cartao = st.number_input("Cartão (R$)", min_value=0.0, format="%.2f")
        pix = st.number_input("Pix (R$)", min_value=0.0, format="%.2f")
        
        if st.form_submit_button("Salvar") and (dinheiro + cartao + pix) > 0:
            new_data = pd.DataFrame([{
                'Data': data, 'Dinheiro': dinheiro, 'Cartao': cartao, 'Pix': pix
            }])
            st.session_state['df_receipts'] = pd.concat(
                [st.session_state['df_receipts'], new_data], ignore_index=True)
            save_data(st.session_state['df_receipts'])
            st.success("Dados salvos!")
    
    st.header("📊 Análise de Recebimentos")
    if not st.session_state['df_receipts'].empty:
        df = st.session_state['df_receipts'].copy()
        df['Total'] = df[['Dinheiro', 'Cartao', 'Pix']].sum(axis=1)
        df['Data'] = pd.to_datetime(df['Data'])
        
        # Gráfico de Pizza
        totais = df[['Dinheiro', 'Cartao', 'Pix']].sum().reset_index()
        totais.columns = ['Forma', 'Total']
        
        pie_chart = create_altair_chart(
            totais, 'pie', 'Forma', 'Total',
            title='Distribuição dos Recebimentos'
        )
        st.altair_chart(pie_chart, use_container_width=True)
        
        # Gráfico de Linha Temporal
        line_chart = create_altair_chart(
            df, 'line', 'Data', 'Total',
            title='Evolução dos Recebimentos Diários'
        )
        st.altair_chart(line_chart, use_container_width=True)
        
        # Gráfico de Barras Agrupadas
        melted_df = df.melt(id_vars=['Data'], 
                           value_vars=['Dinheiro', 'Cartao', 'Pix'],
                           var_name='Forma', 
                           value_name='Valor')
        
        bar_chart = create_altair_chart(
            melted_df, 'bar', 'Data', 'Valor', 'Forma',
            title='Recebimentos Diários por Forma de Pagamento'
        )
        st.altair_chart(bar_chart, use_container_width=True)
        
        # Tabela de Dados
        st.dataframe(df.sort_values('Data', ascending=False))
    else:
        st.info("Nenhum recebimento cadastrado.")

if __name__ == '__main__':
    pass
