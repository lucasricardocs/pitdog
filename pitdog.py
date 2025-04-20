import streamlit as st
import pandas as pd
import random
import time

# ----- Funções Auxiliares Atualizadas -----
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
        combination[name] = round_to_50_or_00(random.uniform(1, 10))  # Valores iniciais menores e arredondados
    return combination

def adjust_with_onions(combination, item_prices, target_value):
    """
    Ajusta a combinação adicionando cebolas se o valor for menor que o target.
    Retorna a combinação modificada e o valor final.
    """
    current_value = calculate_combination_value(combination, item_prices)
    difference = target_value - current_value
    
    if difference <= 0 or "Cebola" not in item_prices:
        return combination, current_value
    
    onion_price = item_prices["Cebola"]
    num_onions = int(round(difference / onion_price))
    
    if num_onions > 0:
        combination["Cebola (Ajuste)"] = num_onions
    
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
    
    # Penaliza combinações que ultrapassam o target
    best_diff = abs(target_value - current_value) + (1000 if current_value > target_value else 0)

    current_items = list(best_combination.keys())

    for _ in range(max_iterations):
        if not current_items: break

        neighbor = best_combination.copy()
        item_to_modify = random.choice(current_items)

        # Modifica em incrementos de 0.50
        change = random.choice([-0.50, 0.50, -1.00, 1.00])
        neighbor[item_to_modify] = round_to_50_or_00(neighbor[item_to_modify] + change)
        neighbor[item_to_modify] = max(0.50, neighbor[item_to_modify])  # Mínimo 0.50 (1 cebola)

        neighbor_value = calculate_combination_value(neighbor, item_prices)
        
        # Penaliza vizinhos que ultrapassam o target
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

# ----- Interface Streamlit (Mantida como original) -----
st.set_page_config(page_title="Análise de Vendas & Combinações", layout="wide", initial_sidebar_state="expanded")

# [Restante do código da interface permanece EXATAMENTE IGUAL até a parte de processamento do arquivo]

    # --- Display dos Resultados em Abas ---
    tab1, tab2, tab3 = st.tabs(["📈 Resumo das Vendas", "🧩 Detalhes das Combinações", "📄 Dados Processados"])

    # [Código da tab1 e tab3 permanece EXATAMENTE IGUAL]

    with tab2:
        st.header("🧩 Detalhes das Combinações Geradas")
        st.caption(f"Tentando alocar {drink_percentage}% para bebidas e {sandwich_percentage}% para sanduíches.")

        ordem_formas = [
            'Débito Visa', 'Débito MasterCard', 'Débito Elo',
            'Crédito Visa', 'Crédito MasterCard', 'Crédito Elo', 'PIX'
        ]
        vendas_ordenadas = {forma: vendas[forma] for forma in ordem_formas if forma in vendas}
        for forma, total in vendas.items():
            if forma not in vendas_ordenadas: 
                vendas_ordenadas[forma] = total

        for forma, total_pagamento in vendas_ordenadas.items():
             if total_pagamento <= 0: continue

             with st.spinner(f"Gerando combinação para {forma}..."):
                 target_bebidas = round_to_50_or_00(total_pagamento * (drink_percentage / 100.0))
                 target_sanduiches = round_to_50_or_00(total_pagamento - target_bebidas)

                 # Otimização separada para bebidas e sanduíches
                 comb_bebidas = local_search_optimization(
                     bebidas_precos, target_bebidas, tamanho_combinacao_bebidas, max_iterations
                 )
                 comb_sanduiches = local_search_optimization(
                     sanduiches_precos, target_sanduiches, tamanho_combinacao_sanduiches, max_iterations
                 )

                 # Arredonda quantidades para inteiros
                 comb_bebidas_rounded = {name: round(qty) for name, qty in comb_bebidas.items() if round(qty) > 0}
                 comb_sanduiches_rounded = {name: round(qty) for name, qty in comb_sanduiches.items() if round(qty) > 0}

                 # Ajusta com cebolas se necessário (apenas para sanduíches)
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
                         for nome, qtt in comb_sanduiches_final.items():
                             prefix = "🔹 " if "Cebola" in nome else ""
                             val_item = sanduiches_precos[nome] * qtt
                             st.markdown(f"- {prefix}**{qtt}** **{nome}:** {format_currency(val_item)}")
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

# [Restante do código permanece EXATAMENTE IGUAL]
