import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import random
import sqlite3
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão - Clips Burger", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

# --- BANCO DE DADOS SQLITE ---
DB_FILE = 'recebimentos.db'  # Arquivo no diretório atual

def init_db():
    """Inicializa o banco de dados SQLite"""
    try:
        # Cria o arquivo diretamente no diretório atual
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS recebimentos
                     (data TEXT, dinheiro REAL, cartao REAL, pix REAL)''')
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao inicializar banco de dados: {str(e)}")

def load_receipts_data():
    """Carrega os dados do banco SQLite"""
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql("SELECT * FROM recebimentos", conn)
        conn.close()
        
        if not df.empty:
            df['Data'] = pd.to_datetime(df['data'])
            df = df.drop(columns=['data'])
            return df.sort_values('Data', ascending=False)
        return pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])
    except Exception as e:
        st.error(f"Erro ao carregar dados do banco: {e}")
        return pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])
        
def save_receipts_data(df):
    """Salva os dados no banco SQLite"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Limpa a tabela antes de inserir novos dados
        c.execute("DELETE FROM recebimentos")
        
        # Prepara os dados para inserção
        df['data'] = df['Data'].dt.strftime('%Y-%m-%d')
        df[['data', 'Dinheiro', 'Cartao', 'Pix']].to_sql('recebimentos', conn, if_exists='append', index=False)
        
        conn.commit()
        conn.close()
        st.success("Dados salvos com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")

# Inicializa o banco de dados
init_db()

# Carrega os dados iniciais
if 'df_receipts' not in st.session_state:
    st.session_state['df_receipts'] = load_receipts_data()

# --- FUNÇÕES AUXILIARES ---
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

def local_search_optimization(item_prices, target_value, combination_size, max_iterations):
    """Optimiza combinações de produtos para atingir um valor alvo."""
    if not item_prices or target_value <= 0:
        return {}

    best_combination = generate_initial_combination(item_prices, combination_size)
    best_combination = {k: round_to_50_or_00(v) for k, v in best_combination.items()}
    current_value = calculate_combination_value(best_combination, item_prices)

    best_diff = abs(target_value - current_value) + (10000 if current_value > target_value else 0)
    current_items = list(best_combination.keys())

    for _ in range(max_iterations):
        if not current_items: break

        neighbor = best_combination.copy()
        item_to_modify = random.choice(current_items)

        change = random.choice([-0.50, 0.50, -1.00, 1.00])
        neighbor[item_to_modify] = round_to_50_or_00(neighbor[item_to_modify] + change)
        neighbor[item_to_modify] = max(0.50, neighbor[item_to_modify])

        neighbor_value = calculate_combination_value(neighbor, item_prices)
        neighbor_diff = abs(target_value - neighbor_value) + (10000 if neighbor_value > target_value else 0)

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

# --- CARDÁPIOS ATUALIZADOS ---
DADOS_SANDUICHES = """
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
"""

DADOS_BEBIDAS = """
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

# --- INTERFACE STREAMLIT ---
col_title1, col_title2 = st.columns([0.30, 0.70])
with col_title1:
    try:
        st.image("logo.png", width=1000)
    except FileNotFoundError:
        st.warning("Logo não encontrada")
with col_title2:
    st.title("Sistema de Gestão")
    st.markdown("<p style='font-weight:bold; font-size:30px; margin-top:-15px'>Clip's Burger</p>", unsafe_allow_html=True)

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

# --- ABAS PRINCIPAIS ---
tab1, tab2, tab3 = st.tabs(["📈 Resumo das Vendas", "🧩 Detalhes das Combinações", "💰 Cadastro de Recebimentos"])

# --- TAB 1: RESUMO DAS VENDAS ---
with tab1:
    st.header("📈 Resumo das Vendas")
    arquivo = st.file_uploader("📤 Envie o arquivo de transações (.csv ou .xlsx)", type=["csv", "xlsx"])

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
                    'crédito à vista american express': 'Crédito Amex',
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

                # Cardápios
                dados_sanduiches = """X Salada Simples R$ 18,00
X Bacon R$ 22,00
X Tudo R$ 25,00
X Frango R$ 20,00
X Egg R$ 21,00
Cebola R$ 5,00"""
                
                dados_bebidas = """Suco R$ 10,00
Refrigerante R$ 8,00
Água R$ 5,00
Cerveja R$ 12,00"""
                
                sanduiches_precos = parse_menu_string(dados_sanduiches)
                bebidas_precos = parse_menu_string(dados_bebidas)

                if not sanduiches_precos or not bebidas_precos:
                    st.error("Erro ao carregar cardápios. Verifique os dados no código.")
                    st.stop()

                # Gráfico de vendas
                st.subheader("Vendas por Forma de Pagamento")
                if vendas:
                    df_vendas = pd.DataFrame(list(vendas.items()), columns=['Forma de Pagamento', 'Valor Total'])
                    
                    chart = alt.Chart(df_vendas).mark_bar().encode(
                        x=alt.X('Forma de Pagamento:N', axis=alt.Axis(labels=False, title=None)),  # Remove rótulos e título do eixo X
                        y=alt.Y('Valor Total:Q', title=None),  # Remove título do eixo Y
                        color=alt.Color('Forma de Pagamento:N', legend=alt.Legend(
                            title="Formas de Pagamento",
                            orient='bottom',
                            titleFontSize=14,
                            labelFontSize=12
                        )),
                        tooltip=['Forma de Pagamento', 'Valor Total']
                    ).properties(
                        height=400
                    ).configure_axis(
                        grid=False  # Remove linhas de grade se desejar
                    )
                    
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("Nenhum dado de vendas disponível")
                
                    # Divisor de página no final
                    st.divider()
                    
                # --- Cálculo dos impostos e custos fixos ---
                st.subheader("💰 Resumo de Impostos e Custos Fixos")

                salario_minimo = st.number_input("💼 Salário Mínimo (R$)", min_value=0.0, value=1518.0, step=50.0)
                custo_contadora = st.number_input("📋 Custo com Contadora (R$)", min_value=0.0, value=316.0, step=10.0)

                total_vendas = sum(vendas.values())
                st.metric("💵 Faturamento Bruto", format_currency(total_vendas))

                aliquota_simples = 0.06
                imposto_simples = total_vendas * aliquota_simples
                st.metric("📊 Simples Nacional (6%)", format_currency(imposto_simples))
                with st.expander("📘 Como é calculado o Simples Nacional?"):
                    st.markdown(f"""
                    - Alíquota aplicada: **6%**
                    - Fórmula: `faturamento_bruto × 6%`
                    - Exemplo: `{format_currency(total_vendas)} × 0.06 = {format_currency(imposto_simples)}`
                    """)

                fgts = salario_minimo * 0.08
                ferias_mais_terco = (salario_minimo / 12) + ((salario_minimo / 12) / 3)
                decimo_terceiro = salario_minimo / 12
                custo_funcionario = salario_minimo + fgts + ferias_mais_terco + decimo_terceiro
                st.metric("👷‍♂️ Custo Mensal com Funcionário CLT", format_currency(custo_funcionario))
                with st.expander("📘 Como é calculado o custo com funcionário?"):
                    st.markdown(f"""
                    - **Salário Mínimo**: {format_currency(salario_minimo)}
                    - **FGTS (8%)**: {format_currency(fgts)}
                    - **Férias + 1/3 constitucional**: {format_currency(ferias_mais_terco)}
                    - **13º proporcional**: {format_currency(decimo_terceiro)}
                    - **Total**: {format_currency(custo_funcionario)}
                    """)

                st.metric("📋 Custo com Contadora", format_currency(custo_contadora))
                with st.expander("📘 Custo da Contadora"):
                    st.markdown(f"""
                    - Valor mensal fixo: **{format_currency(custo_contadora)}**
                    - Inclui folha, DAS, declarações, etc.
                    """)

                total_custos = imposto_simples + custo_funcionario + custo_contadora
                lucro_estimado = total_vendas - total_custos
                st.metric("💸 Total de Custos", format_currency(total_custos))
                st.metric("📈 Lucro Estimado (após custos)", format_currency(lucro_estimado))
                with st.expander("📘 Como é calculado o lucro estimado?"):
                    st.markdown(f"""
                    - Fórmula: `faturamento - (impostos + funcionário + contadora)`
                    - Cálculo:
                    ```
                    {format_currency(total_vendas)} - ({format_currency(imposto_simples)} + {format_currency(custo_funcionario)} + {format_currency(custo_contadora)})
                    = {format_currency(lucro_estimado)}
                    ```
                    """)

            except Exception as e:
                st.error(f"Erro no processamento do arquivo: {str(e)}")
    else:
        st.info("✨ Aguardando o envio do arquivo de transações para iniciar a análise...")
# --- TAB 3: CADASTRO DE RECEBIMENTOS ---
with tab3:
    st.header("💰 Cadastro de Recebimentos Diários")

    # Formulário para adicionar recebimentos
    with st.form("daily_receipt_form", clear_on_submit=True):
        data = st.date_input("Data do Recebimento", datetime.now().date())
        
        col1, col2, col3 = st.columns(3)
        dinheiro = col1.number_input("Dinheiro (R$)", min_value=0.0, step=0.01, format="%.2f")
        cartao = col2.number_input("Cartão (R$)", min_value=0.0, step=0.01, format="%.2f")
        pix = col3.number_input("Pix (R$)", min_value=0.0, step=0.01, format="%.2f")
        
        submitted = st.form_submit_button("Salvar Recebimento")
        if submitted:
            if dinheiro + cartao + pix > 0:
                new_receipt = pd.DataFrame([{
                    'Data': pd.to_datetime(data),
                    'Dinheiro': dinheiro,
                    'Cartao': cartao,
                    'Pix': pix
                }])
                
                # Atualiza os dados na sessão e no banco de dados
                st.session_state['df_receipts'] = pd.concat([st.session_state['df_receipts'], new_receipt], ignore_index=True)
                save_receipts_data(st.session_state['df_receipts'])
                st.success("Recebimento salvo com sucesso!")
            else:
                st.warning("Por favor, insira ao menos um valor positivo.")

    # Visualização dos dados
    st.header("📊 Análise de Recebimentos")
    
    if not st.session_state['df_receipts'].empty:
        df = st.session_state['df_receipts'].copy()
        
        # Gráfico de Pizza
        st.subheader("Distribuição por Forma de Pagamento")
        total_pagamentos = df[['Dinheiro', 'Cartao', 'Pix']].sum()
        
        pie_chart = alt.Chart(
            pd.DataFrame({
                'Forma': total_pagamentos.index,
                'Valor': total_pagamentos.values
            })
        ).mark_arc().encode(
            theta='Valor',
            color='Forma',
            tooltip=['Forma', 'Valor']
        ).properties(
            width=500,
            height=400
        )
        st.altair_chart(pie_chart, use_container_width=True)
        
        # Gráfico de Linha (Evolução)
        st.subheader("Evolução dos Recebimentos")
        df['Total'] = df['Dinheiro'] + df['Cartao'] + df['Pix']
        df['Data'] = pd.to_datetime(df['Data'])
        
        line_chart = alt.Chart(df).mark_line().encode(
            x='Data:T',
            y='Total:Q',
            tooltip=['Data', 'Dinheiro', 'Cartao', 'Pix', 'Total']
        ).properties(
            width=800,
            height=400
        )
        st.altair_chart(line_chart, use_container_width=True)
        
        # Tabela com todos os dados
        st.subheader("Histórico Completo")
        st.dataframe(df.sort_values('Data', ascending=False))
    else:
        st.info("Nenhum recebimento cadastrado ainda. Use o formulário acima para adicionar dados.")

if __name__ == '__main__':
    pass
