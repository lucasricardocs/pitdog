# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import random
import time # Mantido caso precise no futuro, mas não usado na busca atual
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# ----- Funções Auxiliares -----
def parse_menu_string(menu_data_string):
    """Parses a multi-line string containing menu items and prices."""
    # (Mantida exatamente como na sua versão anterior - sem alterações)
    menu = {}
    lines = menu_data_string.strip().split("\n")
    for line in lines:
        parts = line.rsplit("R$ ", 1)
        if len(parts) == 2:
            name = parts[0].strip()
            try:
                price = float(parts[1].replace(",", ".").strip())
                menu[name] = price
            except ValueError:
                st.warning(f"Preço inválido para '{name}'. Ignorando item.")
        elif line.strip():
            st.warning(f"Formato inválido na linha do cardápio: '{line}'. Ignorando linha.")
    return menu

def calculate_combination_value(combination, item_prices):
    """Calculates the total value of a combination based on item prices."""
    # (Mantida exatamente como na sua versão anterior - sem alterações)
    # Garante que item exista no dicionario de precos antes de multiplicar
    return sum(item_prices.get(name, 0) * quantity for name, quantity in combination.items() if quantity > 0 and name in item_prices)


def round_to_50_or_00(value):
    """Arredonda para o múltiplo de 0.50 mais próximo"""
    # (Mantida exatamente como na sua versão anterior - sem alterações)
    # Necessária para arredondar os VALORES ALVO (targets)
    tolerance = 1e-9
    return round((value + tolerance) * 2) / 2

# ===== FUNÇÃO MODIFICADA para se alinhar com a lógica do primeiro exemplo =====
def generate_initial_combination(item_prices, combination_size):
    """
    Gera uma combinação inicial aleatória.
    Adaptação: Usa amostragem sem reposição (sample) como no Streamlit,
               mas gera quantidades float entre 1 e 75, como no primeiro exemplo.
    """
    combination = {}
    item_names = list(item_prices.keys())
    if not item_names:
        return combination

    # Garante que não tentamos pegar mais itens únicos do que os disponíveis
    actual_size = min(combination_size, len(item_names))
    if actual_size <= 0:
        return {} # Retorna vazio se não for possível escolher itens

    # Escolhe os nomes dos itens SEM reposição
    chosen_names = random.sample(item_names, actual_size)

    # Atribui quantidades float aleatórias entre 1 e 75
    for name in chosen_names:
        # Quantidade float aleatória entre 1.0 e 75.0
        combination[name] = random.uniform(1.0, 75.0)

    return combination

