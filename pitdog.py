import streamlit as st
import pandas as pd
import random
import time
from typing import Dict, Tuple

# ================== FUNÇÕES AUXILIARES ==================
def parse_menu_string(menu_data_string: str) -> Dict[str, float]:
    """Converte string do cardápio para dicionário {item: preço}"""
    menu = {}
    for line in menu_data_string.strip().split("\n"):
        if "R$" not in line:
            continue
        try:
            name, price = line.split("R$")
            name = name.strip()
            price = float(price.strip().replace(",", "."))
            menu[name] = price
        except (ValueError, IndexError):
            st.warning(f"Ignorando linha inválida: '{line}'")
    return menu

def calculate_combination_value(combination: Dict[str, float], item_prices: Dict[str, float]) -> float:
    """Calcula o valor total de uma combinação"""
    return sum(item_prices.get(name, 0) * qty for name, qty in combination.items())

def round_to_50_or_00(value: float) -> float:
    """Arredonda para o múltiplo de 0.50 mais próximo"""
    return round(value * 2) / 2

def generate_initial_combination(item_prices: Dict[str, float], max_items: int) -> Dict[str, float]:
    """Gera combinação inicial aleatória"""
    items = list(item_prices.keys())
    if not items:
        return {}
    
    chosen = random.sample(items, min(max_items, len(items)))
    return {item: round_to_50_or_00(random.uniform(1, 10)) for item in chosen}

def adjust_with_onions(combination: Dict[str, float], item_prices: Dict[str, float], target: float) -> Tuple[Dict[str, float], float]:
    """Completa com cebolas se necessário (apenas para sanduíches)"""
    current = calculate_combination_value(combination, item_prices)
    if current >= target or "Cebola" not in item_prices:
        return combination, current
    
    onion_price = item_prices["Cebola"]
    needed = round((target - current) / onion_price, 0)
    if needed > 0:
        combination["Cebola (Ajuste)"] = int(needed)
    
    final = calculate_combination_value(combination, item_prices)
    return combination, final

def adjust_combinations(
    drinks: Dict[str, float], 
    sandwiches: Dict[str, float], 
    target: float,
    drink_prices: Dict[str, float], 
    sandwich_prices: Dict[str, float]
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Ajusta as combinações para:
    1. Nunca ultrapassar o valor total
    2. Manter proporção original
    3. Completar com cebolas se necessário
    """
    # Calcula valores atuais
    drink_value = calculate_combination_value(drinks, drink_prices)
    sandwich_value = calculate_combination_value(sandwiches, sandwich_prices)
    total = drink_value + sandwich_value
    
    # Função para reduzir combinação
    def reduce_combination(comb: Dict[str, float], prices: Dict[str, float], amount: float) -> Dict[str, float]:
        remaining = amount
        while remaining > 0 and comb:
            # Remove do mais caro primeiro
            item = max(comb.items(), key=lambda x: prices[x[0]])[0]
            item_price = prices[item]
            
            if comb[item] > 1 and item_price <= remaining:
                qty_to_remove = min(int(remaining // item_price), comb[item] - 1)
                comb[item] -= qty_to_remove
                remaining -= qty_to_remove * item_price
            else:
                remaining -= prices[item] * comb[item]
                del comb[item]
        return comb
    
    # Se ultrapassou, reduz primeiro sanduíches
    if total > target:
        excess = total - target
        sandwiches = reduce_combination(sandwiches, sandwich_prices, excess)
        total = calculate_combination_value(drinks, drink_prices) + calculate_combination_value(sandwiches, sandwich_prices)
        
        # Caso raro: se ainda estiver acima, reduz bebidas
        if total > target:
            drinks = reduce_combination(drinks, drink_prices, total - target)
    
    # Completa com cebolas se necessário
    sandwiches, _ = adjust_with_onions(sandwiches, sandwich_prices, target - calculate_combination_value(drinks, drink_prices))
    
    return drinks, sandwiches

def format_currency(value: float) -> str:
    """Formata valor como moeda BR"""
    try:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ --"

# ================== INTERFACE STREAMLIT ==================
st.set_page_config(page_title="Otimizador de Combinações", layout="wide")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    drink_perc = st.slider("% para Bebidas", 0, 100, 30)
    max_drink_types = st.slider("Tipos de Bebidas", 1, 10, 4)
    max_sandwich_types = st.slider("Tipos de Sanduíches", 1, 10, 5)
    iterations = st.select_slider("Iterações", [1000, 5000, 10000, 20000], 10000)

# Cardápios fixos
bebidas = parse_menu_string("""
Suco R$ 10,00
Creme R$ 15,00
Refri Lata R$ 7,00
Refri 1L R$ 10,00
Água R$ 3,00
""")

sanduiches = parse_menu_string("""
X Salada R$ 18,00
X Bacon R$ 22,00
X Frango R$ 24,00
X Tudo R$ 30,00
Cebola R$ 0.50
""")

# Upload de arquivo
upload = st.file_uploader("📤 Upload de Transações", type=["csv", "xlsx"])
if upload:
    try:
        # Processamento do arquivo
        if upload.name.endswith(".csv"):
            df = pd.read_csv(upload, sep=";", decimal=",")
        else:
            df = pd.read_excel(upload)
        
        # Pré-processamento
        df["Valor"] = pd.to_numeric(df["Valor"].astype(str).str.replace(".", "").str.replace(",", "."))
        totals = df.groupby("FormaPagamento")["Valor"].sum()
        
        # Otimização para cada forma de pagamento
        for forma, total in totals.items():
            with st.expander(f"{forma} (Total: {format_currency(total)})"):
                # Define targets
                target_bebidas = round_to_50_or_00(total * drink_perc / 100)
                target_sanduiches = round_to_50_or_00(total - target_bebidas)
                
                # Gera combinações
                comb_bebidas = generate_initial_combination(bebidas, max_drink_types)
                comb_sanduiches = generate_initial_combination(sanduiches, max_sandwich_types)
                
                # Otimização local
                for _ in range(iterations):
                    # ... (implementação da busca local como anteriormente)
                    pass
                
                # Ajuste final
                comb_bebidas, comb_sanduiches = adjust_combinations(
                    comb_bebidas, comb_sanduiches, total, bebidas, sanduiches
                )
                
                # Exibição
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🍹 Bebidas")
                    for item, qty in comb_bebidas.items():
                        st.write(f"- {qty:.0f}x {item}: {format_currency(bebidas[item] * qty)}")
                    st.metric("Total", format_currency(calculate_combination_value(comb_bebidas, bebidas)))
                
                with col2:
                    st.subheader("🍔 Sanduíches")
                    for item, qty in comb_sanduiches.items():
                        st.write(f"- {qty:.0f}x {item}: {format_currency(sanduiches[item] * qty)}")
                    st.metric("Total", format_currency(calculate_combination_value(comb_sanduiches, sanduiches))))
                
                st.metric("TOTAL GERAL", format_currency(calculate_combination_value(comb_bebidas, bebidas) + calculate_combination_value(comb_sanduiches, sanduiches)))
    
    except Exception as e:
        st.error(f"Erro: {str(e)}")
else:
    st.info("Faça upload do arquivo para iniciar")
