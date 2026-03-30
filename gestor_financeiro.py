import streamlit as st
import pandas as pd
from database import inicializar_banco, salvar_dados, engine, deletar_registro, atualizar_registro
from fpdf import FPDF

# --- 1. FUNÇÃO DE SEGURANÇA ---
def verificar_senha():
    def login():
        senha_digitada = st.text_input("Digite a senha para acessar:", type="password")
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

# --- 2. FUNÇÃO PARA GERAR PDF ATUALIZADA ---
def gerar_pdf(dataframe):
    # Cálculos considerando Baixa de Reserva como saída
    t_entradas = dataframe[dataframe['tipo'] == 'Entrada']['valor'].sum()
    t_saidas = dataframe[dataframe['tipo'].isin(['Saída', 'Baixa de Reserva'])]['valor'].sum()
    saldo = t_entradas - t_saidas

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio Financeiro - Gestao de Caixa", ln=True, align="C")
    pdf.ln(10)
    
    # Cabeçalho ajustado para caber a Finalidade
    pdf.set_font("Arial", "B", 9)
    pdf.cell(22, 10, "Data", 1)
    pdf.cell(40, 10, "Categoria", 1)
    pdf.cell(23, 10, "Valor", 1)
    pdf.cell(32, 10, "Tipo", 1)
    pdf.cell(73, 10, "Finalidade / Obs", 1)
    pdf.ln()

    # Dados
    pdf.set_font("Arial", "", 8)
    for _, row in dataframe.iterrows():
        pdf.cell(22, 10, str(row['data']), 1)
        pdf.cell(40, 10, str(row['categoria'])[:22], 1)
        pdf.cell(23, 10, f"R$ {row['valor']:.2f}", 1)
        pdf.cell(32, 10, str(row['tipo']), 1)
        obs_texto = str(row['observacao']) if row['observacao'] else "-"
        pdf.cell(73, 10, obs_texto[:45], 1)
        pdf.ln()
    
    # Rodapé
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 8, f"Total Entradas: R$ {t_entradas:.2f}", ln=True)
    pdf.cell(190, 8, f"Total Saidas/Baixas: R$ {t_saidas:.2f}", ln=True)
    pdf.set_text_color(0, 128, 0) if saldo >= 0 else pdf.set_text_color(255, 0, 0)
    pdf.cell(190, 10, f"SALDO FINAL EM CAIXA: R$ {saldo:.2f}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestor Financeiro ADS", layout="wide")

# --- 4. INÍCIO DO APP ---
if verificar_senha():
    inicializar_banco()

    st.title("💰 Meu Gestor Financeiro - Cloud")

    if st.sidebar.button("Sair / Bloquear"):
        del st.session_state["autenticado"]
        st.rerun()

    # Categorias
    lista_categorias_base = [
        "açougue", "agua potavel", "areia pet", "barbearia", "condominio",
        "deposito apartamento pagamento", "deposito apartamento vale",
        "enel", "gastos parcelados", "internet", "lanche gean pagamento", 
        "lanche gean vale", "mercado", "pagamento recebido", 
        "reserva de caixa no vale", "reserva de caixa no pagamento", 
        "taxi/uber", "universidade", "vacina pets", "vale recebido", "vivo celular"
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
            # BOTÃO DE BAIXA DE RESERVA ADICIONADO AQUI
            tipo = st.radio("Tipo", ["Entrada", "Saída", "Baixa de Reserva"], horizontal=True)

        # CAMPO DE FINALIDADE (OBSERVAÇÃO)
        obs = st.text_input("📝 Finalidade (Para que foi usado o dinheiro?)", placeholder="Ex: Conserto da pia, Remédio, Retirada emergencial...")

        if st.button("Confirmar Lançamento", use_container_width=True):
            if valor > 0:
                if salvar_dados(data, categoria, valor, tipo, obs):
                    st.success(f"✅ Registrado: {categoria} como {tipo}")
                    st.rerun() 
            else:
                st.warning("O valor deve ser maior que zero.")

    st.divider()

    # --- DASHBOARD ---
    if engine:
        try:
            df = pd.read_sql("SELECT * FROM lancamentos", engine)

            if not df.empty:
                # Cálculos do Dashboard
                total_ent = df[df['tipo'] == 'Entrada']['valor'].sum()
                total_sai = df[df['tipo'].isin(['Saída', 'Baixa de Reserva'])]['valor'].sum()
                saldo_real = total_ent - total_sai

                st.subheader("📊 Resumo Financeiro Atual")
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Entradas", f"R$ {total_ent:,.2f}")
                m2.metric("Saídas + Baixas", f"R$ {total_sai:,.2f}", delta_color="inverse")
                m3.metric("Saldo Real em Caixa", f"R$ {saldo_real:,.2f}")
                
                st.divider()

                col_tabela, col_grafico = st.columns([1.2, 0.8])
                with col_tabela:
                    st.write("**Histórico de Lançamentos**")
                    st.dataframe(df.sort_values(by='id', ascending=False), hide_index=True)
                with col_grafico:
                    st.write("**Consumo por Categoria (Saídas e Baixas)**")
                    resumo = df[df['tipo'].isin(['Saída', 'Baixa de Reserva'])].groupby("categoria")["valor"].sum()
                    st.bar_chart(resumo)
                
                # --- EXPORTAÇÃO ---
                st.divider()
                st.write("📂 **Exportar Dados**")
                pdf_output = gerar_pdf(df)
                st.download_button("📥 Baixar Relatório em PDF", pdf_output, "financeiro_ads.pdf", "application/pdf", use_container_width=True)

                # --- GERENCIAMENTO (EDITAR/EXCLUIR) ---
                st.divider()
                st.subheader("🛠️ Gerenciar Registro")
                dict_opcoes = {f"ID {r['id']} | {r['categoria']} (R$ {r['valor']})": r for _, r in df.iterrows()}
                selecionado = st.selectbox("Selecione para editar ou excluir:", options=sorted(list(dict_opcoes.keys()), reverse=True))
                
                if selecionado:
                    item = dict_opcoes[selecionado]
                    with st.expander("📝 Formulário de Edição"):
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            n_data = st.date_input("Nova Data", value=pd.to_datetime(item['data']))
                            n_valor = st.number_input("Novo Valor", value=float(item['valor']), key="edit_v")
                        with ce2:
                            n_cat = st.selectbox("Nova Categoria", lista_categorias, index=lista_categorias.index(item['categoria']) if item['categoria'] in lista_categorias else 0)
                            opcoes_tipo = ["Entrada", "Saída", "Baixa de Reserva"]
                            n_tipo = st.radio("Novo Tipo", opcoes_tipo, index=opcoes_tipo.index(item['tipo']) if item['tipo'] in opcoes_tipo else 1)
                        
                        n_obs = st.text_input("Nova Finalidade", value=item['observacao'] if item['observacao'] else "")

                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("💾 Salvar Alterações", type="primary"):
                                if atualizar_registro(item['id'], n_data, n_cat, n_valor, n_tipo, n_obs):
                                    st.success("Alterado!"); st.rerun()
                        with b2:
                            if st.button("🗑️ Excluir permanentemente"):
                                if deletar_registro(item['id']):
                                    st.warning("Excluído!"); st.rerun()
            else:
                st.info("Nenhum dado encontrado no banco de dados.")
        except Exception as e:
            st.error(f"Erro ao processar dados: {e}")