# Função mantida pois é usada para o ajuste *pós-busca*
def adjust_with_onions(combination, item_prices, target_value):
    """
    Ajusta a combinação adicionando cebolas se o valor for menor que o target.
    Retorna a combinação modificada e o valor final.
    Limita a quantidade máxima de cebolas a 20 unidades.
    (Mantida exatamente como na sua versão anterior - sem alterações)
    """
    current_value = calculate_combination_value(combination, item_prices)
    difference = target_value - current_value

    if difference <= 0 or "Cebola" not in item_prices or item_prices["Cebola"] <= 0:
        return combination, current_value

    onion_price = item_prices["Cebola"]
    num_onions_to_add = max(0, int(difference // onion_price))

    current_onions = combination.get("Cebola", 0)
    max_possible_onions = 20

    if current_onions + num_onions_to_add > max_possible_onions:
        num_onions_to_add = max_possible_onions - current_onions

    if num_onions_to_add > 0:
        # Certifique-se que a quantidade adicionada é um inteiro ou float compatível
        combination["Cebola"] = current_onions + float(num_onions_to_add)

    final_value = calculate_combination_value(combination, item_prices)
    return combination, final_value

# ===== FUNÇÃO PRINCIPAL DA BUSCA - LÓGICA SUBSTITUÍDA =====
def local_search_optimization(item_prices, target_value, combination_size, max_iterations):
    """
    Executa o algoritmo de busca local implementando a lógica
    da função 'busca_local_otimizada' do primeiro exemplo.
    - Quantidades são float [1.0, 75.0].
    - Modificação: +/- random.uniform(-5, 5).
    - Critério: Minimizar diferença absoluta.
    - Parada: max_iterations ou diff < 0.01.
    """
    if not item_prices or target_value <= 0:
        return {} # Retorna dicionário vazio se não há itens ou alvo inválido

    # 1. Geração da combinação inicial (usando a função adaptada)
    best_combination = generate_initial_combination(item_prices, combination_size)
    if not best_combination:
         return {} # Retorna vazio se a geração inicial falhar

    # 2. Cálculo da diferença inicial (absoluta)
    current_value = calculate_combination_value(best_combination, item_prices)
    best_difference = abs(target_value - current_value)

    # 3. Loop de otimização
    for _ in range(max_iterations):
        # Pega os nomes dos itens atualmente na melhor combinação
        # É importante atualizar a cada iteração caso a melhor combinação mude
        current_item_names = list(best_combination.keys())
        if not current_item_names:
             break # Para se a combinação ficar vazia (não deveria acontecer com clamp >= 1)

        # Cria uma cópia (vizinho) para modificar
        neighbor = best_combination.copy()

        # Escolhe um item aleatório *já presente* no vizinho para modificar
        item_to_modify = random.choice(current_item_names)

        # Calcula a mudança aleatória (float)
        change = random.uniform(-5.0, 5.0)

        # Aplica a mudança à quantidade do item escolhido
        # Usar .get com default 1.0 é uma segurança, mas o item deve existir
        neighbor[item_to_modify] = neighbor.get(item_to_modify, 1.0) + change

        # Aplica o clamp (limita a quantidade entre 1.0 e 75.0)
        neighbor[item_to_modify] = max(1.0, min(neighbor[item_to_modify], 75.0))

        # Calcula a diferença absoluta do vizinho
        neighbor_value = calculate_combination_value(neighbor, item_prices)
        neighbor_difference = abs(target_value - neighbor_value)

        # Aceita o vizinho se a diferença for estritamente menor
        if neighbor_difference < best_difference:
            best_difference = neighbor_difference
            best_combination = neighbor # Atualiza a melhor combinação

        # Critério de parada por qualidade da solução
        if best_difference < 0.01:
            break

    # Retorna a melhor combinação encontrada (com quantidades float)
    return best_combination
# =========================================================

def format_currency(value):
    """Formats a number as Brazilian Real currency."""
    # (Mantida exatamente como na sua versão anterior - sem alterações)
    if pd.isna(value) or value is None:
        return "R$ -"
    try:
        float_value = float(value)
        return f"R$ {float_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ Inválido"

# --- Funções de Plotagem ---
# (Mantidas exatamente como na sua versão anterior - sem alterações)
def plot_daily_sales(df):
    """Gráfico de vendas por dia"""
    try:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        df.dropna(subset=['Data'], inplace=True)
        if df.empty: return
        daily_sales = df.groupby(df['Data'].dt.date)['Valor_Numeric'].sum()
        if daily_sales.empty: return

        fig, ax = plt.subplots(figsize=(10, 5))
        daily_sales.plot(kind='line', marker='o', ax=ax)
        ax.set_title('Vendas Diárias')
        ax.set_xlabel('Data')
        ax.set_ylabel('Valor (R$)')
        ax.grid(True)
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.warning(f"Não foi possível gerar gráfico de vendas diárias: {e}")


def plot_payment_methods(df):
    """Gráfico de formas de pagamento"""
    try:
        # Garantir que 'Forma Nomeada' existe e não está vazia
        if 'Forma Nomeada' not in df.columns or df['Forma Nomeada'].isnull().all():
            st.warning("Coluna 'Forma Nomeada' não encontrada ou vazia para gráfico de pagamentos.")
            return

        payment_methods = df.groupby('Forma Nomeada')['Valor_Numeric'].sum().sort_values(ascending=False)
        if payment_methods.empty: return

        fig, ax = plt.subplots(figsize=(10, 5))
        payment_methods.plot(kind='bar', ax=ax)
        ax.set_title('Vendas por Forma de Pagamento')
        ax.set_xlabel('Forma de Pagamento')
        ax.set_ylabel('Valor (R$)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.warning(f"Não foi possível gerar gráfico de formas de pagamento: {e}")

def plot_hourly_sales(df):
    """Gráfico de vendas por hora do dia"""
    if 'Hora' not in df.columns:
        # st.info("Coluna 'Hora' não encontrada para gerar gráfico de vendas por hora.") # Menos verboso
        return
    try:
        # Tenta converter diferentes formatos de hora
        df_copy = df.copy() # Trabalhar com cópia para evitar modificar original
        df_copy['Hora_Num'] = pd.to_datetime(df_copy['Hora'], errors='coerce').dt.hour
        if df_copy['Hora_Num'].isnull().all():
             df_copy['Hora_Num'] = pd.to_datetime(df_copy['Hora'], format='%H:%M', errors='coerce').dt.hour

        df_copy.dropna(subset=['Hora_Num'], inplace=True)
        if df_copy.empty: return

        # Garante que Hora_Num é inteiro para o groupby
        df_copy['Hora_Num'] = df_copy['Hora_Num'].astype(int)

        hourly_sales = df_copy.groupby('Hora_Num')['Valor_Numeric'].sum()
        hourly_sales = hourly_sales.reindex(range(24), fill_value=0)
        if hourly_sales.empty or hourly_sales.sum() == 0: return # Não plotar se vazio ou só zeros

        fig, ax = plt.subplots(figsize=(10, 5))
        hourly_sales.plot(kind='bar', ax=ax)
        ax.set_title('Vendas por Hora do Dia')
        ax.set_xlabel('Hora')
        ax.set_ylabel('Valor (R$)')
        plt.xticks(rotation=0)
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.warning(f"Não foi possível gerar gráfico de vendas por hora: {e}")


# ----- Interface Streamlit -----
# (Mantida exatamente como na sua versão anterior - sem alterações nos widgets ou layout)
st.set_page_config(page_title="Análise de Vendas & Combinações", layout="wide", initial_sidebar_state="expanded")

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
        "Número Máx. de tipos de Bebidas",
        min_value=1, max_value=10, value=5, step=1,
        help="Define o número máximo de tipos diferentes de bebidas na combinação inicial."
    )
    tamanho_combinacao_sanduiches = st.slider(
        "Número Máx. de tipos de Sanduíches",
        min_value=1, max_value=10, value=5, step=1,
        help="Define o número máximo de tipos diferentes de sanduíches na combinação inicial."
    )
    max_iterations = st.select_slider(
        "Qualidade da Otimização (Iterações) ✨",
        options=[1000, 5000, 10000, 20000, 50000, 100000], # Adicionado 100k
        value=10000, # Mantido padrão 10k
        help="Número de tentativas de melhoria para cada busca local."
    )
    # REMOVIDO o slider de reinicializações, pois a lógica agora é a do primeiro exemplo (busca única)
    st.info("Lembre-se: As combinações são aproximações heurísticas.")

# --- File Upload ---
arquivo = st.file_uploader("📤 Envie o arquivo de transações (.csv ou .xlsx)", type=["csv", "xlsx"])

if arquivo:
    with st.spinner(f'Processando "{arquivo.name}"...'):
        try:
            # (Leitura de arquivo mantida como na versão anterior, com tentativas de separador/encoding)
            if arquivo.name.endswith(".csv"):
                try:
                    df = pd.read_csv(arquivo, sep=';', encoding='latin-1', dtype=str)
                except Exception:
                    try:
                        arquivo.seek(0)
                        df = pd.read_csv(arquivo, sep=',', encoding='utf-8', dtype=str)
                    except Exception:
                         try:
                              arquivo.seek(0)
                              df = pd.read_csv(arquivo, sep=';', encoding='utf-8', dtype=str)
                         except Exception as e:
                              st.error(f"Não foi possível ler o CSV. Verifique o separador (',' ou ';') e a codificação (UTF-8 ou Latin-1). Erro: {e}")
                              st.stop()
            else: # .xlsx
                df = pd.read_excel(arquivo, dtype=str)

            st.success(f"Arquivo '{arquivo.name}' carregado com sucesso!")

            # (Processamento de dados mantido como na versão anterior - robusto)
            required_columns = ['Tipo', 'Bandeira', 'Valor']
            if not all(col in df.columns for col in required_columns):
                st.error(f"Erro: O arquivo precisa conter as colunas: {', '.join(required_columns)}. Colunas encontradas: {', '.join(df.columns)}")
                st.stop()

            df_processed = df.copy()
            df_processed['Tipo'] = df_processed['Tipo'].astype(str).str.lower().str.strip().fillna('desconhecido')
            df_processed['Bandeira'] = df_processed['Bandeira'].astype(str).str.lower().str.strip().fillna('desconhecida')
            df_processed['Valor_Str'] = df_processed['Valor'].astype(str).str.strip()

            df_processed['Valor_Numeric'] = pd.to_numeric(
                df_processed['Valor_Str'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
                errors='coerce'
            )
            mask_failed = df_processed['Valor_Numeric'].isna()
            df_processed.loc[mask_failed, 'Valor_Numeric'] = pd.to_numeric(
                 df_processed.loc[mask_failed, 'Valor_Str'].str.replace(',', '', regex=False),
                 errors='coerce'
            )

            initial_rows = len(df_processed)
            df_processed.dropna(subset=['Valor_Numeric'], inplace=True)
            dropped_rows = initial_rows - len(df_processed)
            if dropped_rows > 0:
                 st.warning(f"{dropped_rows} linhas foram removidas por não conterem um valor numérico válido na coluna 'Valor'.")

            if 'Data' in df_processed.columns:
                try:
                     df_processed['Data'] = pd.to_datetime(df_processed['Data'], errors='coerce', dayfirst=True)
                     if df_processed['Data'].isnull().all():
                           df_processed['Data'] = pd.to_datetime(df_processed['Data'], errors='coerce')
                     df_processed.dropna(subset=['Data'], inplace=True)
                except Exception as e:
                     st.warning(f"Não foi possível converter a coluna 'Data' completamente. Erro: {e}")
            if 'Hora' in df_processed.columns:
                 df_processed['Hora'] = df_processed['Hora'].astype(str).str.strip()


            df_processed['Categoria'] = df_processed['Tipo'] + ' ' + df_processed['Bandeira']
            categorias_desejadas = {
                'crédito à vista elo': 'Crédito Elo', 'credito a vista elo': 'Crédito Elo', 'crédito elo': 'Crédito Elo',
                'crédito à vista mastercard': 'Crédito MasterCard', 'credito a vista mastercard': 'Crédito MasterCard','crédito mastercard': 'Crédito MasterCard',
                'crédito à vista visa': 'Crédito Visa', 'credito a vista visa': 'Crédito Visa','crédito visa': 'Crédito Visa',
                'débito elo': 'Débito Elo',
                'débito mastercard': 'Débito MasterCard',
                'débito visa': 'Débito Visa',
                'pix desconhecida': 'PIX', 'pix ': 'PIX', 'pix': 'PIX'
            }
            df_processed['Forma Nomeada'] = df_processed['Categoria'].map(categorias_desejadas).fillna(
                df_processed['Tipo'].map({'pix': 'PIX'})
            )

            df_filtered = df_processed.dropna(subset=['Forma Nomeada']).copy()

            if df_filtered.empty:
                st.warning("Nenhuma transação encontrada para as formas de pagamento mapeadas (Débito/Crédito Visa/Master/Elo, PIX). Verifique os dados no arquivo.")
                st.dataframe(df_processed[['Tipo', 'Bandeira', 'Valor', 'Categoria']].head(20))
                st.stop()

            vendas = df_filtered.groupby('Forma Nomeada')['Valor_Numeric'].sum()

            # (Definição dos Cardápios mantida como na versão anterior)
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
                st.error("Erro fatal ao carregar cardápios a partir do código. Verifique os dados e o formato 'Nome R$ Preço'.")
                st.stop()
            if "Cebola" not in sanduiches_precos:
                st.warning("Item 'Cebola R$ 0.50' não encontrado no cardápio de sanduíches. A função de ajuste com cebolas pode não funcionar.")


            # Abas de resultados
            tab1, tab2, tab3 = st.tabs(["📈 Resumo das Vendas", "🧩 Detalhes das Combinações", "📄 Dados Processados"])

            with tab1:
                # (Conteúdo da Tab1 mantido como na versão anterior)
                st.header("📈 Resumo das Vendas")
                st.subheader("Vendas Totais por Forma de Pagamento")
                if not vendas.empty:
                    df_vendas = vendas.reset_index()
                    df_vendas.columns = ['Forma de Pagamento', 'Valor Total']
                    df_vendas['Valor Formatado'] = df_vendas['Valor Total'].apply(format_currency)
                    plot_payment_methods(df_filtered)
                    st.dataframe(df_vendas[['Forma de Pagamento', 'Valor Formatado']].sort_values('Valor Total', ascending=False), use_container_width=True)
                else:
                    st.warning("Nenhum dado de venda para exibir.")

                if 'Data' in df_filtered.columns:
                    st.subheader("Vendas Diárias")
                    plot_daily_sales(df_filtered.copy())

                if 'Hora' in df_filtered.columns:
                    st.subheader("Vendas por Hora do Dia")
                    plot_hourly_sales(df_filtered.copy())

                if 'Data' in df_filtered.columns and 'Hora' in df_filtered.columns:
                     try:
                         st.subheader("Heatmap de Vendas (Dia da Semana x Hora)")
                         df_heatmap = df_filtered.copy()
                         df_heatmap['Data'] = pd.to_datetime(df_heatmap['Data'], errors='coerce')
                         df_heatmap.dropna(subset=['Data'], inplace=True)

                         df_heatmap['Dia da Semana'] = df_heatmap['Data'].dt.day_name()
                         df_heatmap['Hora_Num'] = pd.to_datetime(df_heatmap['Hora'], errors='coerce').dt.hour
                         if df_heatmap['Hora_Num'].isnull().all():
                             df_heatmap['Hora_Num'] = pd.to_datetime(df_heatmap['Hora'], format='%H:%M', errors='coerce').dt.hour
                         df_heatmap.dropna(subset=['Hora_Num'], inplace=True)
                         df_heatmap['Hora_Num'] = df_heatmap['Hora_Num'].astype(int)

                         if not df_heatmap.empty:
                              heatmap_data = df_heatmap.pivot_table(
                                   index='Dia da Semana', columns='Hora_Num', values='Valor_Numeric',
                                   aggfunc='sum', fill_value=0
                              )
                              dias_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                              dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'] # Abrev.
                              mapa_dias = dict(zip(dias_en, dias_pt))
                              heatmap_data = heatmap_data.reindex(dias_en).rename(index=mapa_dias)
                              heatmap_data = heatmap_data.reindex(columns=range(24), fill_value=0)

                              if not heatmap_data.empty and heatmap_data.values.any(): # Checa se tem valores não-zero
                                   fig, ax = plt.subplots(figsize=(14, 7))
                                   sns.heatmap(heatmap_data, cmap='YlGnBu', ax=ax, linewidths=.5, annot=False) # Annot=False
                                   ax.set_title('Vendas por Dia da Semana e Hora')
                                   ax.set_xlabel('Hora do Dia')
                                   ax.set_ylabel('Dia da Semana')
                                   plt.xticks(rotation=0)
                                   plt.yticks(rotation=0)
                                   st.pyplot(fig)
                              else:
                                  st.info("Não há dados de vendas suficientes agregados por dia/hora para gerar o heatmap.")
                         else:
                              st.info("Não há dados suficientes (com data e hora válidas) para gerar o heatmap.")
                     except Exception as e:
                         st.warning(f"Não foi possível gerar o heatmap: {str(e)}")


            with tab2:
                st.header("🧩 Detalhes das Combinações Geradas")
                st.caption(f"Alocação: {drink_percentage}% bebidas | {sandwich_percentage}% sanduíches") # Removido num_reinicializacoes

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

                    st.markdown(f"--- \n ### {forma} (Meta Total: {format_currency(total_pagamento)})")
                    # O spinner agora reflete a busca única
                    with st.spinner(f"Calculando combinação para {forma}..."):
                        target_bebidas = round_to_50_or_00(total_pagamento * (drink_percentage / 100.0))
                        target_sanduiches = round_to_50_or_00(total_pagamento - target_bebidas)

                        # ===== CHAMADA DA FUNÇÃO DE BUSCA (agora com a nova lógica) =====
                        # A função retorna quantidades float entre 1 e 75
                        comb_bebidas_float = local_search_optimization(
                            bebidas_precos, target_bebidas, tamanho_combinacao_bebidas, max_iterations
                        )
                        comb_sanduiches_float = local_search_optimization(
                            sanduiches_precos, target_sanduiches, tamanho_combinacao_sanduiches, max_iterations
                        )
                        # =================================================================

                        # ---- PÓS-PROCESSAMENTO ----
                        # Arredonda as quantidades float para inteiros APÓS a busca terminar
                        # Itens com quantidade < 0.5 serão arredondados para 0 e removidos
                        comb_bebidas_rounded = {name: round(qty) for name, qty in comb_bebidas_float.items() if round(qty) > 0}
                        comb_sanduiches_rounded = {name: round(qty) for name, qty in comb_sanduiches_float.items() if round(qty) > 0}

                        # Aplica ajuste com cebolas (usa quantidades já arredondadas)
                        comb_sanduiches_final, total_sanduiches_calc = adjust_with_onions(
                             comb_sanduiches_rounded.copy(),
                             sanduiches_precos,
                             target_sanduiches
                        )
                        # Calcula totais com base nas quantidades arredondadas/ajustadas
                        total_bebidas_calc = calculate_combination_value(comb_bebidas_rounded, bebidas_precos)
                        total_geral_calc = total_bebidas_calc + total_sanduiches_calc
                        # ---- FIM PÓS-PROCESSAMENTO ----

                    # (Exibição dos resultados mantida como na versão anterior)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader(f"🍹 Bebidas (Meta: {format_currency(target_bebidas)})")
                        if comb_bebidas_rounded:
                            for nome, qtt in sorted(comb_bebidas_rounded.items()):
                                val_item = bebidas_precos.get(nome, 0) * qtt
                                st.markdown(f"- **{qtt}x** {nome}: {format_currency(val_item)}")
                            st.divider()
                            st.metric("Subtotal Bebidas", format_currency(total_bebidas_calc))
                        else:
                            st.info("Nenhuma bebida na combinação final.")

                    with col2:
                        st.subheader(f"🍔 Sanduíches (Meta: {format_currency(target_sanduiches)})")
                        if comb_sanduiches_final:
                            onions_before_adjust = comb_sanduiches_rounded.get("Cebola", 0)
                            onions_after_adjust = comb_sanduiches_final.get("Cebola", 0)
                            onion_adjusted = onions_after_adjust > onions_before_adjust

                            for nome, qtt in sorted(comb_sanduiches_final.items()):
                                display_name = nome
                                prefix = ""
                                if nome == "Cebola" and onion_adjusted and qtt == onions_after_adjust:
                                     prefix = "🔹 "

                                val_item = sanduiches_precos.get(nome, 0) * qtt
                                st.markdown(f"- {prefix}**{qtt}x** {display_name}: {format_currency(val_item)}")

                            st.divider()
                            st.metric("Subtotal Sanduíches", format_currency(total_sanduiches_calc))
                            if onion_adjusted:
                                st.caption(f"🔹 Inclui {onions_after_adjust - onions_before_adjust} Cebola(s) adicionada(s) para ajuste.")
                        else:
                            st.info("Nenhum sanduíche na combinação final.")

                    st.divider()
                    diff = total_geral_calc - total_pagamento
                    st.metric(
                        "💰 TOTAL GERAL (Calculado)",
                        format_currency(total_geral_calc),
                        delta=f"{format_currency(diff)} vs Meta ({format_currency(total_pagamento)})",
                        delta_color="off" if abs(diff) < 0.01 else ("inverse" if diff > 0 else "normal")
                    )


            with tab3:
                # (Conteúdo da Tab3 mantido como na versão anterior)
                st.header("📄 Tabela de Dados Processados")
                st.markdown("Dados filtrados e usados para a análise e geração das combinações.")
                cols_base = ['Tipo', 'Bandeira', 'Valor_Str', 'Categoria', 'Forma Nomeada', 'Valor_Numeric']
                cols_to_show = []
                if 'Data' in df_filtered.columns: cols_to_show.append('Data')
                if 'Hora' in df_filtered.columns: cols_to_show.append('Hora')
                cols_to_show.extend([col for col in cols_base if col in df_filtered.columns])

                df_display = df_filtered[cols_to_show].copy()
                if 'Valor_Numeric' in df_display.columns:
                     df_display['Valor Formatado'] = df_display['Valor_Numeric'].apply(format_currency)
                     if 'Valor_Str' in df_display.columns:
                           cols_final_display = list(df_display.columns)
                           cols_final_display.remove('Valor Formatado')
                           idx = cols_final_display.index('Valor_Str')
                           cols_final_display.insert(idx + 1, 'Valor Formatado')
                           df_display = df_display[cols_final_display]


                st.dataframe(df_display, use_container_width=True)
                st.caption(f"Total de {len(df_filtered)} transações mapeadas e processadas.")


        except Exception as e:
            st.error(f"Ocorreu um erro inesperado durante o processamento: {str(e)}")
            import traceback
            st.exception(traceback.format_exc())
else:
    st.info("✨ Aguardando o envio do arquivo de transações para iniciar a análise...")
    # st.balloons() # Removido ou comentado se não desejar balões
