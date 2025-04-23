import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import random
import sqlite3

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão - Clips Burger", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

# --- BANCO DE DADOS SQLite ---
DB_FILE = "recebimentos.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS recebimentos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  data TEXT NOT NULL,
                  dinheiro REAL NOT NULL,
                  cartao REAL NOT NULL,
                  pix REAL NOT NULL)''')
    conn.commit()
    conn.close()

@st.cache_resource
def get_db():
    init_db()
    return sqlite3.connect(DB_FILE)

def salvar_recebimento(data, dinheiro, cartao, pix):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO recebimentos (data, dinheiro, cartao, pix) VALUES (?, ?, ?, ?)",
              (data.isoformat(), dinheiro, cartao, pix))
    conn.commit()
    conn.close()

def carregar_recebimentos():
    conn = get_db()
    df = pd.read_sql("SELECT data, dinheiro, cartao, pix FROM recebimentos", conn)
    conn.close()
    if not df.empty:
        df['Data'] = pd.to_datetime(df['data'])
        return df.drop(columns=['data'])
    return pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])

# --- DADOS DO CARDÁPIO ---
DADOS_SANDUICHES = """X Salada Simples R$ 18,00
X Bacon R$ 22,00
X Tudo R$ 25,00
X Frango R$ 20,00
X Egg R$ 21,00
Cebola R$ 5,00"""

DADOS_BEBIDAS = """Suco R$ 10,00
Refrigerante R$ 8,00
Água R$ 5,00
Cerveja R$ 12,00"""

def criar_cardapio(texto):
    cardapio = {}
    for linha in texto.split("\n"):
        partes = linha.split("R$ ")
        if len(partes) == 2:
            nome = partes[0].strip()
            preco = float(partes[1].replace(",", "."))
            cardapio[nome] = preco
    return cardapio

# --- FUNÇÕES AUXILIARES ---
def arredondar(valor):
    return round(valor * 2) / 2

def criar_combinacao(itens, tamanho):
    combinacao = {}
    nomes = list(itens.keys())
    if nomes:
        selecionados = random.sample(nomes, min(tamanho, len(nomes)))
        for nome in selecionados:
            combinacao[nome] = arredondar(random.uniform(1, 10))
    return combinacao

def calcular_total(combinacao, precos):
    return sum(precos.get(nome, 0) * qtd for nome, qtd in combinacao.items())

def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# --- INTERFACE ---
# Carrega dados
sanduiches = criar_cardapio(DADOS_SANDUICHES)
bebidas = criar_cardapio(DADOS_BEBIDAS)
df_recebimentos = carregar_recebimentos()

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    percentual_bebidas = st.slider("Percentual para Bebidas (%)", 0, 100, 20)
    st.caption(f"Sanduíches: {100 - percentual_bebidas}%")
    
    qtd_bebidas = st.slider("Tipos de Bebidas", 1, 10, 3)
    qtd_sanduiches = st.slider("Tipos de Sanduíches", 1, 10, 3)
    
    st.info("As combinações são aproximadas.")

# Cabeçalho
st.title("🍔 Clip's Burger - Gestão")
st.write("Sistema de acompanhamento de vendas e recebimentos")

# Abas
tab1, tab2, tab3 = st.tabs(["📊 Vendas", "🧮 Combinações", "💸 Recebimentos"])

with tab1:
    arquivo = st.file_uploader("Envie o arquivo de vendas", type=["csv", "xlsx"])
    if arquivo:
        try:
            if arquivo.name.endswith(".csv"):
                dados = pd.read_csv(arquivo)
            else:
                dados = pd.read_excel(arquivo)
            
            st.success("Arquivo carregado!")
            st.write(dados)
        except:
            st.error("Erro ao ler arquivo")

with tab2:
    if arquivo:
        # (Aqui viria a lógica de combinações)
        st.write("Combinações aparecerão aqui")
    else:
        st.warning("Envie o arquivo na aba Vendas")

with tab3:
    st.header("Cadastrar Recebimento")
    
    with st.form("form_recebimento"):
        data = st.date_input("Data", datetime.now())
        col1, col2, col3 = st.columns(3)
        dinheiro = col1.number_input("Dinheiro", 0.0, step=0.5)
        cartao = col2.number_input("Cartão", 0.0, step=0.5)
        pix = col3.number_input("Pix", 0.0, step=0.5)
        
        if st.form_submit_button("Salvar"):
            if dinheiro + cartao + pix > 0:
                salvar_recebimento(data, dinheiro, cartao, pix)
                st.success("Salvo com sucesso!")
                df_recebimentos = carregar_recebimentos()
            else:
                st.warning("Insira pelo menos um valor")

    st.header("Histórico")
    if not df_recebimentos.empty:
        df_recebimentos['Total'] = df_recebimentos.sum(axis=1)
        st.dataframe(df_recebimentos)
        
        st.download_button(
            "Exportar para CSV",
            df_recebimentos.to_csv(index=False),
            "recebimentos.csv",
            "text/csv"
        )
    else:
        st.info("Nenhum recebimento cadastrado")
