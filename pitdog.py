import streamlit as st
import pandas as pd
import random
import numpy as np
from datetime import datetime

# ----- Funções Auxiliares -----
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
                st.warning(f"Preço inválido para '{nome}'. Ignorando.")
    return cardapio

def calcular_valor_combinacao(combinacao, itens):
    return sum(itens[nome] * quantidade for nome, quantidade in combinacao.items())

def gerar_combinacao_inicial(itens, tamanho_combinacao):
    combinacao = {}
    nomes_itens = list(itens.keys())
    for _ in range(tamanho_combinacao):
        nome = random.choice(nomes_itens)
        combinacao[nome] = random.uniform(1, 75)
    return combinacao

def busca_local_otimizada(itens, valor_total, tamanho_combinacao):
    melhor_combinacao = gerar_combinacao_inicial(itens, tamanho_combinacao)
    melhor_diferenca = abs(valor_total - calcular_valor_combinacao(melhor_combinacao, itens))

    for _ in range(10000):
        vizinho = melhor_combinacao.copy()
        nome = random.choice(list(vizinho.keys()))
        vizinho[nome] += random.uniform(-5, 5)
        vizinho[nome] = max(1, min(vizinho[nome], 75))

        diferenca = abs(valor_total - calcular_valor_combinacao(vizinho, itens))
        if diferenca < melhor_diferenca:
            melhor_diferenca = diferenca
            melhor_combinacao = vizinho

        if melhor_diferenca < 0.01:
            break

    return melhor_combinacao

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ----- Interface Streamlit -----
st.set_page_config(page_title="Relatório de Vendas + Combinações", layout="centered")
st.title("📊 Análise de Transações e Combinação de Vendas")

arquivo = st.file_uploader("Envie o arquivo de transações (.csv ou .xlsx)", type=["csv", "xlsx"])

if arquivo:
    try:
        if arquivo.name.endswith(".csv"):
            df = pd.read_csv(arquivo, sep=';', encoding='utf-8')
        else:
            df = pd.read_excel(arquivo)

        st.success("Arquivo carregado com sucesso!")
        st.dataframe(df.head())

        df['Tipo'] = df['Tipo'].str.lower().str.strip()
        df['Bandeira'] = df['Bandeira'].str.lower().str.strip()
        df['Valor'] = df['Valor'].astype(str).str.replace(',', '.').astype(float)
        df['Categoria'] = df['Tipo'] + ' ' + df['Bandeira']

        categorias_desejadas = {
            'crédito à vista elo': 'Crédito Elo',
            'crédito à vista mastercard': 'Crédito MasterCard',
            'crédito à vista visa': 'Crédito Visa',
            'débito elo': 'Débito Elo',
            'débito mastercard': 'Débito MasterCard',
            'débito visa': 'Débito Visa',
            'pix': 'PIX'
        }

        df['Forma Nomeada'] = df['Categoria'].map(categorias_desejadas)
        df = df.dropna(subset=['Forma Nomeada'])
        vendas = df.groupby('Forma Nomeada')['Valor'].sum().to_dict()

        st.subheader("💳 Valores somados por forma de pagamento")
        st.write(vendas)

        # --- Cardápios ---
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

        st.subheader("🍔 Combinações geradas por forma de pagamento")
        
        # Ordem desejada para os expansíveis
        ordem_formas = [
            'Débito Visa',
            'Débito MasterCard',
            'Débito Elo',
            'Crédito Visa',
            'Crédito MasterCard',
            'Crédito Elo',
            'PIX'
        ]
        
        combinacoes = {}
        for forma in ordem_formas:
            if forma in vendas:
                total = vendas[forma]
                valor_bebidas = total * 0.2
                valor_sanduiches = total - valor_bebidas
                comb_bebidas = busca_local_otimizada(bebidas, valor_bebidas, 5)
                comb_sanduiches = busca_local_otimizada(sanduiches, valor_sanduiches, 5)
                combinacoes[forma] = {"Bebidas": comb_bebidas, "Sanduiches": comb_sanduiches}
                
                with st.expander(f"{forma} - {formatar_moeda(total)}", expanded=False):
                    st.subheader("🍹 Bebidas")
                    total_bebidas = 0
                    cols = st.columns(3)
                    for i, (nome, quantidade) in enumerate(comb_bebidas.items()):
                        quantidade = round(quantidade)
                        valor_total = bebidas[nome] * quantidade
                        total_bebidas += valor_total
                        with cols[i % 3]:
                            st.metric(
                                label=nome,
                                value=f"{quantidade} un",
                                delta=formatar_moeda(valor_total)
                    
                    st.divider()
                    st.metric("Total Bebidas", formatar_moeda(total_bebidas))
                    
                    st.subheader("🍔 Sanduíches")
                    total_sanduiches = 0
                    cols = st.columns(3)
                    for i, (nome, quantidade) in enumerate(comb_sanduiches.items()):
                        quantidade = round(quantidade)
                        valor_total = sanduiches[nome] * quantidade
                        total_sanduiches += valor_total
                        with cols[i % 3]:
                            st.metric(
                                label=nome,
                                value=f"{quantidade} un",
                                delta=formatar_moeda(valor_total))
                    
                    st.divider()
                    st.metric("Total Sanduíches", formatar_moeda(total_sanduiches))
                    st.metric("TOTAL GERAL", formatar_moeda(total_bebidas + total_sanduiches), delta_color="off")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
