import streamlit as st
import pandas as pd
from database import inicializar_banco, salvar_dados, engine

# Configuração da página padrão 2026
st.set_page_config(page_title="Gestor Financeiro ADS", layout="wide")

# Inicializa o banco de dados no Neon
inicializar_banco()

st.title("💰 Meu Gestor Financeiro - Cloud")

# --- FORMULÁRIO DE LANÇAMENTO ---
with st.expander("➕ Novo Lançamento", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        data = st.date_input("Data")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    
    with col2:
        categoria = st.selectbox("Categoria", [
            "Salário Mensal", "13º Salário", "Férias", 
            "Amortização FGTS", "Reserva de Caixa", "Aluguel", "Mercado", "Outros"
        ])
    
    with col3:
        tipo = st.radio("Tipo", ["Entrada", "Saída"])
        obs = st.text_input("Nota/Observação")

    if st.button("Confirmar Lançamento"):
        if valor > 0:
            sucesso = salvar_dados(data, categoria, valor, tipo, obs)
            if sucesso:
                st.success(f"✅ {categoria} salvo com sucesso!")
                st.rerun() 
        else:
            st.warning("Insira um valor maior que zero.")

st.divider()

# --- VISUALIZAÇÃO E GRÁFICOS ---
st.subheader("📊 Resumo Financeiro (Nuvem Neon)")

if engine:
    try:
        # 1. ATUALIZADO: Agora buscamos o 'id' para poder deletar depois
        query = "SELECT id, data, categoria, valor, tipo, observacao FROM lancamentos"
        df = pd.read_sql(query, engine)

        if not df.empty:
            col_tabela, col_grafico = st.columns([1, 1])

            with col_tabela:
                st.write("**Histórico Recente**")
                # Ordenamos pelo ID mais novo para facilitar a exclusão do último teste
                df_exibicao = df.sort_values(by='id', ascending=False)
                st.dataframe(df_exibicao, width='stretch', hide_index=True)

            with col_grafico:
                st.write("**Onde você está gastando/recebendo mais:**")
                resumo = df.groupby("categoria")["valor"].sum()
                st.bar_chart(resumo)
            
            # --- 🗑️ SEÇÃO DE EXCLUSÃO (NOVO) ---
            st.divider()
            st.subheader("🗑️ Gerenciar Lançamentos")
            
            # Criamos uma lista de opções para o Selectbox (Ex: ID 1 - Mercado)
            opcoes_delete = {
                f"ID {row['id']} - {row['categoria']} (R$ {row['valor']})": row['id'] 
                for _, row in df.iterrows()
            }
            
            selecionado = st.selectbox("Selecione o registro para excluir:", options=list(opcoes_delete.keys()))
            
            if st.button("Confirmar Exclusão", type="primary"):
                id_para_deletar = opcoes_delete[selecionado]
                
                # Importamos a função que você adicionou no database.py
                from database import deletar_registro
                if deletar_registro(id_para_deletar):
                    st.success("Registro removido com sucesso!")
                    st.rerun() # Recarrega a página para atualizar tabela e gráfico
                else:
                    st.error("Erro ao tentar apagar no banco de dados.")
                
        else:
            st.info("Ainda não há lançamentos para gerar o gráfico.")

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
else:
    st.error("Conexão com o banco não configurada no .env")