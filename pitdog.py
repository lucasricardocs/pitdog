# -*- coding: utf-8 -*-
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
        # Usar rsplit para garantir que pegamos o último R$
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
    return sum(item_prices.get(name, 0) * quantity for name, quantity in combination.items())

def round_to_50_or_00(value):
    """Arredonda para o múltiplo de 0.50 mais próximo"""
    # Adiciona uma pequena tolerância para evitar problemas de ponto flutuante
    tolerance = 1e-9
    return round((value + tolerance) * 2) / 2

def generate_initial_combination(item_prices, combination_size):
    """Generates a random initial combination for the local search."""
    combination = {}
    item_names = list(item_prices.keys())
    if not item_names:
        return combination
    # Garante que não tentamos pegar mais itens do que os disponíveis
    size = min(combination_size, len(item_names))
    if size <= 0:
        return combination
    chosen_names = random.sample(item_names, size)
    for name in chosen_names:
        # Gera quantidade inicial e arredonda
        combination[name] = round_to_50_or_00(random.uniform(0.5, 10)) # Garante mínimo de 0.5
        if combination[name] == 0: # Segurança extra se arredondar para 0
             combination[name] = 0.50
    return combination

def adjust_with_onions(combination, item_prices, target_value):
    """
    Ajusta a combinação adicionando cebolas se o valor for menor que o target.
    Retorna a combinação modificada e o valor final.
    Limita a quantidade máxima de cebolas a 20 unidades.
    """
    current_value = calculate_combination_value(combination, item_prices)
    difference = target_value - current_value

    # Só ajusta se a diferença for positiva e Cebola existir no cardápio
    if difference <= 0 or "Cebola" not in item_prices or item_prices["Cebola"] <= 0:
        return combination, current_value

    onion_price = item_prices["Cebola"]
    # Calcula quantas cebolas caberiam na diferença, arredondando para baixo (int)
    # e limitando a 20 no total
    num_onions_to_add = max(0, int(difference // onion_price)) # Usar divisão inteira

    current_onions = combination.get("Cebola", 0)
    max_possible_onions = 20

    # Limita a adição ao máximo de 20 cebolas no total
    if current_onions + num_onions_to_add > max_possible_onions:
        num_onions_to_add = max_possible_onions - current_onions

    if num_onions_to_add > 0:
        combination["Cebola"] = current_onions + num_onions_to_add

    final_value = calculate_combination_value(combination, item_prices)
    return combination, final_value

def local_search_optimization(item_prices, target_value, combination_size, max_iterations):
    """
    Versão modificada para:
    - Valores terminarem em ,00 ou ,50
    - Nunca ultrapassar o target_value (minimiza a penalidade se ultrapassar)
    """
    if not item_prices or target_value <= 0:
        return {}

    best_combination = generate_initial_combination(item_prices, combination_size)
    # Assegura que a combinação inicial tem valores arredondados
    best_combination = {k: round_to_50_or_00(v) for k, v in best_combination.items() if round_to_50_or_00(v) > 0}

    # Se a combinação inicial ficar vazia após arredondamento, retorna vazia
    if not best_combination:
        return {}

    current_value = calculate_combination_value(best_combination, item_prices)

    # Penalidade alta se o valor atual exceder o alvo
    penalty = 1000 if current_value > target_value else 0
    best_score = abs(target_value - current_value) + penalty # Score: menor é melhor

    start_time = time.time()

    for i in range(max_iterations):
        # Otimização: Sair cedo se o tempo estiver acabando (ex: 5 segundos por busca)
        # if time.time() - start_time > 5:
        #     break

        current_items = list(best_combination.keys())
        if not current_items: break # Se a combinação ficar vazia

        neighbor = best_combination.copy()
        item_to_modify = random.choice(current_items)

        # Tenta adicionar ou remover 0.50 ou 1.00
        change = random.choice([-1.00, -0.50, 0.50, 1.00])
        neighbor[item_to_modify] = neighbor.get(item_to_modify, 0) + change
        neighbor[item_to_modify] = round_to_50_or_00(neighbor[item_to_modify]) # Arredonda após mudança

        # Remove o item se a quantidade for 0 ou menos, senão garante mínimo de 0.50
        if neighbor[item_to_modify] <= 0:
            del neighbor[item_to_modify]
            # Se o vizinho ficou vazio, pule esta iteração
            if not neighbor:
                 continue
        # else: # Já garantido pelo arredondamento para 0.50
        #     neighbor[item_to_modify] = max(0.50, neighbor[item_to_modify])


        neighbor_value = calculate_combination_value(neighbor, item_prices)
        neighbor_penalty = 1000 if neighbor_value > target_value else 0
        neighbor_score = abs(target_value - neighbor_value) + neighbor_penalty

        # Aceita o vizinho se o score for melhor
        if neighbor_score < best_score:
            best_score = neighbor_score
            best_combination = neighbor
            # Otimização: Se encontrar valor exato, pode parar mais cedo?
            # if best_score < 1e-6: # Quase zero e sem penalidade
            #    break

    # Filtra itens com quantidade zero que possam ter restado (embora a lógica acima deva remover)
    best_combination = {k: v for k, v in best_combination.items() if v > 0}
    return best_combination

# ===== NOVA FUNÇÃO: Wrapper para Múltiplas Reinicializações =====
def busca_local_com_reinicializacoes(item_prices, target_value, combination_size, max_iterations, num_reinicializacoes):
    """
    Executa a 'local_search_optimization' várias vezes e retorna a melhor solução.
    """
    melhor_combinacao_global = {}
    melhor_score_global = float('inf') # Score: menor é melhor

    if not item_prices or target_value <= 0:
        return {}

    for _ in range(num_reinicializacoes):
        # Chama a função de busca local original
        combinacao_atual = local_search_optimization(
            item_prices, target_value, combination_size, max_iterations
        )

        # Avalia a combinação encontrada nesta tentativa
        if combinacao_atual: # Verifica se a busca retornou algo
            valor_atual = calculate_combination_value(combinacao_atual, item_prices)
            penalidade_atual = 1000 if valor_atual > target_value else 0
            score_atual = abs(target_value - valor_atual) + penalidade_atual

            # Se esta tentativa foi melhor que a melhor global encontrada até agora
            if score_atual < melhor_score_global:
                melhor_score_global = score_atual
                melhor_combinacao_global = combinacao_atual
                # Opcional: Critério de parada se solução "perfeita" for encontrada
                if melhor_score_global < 1e-6: # Diferença muito pequena e sem penalidade
                    break
        # else: lida com caso onde a busca original pode retornar {} se falhar na inicialização

    return melhor_combinacao_global
# ===============================================================

def format_currency(value):
    """Formats a number as Brazilian Real currency."""
    if pd.isna(value) or value is None: # Adicionado check para None
        return "R$ -"
    try:
        # Garante que é float antes de formatar
        float_value = float(value)
        # Formatação padrão brasileira
        return f"R$ {float_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ Inválido"

# --- Funções de Plotagem (sem alterações) ---
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
        st.info("Coluna 'Hora' não encontrada para gerar gráfico de vendas por hora.")
        return
    try:
        # Tenta converter diferentes formatos de hora
        df['Hora_Num'] = pd.to_datetime(df['Hora'], errors='coerce').dt.hour
        # Se falhar, tenta outro formato comum
        if df['Hora_Num'].isnull().all():
             df['Hora_Num'] = pd.to_datetime(df['Hora'], format='%H:%M', errors='coerce').dt.hour

        df.dropna(subset=['Hora_Num'], inplace=True)
        if df.empty: return

        hourly_sales = df.groupby('Hora_Num')['Valor_Numeric'].sum()
        hourly_sales = hourly_sales.reindex(range(24), fill_value=0) # Garante todas as horas no eixo
        if hourly_sales.empty: return

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
        options=[1000, 5000, 10000, 20000, 50000],
        value=10000,
        help="Número de tentativas de melhoria para cada combinação individual."
    )
    # ===== NOVO CONTROLE NA SIDEBAR =====
    num_reinicializacoes = st.select_slider(
         "Número de Tentativas (Reinicializações) 🔄",
         options=[1, 3, 5, 10, 20, 50],
         value=5, # Valor padrão
         help="Quantas vezes a busca será reiniciada para tentar encontrar uma solução melhor."
    )
    # ===================================
    st.info("Lembre-se: As combinações são aproximações heurísticas.")

# --- File Upload ---
arquivo = st.file_uploader("📤 Envie o arquivo de transações (.csv ou .xlsx)", type=["csv", "xlsx"])

if arquivo:
    with st.spinner(f'Processando "{arquivo.name}"...'):
        try:
            if arquivo.name.endswith(".csv"):
                # Tenta diferentes separadores e encodings comuns
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

            # Processamento dos dados (com mais robustez)
            required_columns = ['Tipo', 'Bandeira', 'Valor']
            if not all(col in df.columns for col in required_columns):
                st.error(f"Erro: O arquivo precisa conter as colunas: {', '.join(required_columns)}. Colunas encontradas: {', '.join(df.columns)}")
                st.stop()

            df_processed = df.copy()
            # Limpeza e padronização
            df_processed['Tipo'] = df_processed['Tipo'].astype(str).str.lower().str.strip().fillna('desconhecido')
            df_processed['Bandeira'] = df_processed['Bandeira'].astype(str).str.lower().str.strip().fillna('desconhecida')
            df_processed['Valor_Str'] = df_processed['Valor'].astype(str).str.strip()

            # Conversão de valor mais robusta
            df_processed['Valor_Numeric'] = pd.to_numeric(
                df_processed['Valor_Str'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
                errors='coerce'
            )
            # Tentar formato alternativo se falhar (ex: 1,234.56)
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

            # Coluna de Data (se existir)
            if 'Data' in df_processed.columns:
                try:
                     # Tenta formatos comuns de data
                     df_processed['Data'] = pd.to_datetime(df_processed['Data'], errors='coerce', dayfirst=True) # Tenta DD/MM/YYYY primeiro
                     if df_processed['Data'].isnull().all():
                           df_processed['Data'] = pd.to_datetime(df_processed['Data'], errors='coerce') # Tenta formato padrão
                     df_processed.dropna(subset=['Data'], inplace=True) # Remove linhas onde data não pôde ser convertida
                except Exception as e:
                     st.warning(f"Não foi possível converter a coluna 'Data' completamente. Erro: {e}")
            # Coluna de Hora (se existir)
            if 'Hora' in df_processed.columns:
                 df_processed['Hora'] = df_processed['Hora'].astype(str).str.strip() # Garante que é string


            # Mapeamento de Categorias (mantido como estava)
            df_processed['Categoria'] = df_processed['Tipo'] + ' ' + df_processed['Bandeira']
            categorias_desejadas = {
                'crédito à vista elo': 'Crédito Elo', 'credito a vista elo': 'Crédito Elo', 'crédito elo': 'Crédito Elo',
                'crédito à vista mastercard': 'Crédito MasterCard', 'credito a vista mastercard': 'Crédito MasterCard','crédito mastercard': 'Crédito MasterCard',
                'crédito à vista visa': 'Crédito Visa', 'credito a vista visa': 'Crédito Visa','crédito visa': 'Crédito Visa',
                'débito elo': 'Débito Elo',
                'débito mastercard': 'Débito MasterCard',
                'débito visa': 'Débito Visa',
                'pix desconhecida': 'PIX', 'pix ': 'PIX', 'pix': 'PIX' # Mais flexível para PIX
            }
            # Aplica mapeamento mais robusto
            df_processed['Forma Nomeada'] = df_processed['Categoria'].map(categorias_desejadas).fillna(
                df_processed['Tipo'].map({'pix': 'PIX'}) # Tenta mapear PIX apenas pelo tipo também
            )

            # Filtra apenas as transações mapeadas
            df_filtered = df_processed.dropna(subset=['Forma Nomeada']).copy()

            if df_filtered.empty:
                st.warning("Nenhuma transação encontrada para as formas de pagamento mapeadas (Débito/Crédito Visa/Master/Elo, PIX). Verifique os dados no arquivo.")
                st.dataframe(df_processed[['Tipo', 'Bandeira', 'Valor', 'Categoria']].head(20)) # Mostra exemplos do que não foi mapeado
                st.stop()

            # Agrupa as vendas
            vendas = df_filtered.groupby('Forma Nomeada')['Valor_Numeric'].sum()

            # Definição dos Cardápios (Parse robusto)
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
                st.header("📈 Resumo das Vendas")

                # Gráfico de vendas por forma de pagamento
                st.subheader("Vendas Totais por Forma de Pagamento")
                if not vendas.empty:
                    df_vendas = vendas.reset_index()
                    df_vendas.columns = ['Forma de Pagamento', 'Valor Total']
                    df_vendas['Valor Formatado'] = df_vendas['Valor Total'].apply(format_currency)
                    # Usar plot_payment_methods que já formata o eixo Y
                    plot_payment_methods(df_filtered) # Passar o dataframe filtrado
                    st.dataframe(df_vendas[['Forma de Pagamento', 'Valor Formatado']].sort_values('Valor Total', ascending=False), use_container_width=True)
                else:
                    st.warning("Nenhum dado de venda para exibir.")

                # Gráficos adicionais (chamando as funções já existentes)
                if 'Data' in df_filtered.columns:
                    st.subheader("Vendas Diárias")
                    plot_daily_sales(df_filtered.copy()) # Passa cópia para evitar SettingWithCopyWarning

                if 'Hora' in df_filtered.columns:
                    st.subheader("Vendas por Hora do Dia")
                    plot_hourly_sales(df_filtered.copy()) # Passa cópia

                # Heatmap (mantido como estava)
                if 'Data' in df_filtered.columns and 'Hora' in df_filtered.columns:
                     try:
                         st.subheader("Heatmap de Vendas (Dia da Semana x Hora)")
                         df_heatmap = df_filtered.copy() # Usar cópia
                         # Certificar que 'Data' é datetime
                         df_heatmap['Data'] = pd.to_datetime(df_heatmap['Data'], errors='coerce')
                         df_heatmap.dropna(subset=['Data'], inplace=True)

                         # Extrair dia da semana e hora
                         df_heatmap['Dia da Semana'] = df_heatmap['Data'].dt.day_name()
                         # Converter Hora para numérico (hora)
                         df_heatmap['Hora_Num'] = pd.to_datetime(df_heatmap['Hora'], errors='coerce').dt.hour
                         if df_heatmap['Hora_Num'].isnull().all():
                             df_heatmap['Hora_Num'] = pd.to_datetime(df_heatmap['Hora'], format='%H:%M', errors='coerce').dt.hour
                         df_heatmap.dropna(subset=['Hora_Num'], inplace=True)
                         df_heatmap['Hora_Num'] = df_heatmap['Hora_Num'].astype(int)

                         if not df_heatmap.empty:
                              heatmap_data = df_heatmap.pivot_table(
                                   index='Dia da Semana',
                                   columns='Hora_Num',
                                   values='Valor_Numeric',
                                   aggfunc='sum',
                                   fill_value=0
                              )

                              # Ordenar dias da semana e horas
                              dias_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                              dias_pt = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
                              mapa_dias = dict(zip(dias_en, dias_pt))
                              heatmap_data = heatmap_data.reindex(dias_en) # Reindexa pela ordem em inglês
                              heatmap_data.index = heatmap_data.index.map(mapa_dias) # Renomeia para português

                              heatmap_data = heatmap_data.reindex(columns=range(24), fill_value=0) # Garante todas as colunas de hora

                              if not heatmap_data.empty:
                                   fig, ax = plt.subplots(figsize=(14, 7)) # Aumentado
                                   sns.heatmap(heatmap_data, cmap='YlGnBu', ax=ax, linewidths=.5)
                                   ax.set_title('Vendas por Dia da Semana e Hora')
                                   ax.set_xlabel('Hora do Dia')
                                   ax.set_ylabel('Dia da Semana')
                                   plt.xticks(rotation=0)
                                   plt.yticks(rotation=0)
                                   st.pyplot(fig)
                              else:
                                  st.info("Não há dados suficientes para gerar o heatmap após o processamento.")
                         else:
                              st.info("Não há dados suficientes para gerar o heatmap após o processamento.")

                     except Exception as e:
                         st.warning(f"Não foi possível gerar o heatmap: {str(e)}")

            with tab2:
                st.header("🧩 Detalhes das Combinações Geradas")
                st.caption(f"Alocação: {drink_percentage}% bebidas | {sandwich_percentage}% sanduíches | Tentativas: {num_reinicializacoes}x") # Adicionado num_reinicializacoes

                # Ordenação das formas de pagamento para exibição consistente
                ordem_formas = [
                    'Débito Visa', 'Débito MasterCard', 'Débito Elo',
                    'Crédito Visa', 'Crédito MasterCard', 'Crédito Elo', 'PIX'
                ]
                # Cria dicionário ordenado com base nas vendas existentes
                vendas_ordenadas = {forma: vendas[forma] for forma in ordem_formas if forma in vendas}
                # Adiciona quaisquer outras formas que possam existir (menos comum com o mapeamento atual)
                for forma, total in vendas.items():
                    if forma not in vendas_ordenadas:
                        vendas_ordenadas[forma] = total

                # Itera sobre as vendas ordenadas
                for forma, total_pagamento in vendas_ordenadas.items():
                    if total_pagamento <= 0: # Pula formas sem vendas
                        continue

                    st.markdown(f"--- \n ### {forma} (Meta Total: {format_currency(total_pagamento)})")
                    with st.spinner(f"Calculando melhor combinação para {forma} com {num_reinicializacoes} tentativas..."):
                        # Calcula metas para bebidas e sanduíches, arredondando
                        target_bebidas = round_to_50_or_00(total_pagamento * (drink_percentage / 100.0))
                        # Garante que sanduíches recebam o restante para somar o total exato
                        target_sanduiches = round_to_50_or_00(total_pagamento - target_bebidas)

                        # ===== CHAMADA MODIFICADA para usar a função com reinicializações =====
                        comb_bebidas_raw = busca_local_com_reinicializacoes(
                            bebidas_precos, target_bebidas, tamanho_combinacao_bebidas, max_iterations, num_reinicializacoes
                        )
                        comb_sanduiches_raw = busca_local_com_reinicializacoes(
                            sanduiches_precos, target_sanduiches, tamanho_combinacao_sanduiches, max_iterations, num_reinicializacoes
                        )
                        # =====================================================================

                        # Arredonda quantidades para inteiros e filtra itens zerados
                        # Arredonda para o inteiro mais próximo, mas mantém itens > 0
                        comb_bebidas_rounded = {name: round(qty) for name, qty in comb_bebidas_raw.items() if round(qty) > 0}
                        comb_sanduiches_rounded = {name: round(qty) for name, qty in comb_sanduiches_raw.items() if round(qty) > 0}

                        # Aplica ajuste com cebolas na combinação de sanduíches já arredondada
                        comb_sanduiches_final, total_sanduiches_calc = adjust_with_onions(
                             comb_sanduiches_rounded.copy(), # Passa cópia para não modificar original
                             sanduiches_precos,
                             target_sanduiches
                        )
                        # Calcula o total das bebidas com quantidades arredondadas
                        total_bebidas_calc = calculate_combination_value(comb_bebidas_rounded, bebidas_precos)
                        # Calcula o total geral final
                        total_geral_calc = total_bebidas_calc + total_sanduiches_calc

                    # Exibe os resultados no Expander
                    # with st.expander(f"**{forma}** (Meta: {format_currency(total_pagamento)} | Calculado: {format_currency(total_geral_calc)})", expanded=False):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader(f"🍹 Bebidas (Meta: {format_currency(target_bebidas)})")
                        if comb_bebidas_rounded:
                            for nome, qtt in sorted(comb_bebidas_rounded.items()): # Ordena por nome
                                val_item = bebidas_precos.get(nome, 0) * qtt
                                st.markdown(f"- **{qtt}x** {nome}: {format_currency(val_item)}")
                            st.divider()
                            st.metric("Subtotal Bebidas", format_currency(total_bebidas_calc))
                        else:
                            st.info("Nenhuma bebida na combinação final.")

                    with col2:
                        st.subheader(f"🍔 Sanduíches (Meta: {format_currency(target_sanduiches)})")
                        if comb_sanduiches_final:
                            # Verifica se houve ajuste com cebola para destacar
                            onions_before_adjust = comb_sanduiches_rounded.get("Cebola", 0)
                            onions_after_adjust = comb_sanduiches_final.get("Cebola", 0)
                            onion_adjusted = onions_after_adjust > onions_before_adjust

                            for nome, qtt in sorted(comb_sanduiches_final.items()): # Ordena por nome
                                display_name = nome
                                prefix = ""
                                if nome == "Cebola" and onion_adjusted and qtt == onions_after_adjust:
                                     prefix = "🔹 " # Destaca se foi ajustado
                                     # display_name = f"Cebola (+{qtt - onions_before_adjust} ajuste)" # Ou algo assim

                                val_item = sanduiches_precos.get(nome, 0) * qtt
                                st.markdown(f"- {prefix}**{qtt}x** {display_name}: {format_currency(val_item)}")

                            st.divider()
                            st.metric("Subtotal Sanduíches", format_currency(total_sanduiches_calc))
                            if onion_adjusted:
                                st.caption(f"🔹 Inclui {onions_after_adjust - onions_before_adjust} Cebola(s) adicionada(s) para aproximar do valor meta.")
                        else:
                            st.info("Nenhum sanduíche na combinação final.")

                    st.divider()
                    diff = total_geral_calc - total_pagamento
                    st.metric(
                        "💰 TOTAL GERAL (Calculado)",
                        format_currency(total_geral_calc),
                        delta=f"{format_currency(diff)} vs Meta ({format_currency(total_pagamento)})",
                        delta_color="off" if abs(diff) < 0.01 else ("inverse" if diff > 0 else "normal") # Ajuste fino na cor do delta
                    )


            with tab3:
                st.header("📄 Tabela de Dados Processados")
                st.markdown("Dados filtrados e usados para a análise e geração das combinações.")
                # Define colunas a mostrar, verificando se existem
                cols_base = ['Tipo', 'Bandeira', 'Valor_Str', 'Categoria', 'Forma Nomeada', 'Valor_Numeric']
                cols_to_show = []
                if 'Data' in df_filtered.columns: cols_to_show.append('Data')
                if 'Hora' in df_filtered.columns: cols_to_show.append('Hora')
                cols_to_show.extend([col for col in cols_base if col in df_filtered.columns])

                # Formata a coluna de valor numérico para exibição
                df_display = df_filtered[cols_to_show].copy()
                if 'Valor_Numeric' in df_display.columns:
                     df_display['Valor Formatado'] = df_display['Valor_Numeric'].apply(format_currency)
                     # Reordena para colocar valor formatado perto do original
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
            st.exception(traceback.format_exc()) # Mostra traceback para debug
else:
    st.info("✨ Aguardando o envio do arquivo de transações para iniciar a análise...")
    st.balloons()
