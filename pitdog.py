import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Simulador de Combinações", layout="wide")

# Função para ler cardápio a partir de string
def ler_cardapio_do_excel(dados):
    cardapio = {}
    linhas = dados.strip().split("\n")
    for linha in linhas:
        partes = linha.split("R$ ")
        if len(partes) == 2:
            nome = partes[0].strip()
            try:
                preco = float(partes[1].replace(",", "."))
                cardapio[nome] = preco
            except ValueError:
                pass
    return cardapio

# Dados do cardápio
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

sanduiches = ler_cardapio_do_excel(dados_sanduiches)
bebidas = ler_cardapio_do_excel(dados_bebidas)

# Busca local otimizada
def calcular_valor_combinacao(combinacao, itens):
    return sum(itens[nome] * quantidade for nome, quantidade in combinacao.items())

def gerar_combinacao_inicial(itens, tamanho_combinacao):
    return {random.choice(list(itens.keys())): random.uniform(1, 75) for _ in range(tamanho_combinacao)}

def busca_local_otimizada(itens, valor_total, tamanho_combinacao):
    melhor_combinacao = gerar_combinacao_inicial(itens, tamanho_combinacao)
    melhor_diferenca = abs(valor_total - calcular_valor_combinacao(melhor_combinacao, itens))

    for _ in range(10000):
        vizinho = melhor_combinacao.copy()
        nome = random.choice(list(vizinho.keys()))
        vizinho[nome] = max(1, min(vizinho[nome] + random.uniform(-5, 5), 75))
        diferenca = abs(valor_total - calcular_valor_combinacao(vizinho, itens))
        if diferenca < melhor_diferenca:
            melhor_combinacao, melhor_diferenca = vizinho, diferenca
        if melhor_diferenca < 0.01:
            break
    return melhor_combinacao

st.title("🍔 Simulador de Combinação de Pedidos")
st.markdown("Este app calcula combinações otimizadas de sanduíches e bebidas com base em valores de venda por forma de pagamento.")

formas_pagamento = [
    "Crédito Elo", "Crédito MasterCard", "Crédito Visa",
    "Débito Elo", "Débito MasterCard", "Débito Visa", "PIX"
]

st.sidebar.header("🔢 Entradas de Venda")
vendas = {}
for forma in formas_pagamento:
    vendas[forma] = st.sidebar.number_input(f"{forma}", min_value=0.0, value=0.0, step=1.0)

if st.sidebar.button("Calcular Combinações"):
    for forma_pagamento, valor_total in vendas.items():
        if valor_total <= 0:
            continue

        valor_bebidas = int(valor_total * 0.2)
        valor_sanduiches = valor_total - valor_bebidas

        combinacao_bebidas = busca_local_otimizada(bebidas, valor_bebidas, 5)
        combinacao_sanduiches = busca_local_otimizada(sanduiches, valor_sanduiches, 5)

        total_bebidas = sum(bebidas[n] * round(q) for n, q in combinacao_bebidas.items())
        total_sanduiches = sum(sanduiches[n] * round(q) for n, q in combinacao_sanduiches.items())
        total_geral = total_bebidas + total_sanduiches

        st.markdown(f"### 💳 {forma_pagamento}")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🧃 Bebidas")
            df_bebidas = pd.DataFrame(
                [(nome, round(q), f"R$ {bebidas[nome] * round(q):.2f}") for nome, q in combinacao_bebidas.items()],
                columns=["Item", "Qtd", "Total"]
            )
            st.table(df_bebidas)

        with col2:
            st.markdown("#### 🍔 Sanduíches")
            df_sanduiches = pd.DataFrame(
                [(nome, round(q), f"R$ {sanduiches[nome] * round(q):.2f}") for nome, q in combinacao_sanduiches.items()],
                columns=["Item", "Qtd", "Total"]
            )
            st.table(df_sanduiches)

        st.markdown(f"**Total Bebidas:** R$ {total_bebidas:.2f}")
        st.markdown(f"**Total Sanduíches:** R$ {total_sanduiches:.2f}")
        st.markdown(f"**Total Geral:** R$ {total_geral:.2f} _(Diferença: R$ {valor_total - total_geral:.2f})_")
        st.markdown("---")
