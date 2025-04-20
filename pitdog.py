import streamlit as st
import pandas as pd
import random
import time
from typing import Dict, Tuple

# ----- Helper Functions -----
def parse_menu_string(menu_data_string: str) -> Dict[str, float]:
    """Parses menu items and prices from multi-line string"""
    menu = {}
    for line in menu_data_string.strip().split("\n"):
        if "R$" not in line:
            continue
        try:
            name_part, price_part = line.split("R$")
            name = name_part.strip()
            price = float(price_part.strip().replace(",", "."))
            menu[name] = price
        except (ValueError, IndexError):
            continue
    return menu

def calculate_combination_value(combination: Dict[str, float], prices: Dict[str, float]) -> float:
    """Calculates total value of a combination"""
    return sum(prices.get(name, 0) * qty for name, qty in combination.items())

def round_to_50_or_00(value: float) -> float:
    """Rounds to nearest .00 or .50"""
    return round(value * 2) / 2

def generate_initial_combination(prices: Dict[str, float], max_items: int) -> Dict[str, float]:
    """Generates random initial combination"""
    items = list(prices.keys())
    if not items:
        return {}
    selected = random.sample(items, min(max_items, len(items)))
    return {item: round_to_50_or_00(random.uniform(1, 10)) for item in selected}

def local_search_optimization(
    prices: Dict[str, float],
    target: float,
    max_items: int,
    max_iterations: int
) -> Dict[str, float]:
    """Optimizes combination to approximate target value"""
    current = generate_initial_combination(prices, max_items)
    if not current:
        return {}
    
    current_value = calculate_combination_value(current, prices)
    best = current.copy()
    best_diff = abs(target - current_value) + (1000 if current_value > target else 0)
    
    for _ in range(max_iterations):
        neighbor = current.copy()
        item = random.choice(list(neighbor.keys()))
        
        change = random.choice([-0.5, 0.5, -1.0, 1.0])
        neighbor[item] = max(0.5, round_to_50_or_00(neighbor[item] + change))
        
        neighbor_value = calculate_combination_value(neighbor, prices)
        neighbor_diff = abs(target - neighbor_value) + (1000 if neighbor_value > target else 0)

        if neighbor_diff < best_diff:
            best = neighbor
            best_diff = neighbor_diff
            
        if best_diff < 0.01:
            break
            
    return best

def adjust_with_onions(
    combination: Dict[str, float],
    prices: Dict[str, float],
    target: float
) -> Tuple[Dict[str, float], float]:
    """Adds onions if needed to reach target"""
    current = calculate_combination_value(combination, prices)
    if current >= target or "Cebola" not in prices:
        return combination, current
    
    diff = target - current
    num_onions = int(round(diff / prices["Cebola"]))
    
    if num_onions > 0:
        combination["Cebola"] = combination.get("Cebola", 0) + num_onions
    
    final = calculate_combination_value(combination, prices)
    return combination, final

