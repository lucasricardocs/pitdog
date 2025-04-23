# ... (código anterior permanece igual até a Tab1)

with tab1:
    st.header("📈 Resumo das Vendas")
    arquivo = st.file_uploader("📤 Envie o arquivo de transações (.csv ou .xlsx)", 
                             type=["csv", "xlsx"])

    if arquivo:
        try:
            # Verificar o tipo de arquivo
            if arquivo.name.endswith(".csv"):
                # Tentar ler com diferentes delimitadores
                try:
                    df = pd.read_csv(arquivo, sep=';', encoding='utf-8', dtype=str)
                except pd.errors.ParserError:
                    arquivo.seek(0)  # Resetar o ponteiro do arquivo
                    try:
                        df = pd.read_csv(arquivo, sep=',', encoding='utf-8', dtype=str)
                    except:
                        arquivo.seek(0)
                        # Tentar ler automaticamente se ainda falhar
                        df = pd.read_csv(arquivo, engine='python', dtype=str)
            else:
                df = pd.read_excel(arquivo, dtype=str)
            
            # Verificar colunas obrigatórias
            required_cols = ['Tipo', 'Bandeira', 'Valor']
            if not all(col in df.columns for col in required_cols):
                st.error(f"Erro: O arquivo precisa conter as colunas: {', '.join(required_cols)}")
                st.stop()

            # Processamento dos dados
            df['Tipo'] = df['Tipo'].str.lower().str.strip().fillna('desconhecido')
            df['Bandeira'] = df['Bandeira'].str.lower().str.strip().fillna('desconhecida')
            df['Valor'] = pd.to_numeric(
                df['Valor'].str.replace('.', '').str.replace(',', '.'), 
                errors='coerce')
            df = df.dropna(subset=['Valor'])
            
            df['Forma'] = (df['Tipo'] + ' ' + df['Bandeira']).map(FORMAS_PAGAMENTO)
            df = df.dropna(subset=['Forma'])
            
            if df.empty:
                st.warning("Nenhuma transação válida encontrada.")
                st.stop()

            vendas = df.groupby('Forma')['Valor'].sum().reset_index()
            total_vendas = vendas['Valor'].sum()
            
            # Gráfico de Pizza
            st.subheader("Vendas por Forma de Pagamento")
            pie_chart = create_altair_chart(
                vendas, 'pie', 'Forma', 'Valor', 
                title='Distribuição das Vendas por Forma de Pagamento'
            )
            st.altair_chart(pie_chart, use_container_width=True)
            
            # Restante do código da Tab1...
            
        except Exception as e:
            st.error(f"Erro no processamento: {str(e)}")
    else:
        st.info("✨ Aguardando envio do arquivo de transações...")

# ... (código da Tab2 permanece igual)

with tab3:
    st.header("💰 Cadastro de Recebimentos Diários")
    
    # Carrega os dados existentes
    try:
        df_existente = pd.read_excel(CONFIG["excel_file"])
        df_existente['Data'] = pd.to_datetime(df_existente['Data']).dt.date
        st.session_state['df_receipts'] = df_existente
    except Exception as e:
        st.warning(f"Não foi possível carregar dados existentes: {e}")
        st.session_state['df_receipts'] = pd.DataFrame(columns=['Data', 'Dinheiro', 'Cartao', 'Pix'])

    # Formulário para novos dados
    with st.form("receipt_form", clear_on_submit=True):
        data = st.date_input("Data", datetime.now().date())
        dinheiro = st.number_input("Dinheiro (R$)", min_value=0.0, format="%.2f")
        cartao = st.number_input("Cartão (R$)", min_value=0.0, format="%.2f")
        pix = st.number_input("Pix (R$)", min_value=0.0, format="%.2f")
        
        if st.form_submit_button("Salvar") and (dinheiro + cartao + pix) > 0:
            novo_registro = pd.DataFrame([{
                'Data': data,
                'Dinheiro': dinheiro,
                'Cartao': cartao, 
                'Pix': pix
            }])
            
            st.session_state['df_receipts'] = pd.concat(
                [st.session_state['df_receipts'], novo_registro], 
                ignore_index=True
            )
            
            save_data(st.session_state['df_receipts'])
            st.success("Dados salvos com sucesso!")
            st.experimental_rerun()

    # Visualização dos dados
    st.header("📊 Análise de Recebimentos")
    if not st.session_state['df_receipts'].empty:
        df = st.session_state['df_receipts'].copy()
        df['Total'] = df[['Dinheiro', 'Cartao', 'Pix']].sum(axis=1)
        df = df.sort_values('Data')
        
        # Gráfico de Pizza - Distribuição dos Pagamentos
        st.subheader("Distribuição dos Recebimentos")
        totais_pagamentos = df[['Dinheiro', 'Cartao', 'Pix']].sum().reset_index()
        totais_pagamentos.columns = ['Forma', 'Total']
        
        pie_chart = alt.Chart(totais_pagamentos).mark_arc().encode(
            theta='Total',
            color='Forma',
            tooltip=['Forma', 'Total']
        ).properties(
            title='Proporção dos Tipos de Pagamento',
            width=600,
            height=400
        )
        st.altair_chart(pie_chart, use_container_width=True)
        
        # Gráfico de Evolução Patrimonial
        st.subheader("Evolução Patrimonial")
        df['Acumulado'] = df['Total'].cumsum()
        
        line_chart = alt.Chart(df).mark_line(point=True).encode(
            x='Data:T',
            y='Acumulado:Q',
            tooltip=['Data', 'Dinheiro', 'Cartao', 'Pix', 'Total', 'Acumulado']
        ).properties(
            title='Evolução do Total Recebido',
            width=800,
            height=400
        )
        
        st.altair_chart(line_chart, use_container_width=True)
        
        # Tabela com todos os dados
        st.subheader("Histórico Completo")
        st.dataframe(
            df.sort_values('Data', ascending=False).style.format({
                'Dinheiro': format_currency,
                'Cartao': format_currency,
                'Pix': format_currency,
                'Total': format_currency,
                'Acumulado': format_currency
            }),
            height=400
        )
        
        # Opção para deletar registros
        with st.expander("🗑️ Gerenciar Registros", expanded=False):
            registros_para_deletar = st.multiselect(
                "Selecione registros para deletar",
                options=df.index,
                format_func=lambda x: f"{df.loc[x, 'Data']} - {format_currency(df.loc[x, 'Total'])}"
            )
            
            if st.button("Confirmar Exclusão") and registros_para_deletar:
                df = df.drop(registros_para_deletar)
                st.session_state['df_receipts'] = df
                save_data(df)
                st.success(f"{len(registros_para_deletar)} registros removidos!")
                st.experimental_rerun()
    else:
        st.info("Nenhum recebimento cadastrado ainda.")

if __name__ == '__main__':
    pass
