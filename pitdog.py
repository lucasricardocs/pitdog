import streamlit as st
import pandas as pd
import random
import time # Para simular processamento e usar spinner

# ----- Funções Auxiliares (mantidas como antes) -----

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
        elif line.strip(): # Avoid warnings for empty lines
             st.warning(f"Formato inválido na linha do cardápio: '{line}'. Esperado 'Nome R$ Preço'. Ignorando linha.")
    return menu

def calculate_combination_value(combination, item_prices):
    """Calculates the total value of a combination based on item prices."""
    # Certifica que apenas itens existentes no cardápio sejam considerados
    return sum(item_prices.get(name, 0) * quantity for name, quantity in combination.items())


def generate_initial_combination(item_prices, combination_size):
    """Generates a random initial combination for the local search."""
    combination = {}
    item_names = list(item_prices.keys())
    if not item_names:
        return combination
    size = min(combination_size, len(item_names))
    chosen_names = random.sample(item_names, size)
    for name in chosen_names:
        combination[name] = random.uniform(1, 75) # Range arbitrário original
    return combination

def local_search_optimization(item_prices, target_value, combination_size, max_iterations):
    """
    Uses a randomized local search heuristic to find a combination of items
    approximating the target_value. (Docstring omitted for brevity, same as before)
    """
    if not item_prices or target_value <= 0:
        return {}

    best_combination = generate_initial_combination(item_prices, combination_size)
    if not best_combination: return {}

    # Correção: Usar get para evitar KeyError se item não estiver no cardápio (improvável aqui, mas seguro)
    current_value = calculate_combination_value(best_combination, item_prices)
    best_diff = abs(target_value - current_value)

    current_items = list(best_combination.keys())

    for _ in range(max_iterations):
        if not current_items: break

        neighbor = best_combination.copy()
        item_to_modify = random.choice(current_items)

        change = random.uniform(-5, 5) # Range arbitrário original
        neighbor[item_to_modify] += change
        neighbor[item_to_modify] = max(1.0, min(neighbor[item_to_modify], 75.0)) # Range arbitrário original

        # Avalia o vizinho
        neighbor_value = calculate_combination_value(neighbor, item_prices)
        neighbor_diff = abs(target_value - neighbor_value)

        if neighbor_diff < best_diff:
            best_diff = neighbor_diff
            best_combination = neighbor

        if best_diff < 0.01: break # Tolerância para parada antecipada

    return best_combination


def format_currency(value):
    """Formats a number as Brazilian Real currency."""
    if pd.isna(value):
        return "R$ -" # Handle potential NaN values
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ Inválido"


# ----- Interface Streamlit -----
st.set_page_config(page_title="Análise de Vendas & Combinações", layout="wide", initial_sidebar_state="expanded")

# Colunas para Título e Emoji
col_title1, col_title2 = st.columns([0.9, 0.1])
with col_title1:
    st.title("📊 Análise de Vendas e Geração de Combinações")
with col_title2:
    st.image("https://cdn-icons-png.flaticon.com/128/1041/1041880.png", width=70) # Exemplo de ícone

st.markdown("""
Bem-vindo(a)! Esta ferramenta ajuda a visualizar suas vendas por forma de pagamento
e tenta encontrar combinações *hipotéticas* de produtos (baseadas em um cardápio pré-definido)
que poderiam corresponder a esses totais.

**Como usar:**
1.  Ajuste as configurações na barra lateral (opcional).
2.  Faça o upload do seu arquivo de transações (.csv ou .xlsx).
3.  Explore os resultados nas abas abaixo.
""")
st.divider()

# --- Configuration Sidebar ---
with st.sidebar:
    st.header("⚙️ Configurações")
    drink_percentage = st.slider(
        "Percentual para Bebidas (%) 🍹",
        min_value=0, max_value=100, value=20, step=5,
        help="Define qual porcentagem do valor total será usada como meta para bebidas."
    )
    sandwich_percentage = 100 - drink_percentage
    st.caption(f"({sandwich_percentage}% será alocado para Sanduíches 🍔)")

    tamanho_combinacao_bebidas = st.slider(
        "Número de tipos de Bebidas",
        min_value=1, max_value=10, value=5, step=1,
        help="Quantos tipos *diferentes* de bebidas tentar incluir."
    )
    tamanho_combinacao_sanduiches = st.slider(
        "Número de tipos de Sanduíches",
        min_value=1, max_value=15, value=5, step=1,
        help="Quantos tipos *diferentes* de sanduíches tentar incluir."
    )
    max_iterations = st.select_slider(
        "Qualidade da Otimização ✨",
        options=[1000, 5000, 10000, 20000, 50000],
        value=10000,
        help="Número de tentativas do algoritmo. Mais = melhor (e mais lento)."
    )
    st.info("Lembre-se: As combinações são aproximações heurísticas.")


