import streamlit as st
import pandas as pd
from database import inicializar_banco, salvar_dados, engine, deletar_registro, atualizar_registro
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

# --- 2. FUNÇÃO PARA GERAR PDF COM TOTAIS ---
def gerar_pdf(dataframe):
    # Cálculos para o PDF
    t_entradas = dataframe[dataframe['tipo'] == 'Entrada']['valor'].sum()
    t_saidas = dataframe[dataframe['tipo'] == 'Saída']['valor'].sum()
    saldo = t_entradas - t_saidas

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio Financeiro - ADS", ln=True, align="C")
    pdf.ln(10)
    
    # Cabeçalho da tabela
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
        observacao = str(row['observacao']) if row['observacao'] else ""
        pdf.cell(65, 10, observacao[:35], 1)
        pdf.ln()
    
    # Rodapé com Totais no PDF
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 10, f"Total Entradas: R$ {t_entradas:.2f}", ln=True)
    pdf.cell(190, 10, f"Total Saidas: R$ {t_saidas:.2f}", ln=True)
    pdf.set_text_color(0, 128, 0) if saldo >= 0 else pdf.set_text_color(255, 0, 0)
    pdf.cell(190, 10, f"SALDO FINAL: R$ {saldo:.2f}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestor Financeiro ADS", layout="wide")

# --- 4. INÍCIO DO APP PROTEGIDO ---
if verificar_senha():
    inicializar_banco()

    st.title("💰 Meu Gestor Financeiro - Cloud")

    if st.sidebar.button("Sair / Bloquear"):
        del st.session_state["autenticado"]
        st.rerun()

    # Lista de categorias centralizada
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

    # --- FORMULÁRIO DE LANÇAMENTO ---
    with st.expander("➕ Novo Lançamento", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            data = st.date_input("Data")
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        with col2:
            categoria = st.selectbox("Categoria", lista_categorias)
        with col3:
            tipo = st.radio("Tipo", ["Entrada", "Saída"], horizontal=True)

        obs = st.text_area("Nota / Observação", placeholder="Ex: Detalhes ou parcelas")

        if st.button("Confirmar Lançamento", use_container_width=True):
            if valor > 0:
                sucesso = salvar_dados(data, categoria, valor, tipo, obs)
                if sucesso:
                    st.success(f"✅ {categoria} salvo!")
                    st.rerun() 
            else:
                st.warning("Insira um valor maior que zero.")

    st.divider()

    # --- VISUALIZAÇÃO E GRÁFICOS ---
    if engine:
        try:
            df = pd.read_sql("SELECT id, data, categoria, valor, tipo, observacao FROM lancamentos", engine)

            if not df.empty:
                # --- NOVO: CÁLCULO DE TOTAIS PARA DASHBOARD ---
                total_entradas = df[df['tipo'] == 'Entrada']['valor'].sum()
                total_saidas = df[df['tipo'] == 'Saída']['valor'].sum()
                saldo_atual = total_entradas - total_saidas

                st.subheader("📊 Resumo Financeiro Atual")
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Entradas", f"R$ {total_entradas:,.2f}")
                m2.metric("Total Saídas", f"R$ {total_saidas:,.2f}", delta=f"-R$ {total_saidas:,.2f}", delta_color="inverse")
                m3.metric("Saldo em Caixa", f"R$ {saldo_atual:,.2f}", delta=f"R$ {saldo_atual:,.2f}")
                
                st.divider()

                col_tabela, col_grafico = st.columns([1, 1])
                with col_tabela:
                    st.write("**Histórico Recente**")
                    st.dataframe(df.sort_values(by='id', ascending=False), width='stretch', hide_index=True)
                with col_grafico:
                    st.write("**Gasto por Categoria**")
                    resumo = df[df['tipo'] == 'Saída'].groupby("categoria")["valor"].sum()
                    st.bar_chart(resumo)
                
                # --- EXPORTAR PDF ---
                st.divider()
                st.write("📂 **Exportar Relatório**")
                pdf_output = gerar_pdf(df)
                st.download_button("📥 Baixar Relatório em PDF", pdf_output, "financeiro.pdf", "application/pdf", use_container_width=True)

                # --- 🛠️ GERENCIAR (EDITAR / EXCLUIR) ---
                st.divider()
                st.subheader("🛠️ Gerenciar Registro Selecionado")
                
                dict_opcoes = {
                    f"ID {r['id']} | {r['data']} | {r['categoria']} (R$ {r['valor']})": r 
                    for _, r in df.iterrows()
                }
                
                selecionado_label = st.selectbox(
                    "Escolha um item para modificar ou excluir:", 
                    options=sorted(list(dict_opcoes.keys()), reverse=True)
                )
                
                if selecionado_label:
                    item = dict_opcoes[selecionado_label]
                    
                    with st.expander(f"📝 Editar Registro ID {item['id']}", expanded=True):
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            nova_data = st.date_input("Nova Data", value=pd.to_datetime(item['data']))
                            novo_valor = st.number_input("Novo Valor", value=float(item['valor']), key="edit_v")
                        with col_e2:
                            idx_cat = lista_categorias.index(item['categoria']) if item['categoria'] in lista_categorias else 0
                            nova_cat = st.selectbox("Nova Categoria", lista_categorias, index=idx_cat, key="edit_c")
                            novo_tipo = st.radio("Novo Tipo", ["Entrada", "Saída"], index=0 if item['tipo'] == "Entrada" else 1, horizontal=True)
                        
                        nova_obs = st.text_area("Nova Observação", value=item['observacao'] if item['observacao'] else "")

                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                                if atualizar_registro(item['id'], nova_data, nova_cat, novo_valor, novo_tipo, nova_obs):
                                    st.success("Atualizado com sucesso!")
                                    st.rerun()
                        with btn_col2:
                            if st.button("🗑️ Excluir Registro", use_container_width=True):
                                if deletar_registro(item['id']):
                                    st.warning("Removido!")
                                    st.rerun()
            else:
                st.info("Ainda não há lançamentos.")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")