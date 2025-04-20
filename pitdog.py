import streamlit as st
import pandas as pd
import random
import time
from typing import Dict, Tuple, List

# ================== FUNÇÕES AUXILIARES ==================
def parse_menu_string(menu_data: str) -> Dict[str, float]:
    """Converte string do cardápio para dicionário {item: preço}"""
    menu = {}
    for line in menu_data.strip().split("\n"):
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
    """Calcula o valor total de uma combinação"""
    return sum(prices.get(name, 0) * qty for name, qty in combination.items())

def round_to_50_or_00(value: float) -> float:
    """Arredonda para o múltiplo de 0.50 mais próximo"""
    return round(value * 2) / 2

def generate_initial_combination(prices: Dict[str, float], max_items: int) -> Dict[str, float]:
    """Gera combinação inicial aleatória"""
    items = list(prices.keys())
    if not items:
        return {}
    
    num_items = min(max_items, len(items))
    selected = random.sample(items, num_items)
    return {item: round_to_50_or_00(random.uniform(1, 5)) for item in selected}

def local_search_optimization(
    prices: Dict[str, float],
    target: float,
    max_items: int,
    max_iterations: int
) -> Dict[str, float]:
    """Algoritmo de busca local para encontrar combinação ideal"""
    current = generate_initial_combination(prices, max_items)
    if not current:
        return {}
    
    current_value = calculate_combination_value(current, prices)
    best = current.copy()
    best_diff = abs(target - current_value)
    
    for _ in range(max_iterations):
        neighbor = current.copy()
        item = random.choice(list(neighbor.keys()))
        
        # Modifica em incrementos de 0.50
        change = random.choice([-0.5, 0.5, -1.0, 1.0])
        neighbor[item] = max(0.5, neighbor[item] + change)
        neighbor[item] = round_to_50_or_00(neighbor[item])
        
        neighbor_value = calculate_combination_value(neighbor, prices)
        neighbor_diff = abs(target - neighbor_value)
        
        # Penaliza soluções que ultrapassam o target
        if neighbor_value > target:
            neighbor_diff += 1000
            
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
    """Adiciona cebolas para completar o valor se necessário"""
    current = calculate_combination_value(combination, prices)
    if current >= target or "Cebola" not in prices:
        return combination, current
    
    diff = target - current
    onion_price = prices["Cebola"]
    num_onions = int(round(diff / onion_price))
    
    if num_onions > 0:
        combination["Cebola (Ajuste)"] = num_onions
    
    final = calculate_combination_value(combination, prices)
    return combination, final

def format_currency(value: float) -> str:
    """Formata valor como moeda brasileira"""
    try:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ --"

# ================== INTERFACE ==================
st.set_page_config(page_title="Otimizador de Vendas", layout="wide")

# Dados dos cardápios (exatamente como você forneceu)
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

# Processa cardápios
sanduiches_precos = parse_menu_string(dados_sanduiches)
bebidas_precos = parse_menu_string(dados_bebidas)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    drink_perc = st.slider("Percentual para Bebidas", 0, 100, 30)
    max_drink_types = st.slider("Tipos de Bebidas", 1, 10, 4)
    max_sandwich_types = st.slider("Tipos de Sanduíches", 1, 10, 5)
    max_iter = st.select_slider("Iterações de Otimização", [1000, 5000, 10000, 20000], 10000)

# Upload de arquivo
upload = st.file_uploader("📤 Upload do Arquivo de Vendas (CSV ou Excel)", type=["csv", "xlsx"])

if upload:
    try:
        # Processa o arquivo
        if upload.name.endswith(".csv"):
            df = pd.read_csv(upload, sep=";", decimal=",")
        else:
            df = pd.read_excel(upload)
        
        # Pré-processamento
        df["Valor"] = pd.to_numeric(
            df["Valor"].astype(str)
            .str.replace(".", "")
            .str.replace(",", ".")
        )
        
        # Verifica colunas obrigatórias
        if "FormaPagamento" not in df.columns or "Valor" not in df.columns:
            st.error("O arquivo precisa ter as colunas 'FormaPagamento' e 'Valor'")
            st.stop()
        
        # Agrupa por forma de pagamento
        vendas = df.groupby("FormaPagamento")["Valor"].sum()
        
        # Para cada forma de pagamento
        for forma, total in vendas.items():
            with st.expander(f"{forma} (Total: {format_currency(total)})", expanded=False):
                # Calcula targets
                target_bebidas = round_to_50_or_00(total * drink_perc / 100)
                target_sanduiches = round_to_50_or_00(total - target_bebidas)
                
                # Otimização
                with st.spinner(f"Otimizando combinação para {forma}..."):
                    comb_bebidas = local_search_optimization(
                        bebidas_precos, target_bebidas, max_drink_types, max_iter
                    )
                    comb_sanduiches = local_search_optimization(
                        sanduiches_precos, target_sanduiches, max_sandwich_types, max_iter
                    )
                    
                    # Ajusta com cebolas se necessário
                    comb_bebidas, val_bebidas = adjust_with_onions(
                        comb_bebidas, bebidas_precos, target_bebidas
                    )
                    comb_sanduiches, val_sanduiches = adjust_with_onions(
                        comb_sanduiches, sanduiches_precos, target_sanduiches
                    )
                
                # Exibe resultados
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"🍹 Bebidas (Target: {format_currency(target_bebidas)})")
                    for item, qty in comb_bebidas.items():
                        st.write(f"- {int(qty)}x {item}: {format_currency(bebidas_precos[item] * qty)}")
                    st.metric("Total Bebidas", format_currency(val_bebidas))
                
                with col2:
                    st.subheader(f"🍔 Sanduíches (Target: {format_currency(target_sanduiches)})")
                    for item, qty in comb_sanduiches.items():
                        prefix = "🔹 " if "Cebola" in item else ""  # Destaque para cebolas
                        st.write(f"- {prefix}{int(qty)}x {item}: {format_currency(sanduiches_precos[item] * qty)}")
                    st.metric("Total Sanduíches", format_currency(val_sanduiches))
                
                # Calcula diferença
                total_combinacao = val_bebidas + val_sanduiches
                diferenca = total_combinacao - total
                
                st.metric("TOTAL GERAL", 
                         format_currency(total_combinacao),
                         delta=f"Diferença: {format_currency(diferenca)}",
                         delta_color="normal" if diferenca <= 0 else "inverse")
    
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {str(e)}")
        st.stop()
else:
    st.info("Por favor, faça upload de um arquivo de vendas para começar.")