# --- File Upload ---
arquivo = st.file_uploader("📤 Envie o arquivo de transações (.csv ou .xlsx)", type=["csv", "xlsx"], label_visibility="visible")

if arquivo:
    # Mostrar indicador de processamento
    with st.spinner(f'Processando "{arquivo.name}"... Por favor, aguarde.'):
        df = None
        df_processed = None # Para guardar o DF após processamento
        try:
            # --- Leitura e Processamento do Arquivo ---
            start_time = time.time()
            if arquivo.name.endswith(".csv"):
                try:
                    df = pd.read_csv(arquivo, sep=';', encoding='utf-8', dtype=str)
                except Exception:
                    arquivo.seek(0)
                    try:
                        df = pd.read_csv(arquivo, sep=',', encoding='utf-8', dtype=str)
                    except Exception as e:
                        st.error(f"Não foi possível ler o CSV. Verifique o separador (';' ou ',') e a codificação (UTF-8). Erro: {e}")
                        st.stop()
            else:
                df = pd.read_excel(arquivo, dtype=str)

            st.success(f"Arquivo '{arquivo.name}' carregado com sucesso!")

            # --- Limpeza e Preparação dos Dados ---
            required_columns = ['Tipo', 'Bandeira', 'Valor']
            if not all(col in df.columns for col in required_columns):
                st.error(f"Erro: O arquivo precisa conter as colunas: {', '.join(required_columns)}")
                st.stop()

            df_processed = df.copy()
            df_processed['Tipo'] = df_processed['Tipo'].str.lower().str.strip().fillna('desconhecido')
            df_processed['Bandeira'] = df_processed['Bandeira'].str.lower().str.strip().fillna('desconhecida')
            df_processed['Valor_Numeric'] = pd.to_numeric(df_processed['Valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce') # Lida com R$ 1.234,56
            df_processed.dropna(subset=['Valor_Numeric'], inplace=True)

            df_processed['Categoria'] = df_processed['Tipo'] + ' ' + df_processed['Bandeira']
            categorias_desejadas = {
                'crédito à vista elo': 'Crédito Elo', 'crédito à vista mastercard': 'Crédito MasterCard',
                'crédito à vista visa': 'Crédito Visa', 'débito elo': 'Débito Elo',
                'débito mastercard': 'Débito MasterCard', 'débito visa': 'Débito Visa',
                'pix ': 'PIX', 'pix': 'PIX' # Mapeamentos
            }
            df_processed['Forma Nomeada'] = df_processed['Categoria'].map(categorias_desejadas)
            df_filtered = df_processed.dropna(subset=['Forma Nomeada']).copy()

            if df_filtered.empty:
                st.warning("Nenhuma transação encontrada para as formas de pagamento mapeadas.")
                st.stop()

            # --- Cálculo dos Totais ---
            vendas = df_filtered.groupby('Forma Nomeada')['Valor_Numeric'].sum() # Agora é uma Series

            # --- Definição dos Cardápios ---
            dados_sanduiches = """
            X Salada Simples R$ 18,00; X Salada Especial R$ 20,00; X Especial Duplo R$ 24,00;
            X Bacon Simples R$ 22,00; X Bacon Especial R$ 24,00; X Bacon Duplo R$ 28,00;
            X Hamburgão R$ 35,00; X Mata-Fome R$ 39,00; X Frango Simples R$ 22,00;
            X Frango Especial R$ 24,00; X Frango Bacon R$ 27,00; X Frango Tudo R$ 30,00;
            X Lombo Simples R$ 23,00; X Lombo Especial R$ 25,00; X Lombo Bacon R$ 28,00;
            X Lombo Tudo R$ 31,00; X Filé Simples R$ 28,00; X Filé Especial R$ 30,00;
            X Filé Bacon R$ 33,00; X Filé Tudo R$ 36,00; Cebola R$ 0.50
            """
            dados_bebidas = """
            Suco R$ 10,00; Creme R$ 15,00; Refri caçula R$ 3.50; Refri Lata R$ 7,00;
            Refri 600 R$ 8,00; Refri 1L R$ 10,00; Refri 2L R$ 15,00; Água R$ 3,00;
            Água com Gas R$ 4,00
            """
            # Adaptação para ler de string separada por ';' e nova linha
            sanduiches_precos = parse_menu_string(dados_sanduiches.replace(';', '\n'))
            bebidas_precos = parse_menu_string(dados_bebidas.replace(';', '\n'))

            if not sanduiches_precos or not bebidas_precos:
                 st.error("Erro ao carregar cardápios. Verifique os dados no código.")
                 st.stop()

            processing_time = time.time() - start_time
            st.caption(f"Processamento inicial concluído em {processing_time:.2f} segundos.")

        except FileNotFoundError:
            st.error("Erro: Arquivo não encontrado.")
            st.stop()
        except pd.errors.EmptyDataError:
            st.error("Erro: O arquivo enviado está vazio.")
            st.stop()
        except KeyError as e:
            st.error(f"Erro: Coluna esperada não encontrada: {e}. Verifique se 'Tipo', 'Bandeira' e 'Valor' existem.")
            st.stop()
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado no processamento: {e}")
            st.exception(e)
            st.stop()

    # --- Display dos Resultados em Abas ---
    tab1, tab2, tab3 = st.tabs(["📈 Resumo das Vendas", "🧩 Detalhes das Combinações", "📄 Dados Processados"])

    with tab1:
        st.header("📈 Resumo das Vendas por Forma de Pagamento")
        if not vendas.empty:
            # Criar DataFrame para o gráfico
            df_vendas = vendas.reset_index()
            df_vendas.columns = ['Forma de Pagamento', 'Valor Total']
            df_vendas['Valor Formatado'] = df_vendas['Valor Total'].apply(format_currency)

            # Gráfico de Barras
            st.bar_chart(df_vendas.set_index('Forma de Pagamento')['Valor Total'])
            st.caption("Valor total vendido para cada forma de pagamento mapeada.")

            # Tabela com valores formatados (opcional)
            st.dataframe(df_vendas[['Forma de Pagamento', 'Valor Formatado']], use_container_width=True)
        else:
            st.warning("Nenhum dado de venda para exibir.")

    with tab2:
        st.header("🧩 Detalhes das Combinações Geradas")
        st.caption(f"Tentando alocar {drink_percentage}% para bebidas e {sandwich_percentage}% para sanduíches.")

        ordem_formas = [
            'Débito Visa', 'Débito MasterCard', 'Débito Elo',
            'Crédito Visa', 'Crédito MasterCard', 'Crédito Elo', 'PIX'
        ]
        vendas_ordenadas = {forma: vendas[forma] for forma in ordem_formas if forma in vendas}
        for forma, total in vendas.items(): # Adiciona formas não previstas na ordem
            if forma not in vendas_ordenadas: vendas_ordenadas[forma] = total

        if not vendas_ordenadas:
            st.info("Nenhuma venda encontrada nas categorias mapeadas para gerar combinações.")

        for forma, total_pagamento in vendas_ordenadas.items():
             if total_pagamento <= 0: continue

             # Mostrar spinner para a otimização de cada forma
             with st.spinner(f"Gerando combinação para {forma}..."):
                 target_bebidas = total_pagamento * (drink_percentage / 100.0)
                 target_sanduiches = total_pagamento - target_bebidas

                 comb_bebidas_float = local_search_optimization(bebidas_precos, target_bebidas, tamanho_combinacao_bebidas, max_iterations)
                 comb_sanduiches_float = local_search_optimization(sanduiches_precos, target_sanduiches, tamanho_combinacao_sanduiches, max_iterations)

                 comb_bebidas_rounded = {name: round(qty) for name, qty in comb_bebidas_float.items() if round(qty) > 0}
                 comb_sanduiches_rounded = {name: round(qty) for name, qty in comb_sanduiches_float.items() if round(qty) > 0}

                 total_calc_bebidas = calculate_combination_value(comb_bebidas_rounded, bebidas_precos)
                 total_calc_sanduiches = calculate_combination_value(comb_sanduiches_rounded, sanduiches_precos)
                 total_calc_geral = total_calc_bebidas + total_calc_sanduiches

             # Expander para cada forma de pagamento
            with st.expander(f"**{forma}** (Total: R$ {total:.2f})", expanded=False):
                diferenca = valor_total_calc - total
                cor_diferenca = "red" if abs(diferenca) > 0.01 else "green"
                sinal = "+" if diferenca > 0 else ""
                    st.markdown(f"<span style='font-size: large; color: steelblue;'>Valor Calculado: <b style='color: darkblue;'>{format_currency(valor_total_calc)}</b></span> | <span style='font-size: medium; color: grey;'>Diferença: <b style='color: {cor_diferenca};'>{sinal}{format_currency(diferenca)}</b></span>", unsafe_allow_html=True)
                    st.caption("Combinação *hipotética* otimizada para o valor total.")

    # ... (o restante do código para exibir os itens de bebidas e sanduíches) ...
        
            #expander_title = f"**{forma}** (Total: {format_currency(total_pagamento)})"
             #with st.expander(expander_title, expanded=False):
              #   st.markdown(f"<span style='font-size: large; color: grey;'>Bebidas ({drink_percentage}%): {format_currency(target_bebidas)} | Sanduiches ({sandwich_percentage}%): {format_currency(target_sanduiches)}</span>", unsafe_allow_html=True)
               #  st.caption("Combinação *hipotética* encontrada pelo algoritmo. Quantidades arredondadas.")

                 col1, col2 = st.columns(2) # Mantém as colunas para separar Bebidas de Sanduíches
                 with col1:
                     st.subheader("🍹 Bebidas")
                     if comb_bebidas_rounded:
                         # ----- MODIFICAÇÃO AQUI: Exibir como lista -----
                         for nome, qtt in comb_bebidas_rounded.items():
                             val_item = bebidas_precos.get(nome, 0) * qtt
                             # Usar st.markdown para criar um item de lista
                             st.markdown(f"- **{nome}:** {qtt} un ({format_currency(val_item)})")
                         # -------------------------------------------------
                         st.divider() # Mantém o divisor
                         st.metric("Total Calculado (Bebidas)", format_currency(total_calc_bebidas)) # Mantém a métrica total
                     else:
                         st.info("Nenhuma bebida na combinação.") # Mantém mensagem caso vazio

                 with col2:
                     st.subheader("🍔 Sanduíches")
                     if comb_sanduiches_rounded:
                         # ----- MODIFICAÇÃO AQUI: Exibir como lista -----
                         for nome, qtt in comb_sanduiches_rounded.items():
                              val_item = sanduiches_precos.get(nome, 0) * qtt
                              # Usar st.markdown para criar um item de lista
                              st.markdown(f"- **{nome}:** {qtt} un ({format_currency(val_item)})")
                         # -------------------------------------------------
                         st.divider() # Mantém o divisor
                         st.metric("Total Calculado (Sanduíches)", format_currency(total_calc_sanduiches)) # Mantém a métrica total
                     else:
                         st.info("Nenhum sanduíche na combinação.") # Mantém mensagem caso vazio

                 st.divider()
                 diff_geral = total_calc_geral - total_pagamento
                 delta_sign = "+" if diff_geral >= 0 else ""
                 st.metric(
                      "💰 TOTAL GERAL (Calculado da Combinação)",
                      format_currency(total_calc_geral),
                      delta=f"{delta_sign}{format_currency(diff_geral)} vs Meta",
                      delta_color="normal"
                  ) # Mantém a métrica final

    with tab3:
        st.header("📄 Tabela de Dados Processados")
        st.caption("Pré-visualização dos dados após limpeza e mapeamento de categorias.")
        if df_processed is not None:
            # Mostrar colunas relevantes para o usuário
            cols_to_show = ['Tipo', 'Bandeira', 'Valor', 'Categoria', 'Forma Nomeada', 'Valor_Numeric']
            st.dataframe(df_filtered[cols_to_show], use_container_width=True) # Mostra apenas os filtrados usados nos cálculos
            # st.dataframe(df_processed, use_container_width=True) # Ou mostrar todos os processados
        else:
            st.info("Faça o upload de um arquivo para ver os dados processados.")

else:
    st.info("✨ Aguardando o envio do arquivo de transações para iniciar a análise...")
    st.image("https://cdn-icons-png.flaticon.com/128/3652/3652191.png", width=100) # Ícone inicial
