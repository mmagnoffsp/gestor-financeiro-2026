import streamlit as st
import pandas as pd
from database import inicializar_banco, salvar_dados, engine
from fpdf import FPDF

# --- 1. FUNÇÃO DE SEGURANÇA ---
def verificar_senha():
    """Retorna True se a senha estiver correta."""
    def login():
        senha_digitada = st.text_input("Digite a senha para acessar seus dados:", type="password")
        if st.button("Entrar"):
            if senha_digitada == "Ca10Mg43@#$":
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("🔑 Senha incorreta. Acesso negado.")

    if "autenticado" not in st.session_state:
        st.title("🔒 Gestor Financeiro Privado")
        login()
        return False
    return True

# --- 2. FUNÇÃO PARA GERAR PDF ---
def gerar_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio Financeiro - ADS", ln=True, align="C")
    pdf.ln(10)
    
    # Cabeçalho da tabela no PDF
    pdf.set_font("Arial", "B", 10)
    pdf.cell(25, 10, "Data", 1)
    pdf.cell(55, 10, "Categoria", 1)
    pdf.cell(25, 10, "Valor", 1)
    pdf.cell(20, 10, "Tipo", 1)
    pdf.cell(65, 10, "Obs", 1)
    pdf.ln()

    # Dados das linhas
    pdf.set_font("Arial", "", 9)
    for _, row in dataframe.iterrows():
        pdf.cell(25, 10, str(row['data']), 1)
        pdf.cell(55, 10, str(row['categoria']), 1)
        pdf.cell(25, 10, f"R$ {row['valor']:.2f}", 1)
        pdf.cell(20, 10, str(row['tipo']), 1)
        # Limpa e limita a observação para não quebrar o layout do PDF
        observacao = str(row['observacao']) if row['observacao'] else ""
        pdf.cell(65, 10, observacao[:35], 1)
        pdf.ln()
    
    # Gera o PDF em bytes (latin-1 para evitar erros de acentuação básica)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestor Financeiro ADS", layout="wide")

# --- 4. INÍCIO DO APP PROTEGIDO ---
if verificar_senha():
    inicializar_banco()

    st.title("💰 Meu Gestor Financeiro - Cloud")

    # Botão de Logout na barra lateral
    if st.sidebar.button("Sair / Bloquear"):
        del st.session_state["autenticado"]
        st.rerun()

    # --- FORMULÁRIO DE LANÇAMENTO ---
    with st.expander("➕ Novo Lançamento", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            data = st.date_input("Data")
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        
        with col2:
            lista_categorias_base = [
                "açougue", "agua potavel", "areia pet", "barbearia", "condominio",
                "deposito apartamento pagamento", "deposito apartamento vale",
                "enel", "gastos parcelados", "internet", "lanche gean pagamento", 
                "lanche gean vale", "mercado", "pagamento recebido", 
                "reserva de caixa no vale", "reserva de caixa no pagamento", 
                "taxi/uber", "universidade", "vacina pets", "vale recebido", 
                "vivo celular"
            ]
            lista_categorias = sorted([item.title() for item in lista_categorias_base])
            categoria = st.selectbox("Categoria", lista_categorias)
        
        with col3:
            tipo = st.radio("Tipo", ["Entrada", "Saída"], horizontal=True)

        obs = st.text_area("Nota / Observação", placeholder="Ex: Detalhes da entrada ou parcelas")

        if st.button("Confirmar Lançamento", use_container_width=True):
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
            query = "SELECT id, data, categoria, valor, tipo, observacao FROM lancamentos"
            df = pd.read_sql(query, engine)

            if not df.empty:
                col_tabela, col_grafico = st.columns([1, 1])

                with col_tabela:
                    st.write("**Histórico Recente**")
                    df_exibicao = df.sort_values(by='id', ascending=False)
                    st.dataframe(df_exibicao, width='stretch', hide_index=True)

                with col_grafico:
                    st.write("**Resumo por Categoria**")
                    resumo = df.groupby("categoria")["valor"].sum()
                    st.bar_chart(resumo)
                
                # --- 📄 SEÇÃO DE PDF (EXPORTAR) ---
                st.divider()
                st.write("📂 **Exportar Dados**")
                
                # Gera o PDF a partir do dataframe atual
                pdf_output = gerar_pdf(df)
                
                st.download_button(
                    label="📥 Baixar Relatório em PDF",
                    data=pdf_output,
                    file_name="relatorio_financeiro.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

                # --- 🗑️ SEÇÃO DE EXCLUSÃO ---
                st.divider()
                st.subheader("🗑️ Limpar Registro")
                
                col_del_1, col_del_2 = st.columns([3, 1])
                opcoes_delete = {
                    f"ID {row['id']} - {row['categoria']} (R$ {row['valor']})": row['id'] 
                    for _, row in df.iterrows()
                }
                
                with col_del_1:
                    selecionado = st.selectbox(
                        "Selecione para excluir:", 
                        options=sorted(list(opcoes_delete.keys()), reverse=True),
                        label_visibility="collapsed"
                    )
                
                with col_del_2:
                    if st.button("Excluir", type="primary", use_container_width=True):
                        id_para_deletar = opcoes_delete[selecionado]
                        from database import deletar_registro
                        if deletar_registro(id_para_deletar):
                            st.success("Removido!")
                            st.rerun()
            else:
                st.info("Ainda não há lançamentos para gerar o relatório.")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
    else:
        st.error("Conexão com o banco não configurada.")