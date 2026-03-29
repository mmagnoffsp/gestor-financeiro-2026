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
        # Busca os dados
        query = "SELECT data, categoria, valor, tipo FROM lancamentos"
        df = pd.read_sql(query, engine)

        if not df.empty:
            # Criando duas colunas: uma para a tabela e outra para o gráfico
            col_tabela, col_grafico = st.columns([1, 1])

            with col_tabela:
                st.write("**Histórico Recente**")
                # Padrão 2026: width='stretch'
                st.dataframe(df.sort_values(by='data', ascending=False), width='stretch')

            with col_grafico:
                st.write("**Onde você está gastando/recebendo mais:**")
                # Lógica do Gráfico: Agrupa por categoria e soma os valores
                resumo = df.groupby("categoria")["valor"].sum()
                st.bar_chart(resumo)
                
        else:
            st.info("Ainda não há lançamentos para gerar o gráfico.")

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
else:
    st.error("Conexão com o banco não configurada no .env")