def adjust_combinations(
    drinks: Dict[str, float],
    sandwiches: Dict[str, float],
    target_total: float,
    drink_prices: Dict[str, float],
    sandwich_prices: Dict[str, float]
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Ensures total doesn't exceed target"""
    total = calculate_combination_value(drinks, drink_prices) + calculate_combination_value(sandwiches, sandwich_prices)
    if total <= target_total:
        return drinks, sandwiches
    
    excess = total - target_total
    
    def reduce_comb(comb: Dict[str, float], prices: Dict[str, float], amount: float) -> Dict[str, float]:
        reduced = comb.copy()
        remaining = amount
        items_sorted = sorted(reduced.items(), key=lambda x: prices[x[0]], reverse=True)
        
        for item, qty in items_sorted:
            if remaining <= 0:
                break
            item_value = prices[item] * qty
            if item_value >= remaining:
                qty_to_remove = min(qty, int(remaining // prices[item]))
                if qty_to_remove > 0:
                    reduced[item] -= qty_to_remove
                    remaining -= prices[item] * qty_to_remove
            else:
                remaining -= item_value
                del reduced[item]
        return reduced
    
    sandwiches = reduce_comb(sandwiches, sandwich_prices, excess)
    total = calculate_combination_value(drinks, drink_prices) + calculate_combination_value(sandwiches, sandwich_prices)
    
    if total > target_total:
        drinks = reduce_comb(drinks, drink_prices, total - target_total)
    
    return drinks, sandwiches

def format_currency(value: float) -> str:
    """Formats as Brazilian currency"""
    try:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ --"

# ----- UI Configuration -----
st.set_page_config(page_title="Sales Analyzer", layout="wide")

# Menu Data
SANDWICHES = """
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

DRINKS = """
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

# Process menus
sandwich_prices = parse_menu_string(SANDWICHES)
drink_prices = parse_menu_string(DRINKS)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    drink_perc = st.slider("Drink Percentage", 0, 100, 30)
    max_drinks = st.slider("Max Drink Types", 1, 10, 4)
    max_sandwiches = st.slider("Max Sandwich Types", 1, 10, 5)
    iterations = st.select_slider("Optimization Quality", [1000, 5000, 10000, 20000], 5000)

# File Upload
upload = st.file_uploader("📤 Upload Sales File", type=["csv", "xlsx"])

if upload:
    try:
        if upload.name.endswith(".csv"):
            df = pd.read_csv(upload, sep=";", decimal=",")
        else:
            df = pd.read_excel(upload)
        
        # Preprocessing
        df["Valor"] = pd.to_numeric(
            df["Valor"].astype(str)
            .str.replace(".", "")
            .str.replace(",", ".")
        )
        
        if "FormaPagamento" not in df.columns or "Valor" not in df.columns:
            st.error("File must contain 'FormaPagamento' and 'Valor' columns")
            st.stop()
        
        sales = df.groupby("FormaPagamento")["Valor"].sum()
        
        for method, total in sales.items():
            with st.expander(f"{method} (Total: {format_currency(total)})"):
                drink_target = round_to_50_or_00(total * drink_perc / 100)
                sandwich_target = round_to_50_or_00(total - drink_target)
                
                with st.spinner(f"Optimizing {method}..."):
                    drinks = local_search_optimization(drink_prices, drink_target, max_drinks, iterations)
                    sandwiches = local_search_optimization(sandwich_prices, sandwich_target, max_sandwiches, iterations)
                    
                    # Round quantities
                    drinks = {k: round(v) for k, v in drinks.items() if round(v) > 0}
                    sandwiches = {k: round(v) for k, v in sandwiches.items() if round(v) > 0}
                    
                    # Ensure total doesn't exceed
                    drinks, sandwiches = adjust_combinations(drinks, sandwiches, total, drink_prices, sandwich_prices)
                    
                    # Add onions if needed
                    sandwiches, sandwich_total = adjust_with_onions(
                        sandwiches, sandwich_prices, total - calculate_combination_value(drinks, drink_prices)
                    )
                    drink_total = calculate_combination_value(drinks, drink_prices)
                    combined_total = drink_total + sandwich_total
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"🍹 Drinks (Target: {format_currency(drink_target)})")
                    if drinks:
                        for item, qty in drinks.items():
                            st.write(f"- {qty}x {item}: {format_currency(drink_prices[item] * qty)}")
                        st.metric("Drink Total", format_currency(drink_total))
                    else:
                        st.info("No drinks")
                
                with col2:
                    st.subheader(f"🍔 Sandwiches (Target: {format_currency(sandwich_target)})")
                    if sandwiches:
                        has_adjustment = "Cebola" in sandwiches and sandwiches["Cebola"] > 0
                        for item, qty in sandwiches.items():
                            display_name = "Cebola (Adjustment)" if item == "Cebola" and has_adjustment else item
                            prefix = "🔹 " if item == "Cebola" and has_adjustment else ""
                            st.write(f"- {prefix}{qty}x {display_name}: {format_currency(sandwich_prices[item] * qty)}")
                        st.metric("Sandwich Total", format_currency(sandwich_total))
                    else:
                        st.info("No sandwiches")
                
                diff = combined_total - total
                st.metric(
                    "💰 TOTAL",
                    format_currency(combined_total),
                    delta=f"{format_currency(diff)} vs Target",
                    delta_color="normal" if diff <= 0 else "inverse"
                )
    
    except Exception as e:
        st.error(f"Processing error: {str(e)}")
else:
    st.info("Please upload a sales file to begin")
