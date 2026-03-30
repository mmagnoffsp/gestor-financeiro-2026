import streamlit as st
import pandas as pd
from database import inicializar_banco, salvar_dados, engine, deletar_registro, atualizar_registro
from fpdf import FPDF

# --- 1. FUNÇÃO DE SEGURANÇA ---
def verificar_senha():
    def login():
        senha_digitada = st.text_input("Senha de Acesso:", type="password")
        if st.button("Entrar"):
            if senha_digitada == "Ca10Mg43@#$":
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("🔑 Senha incorreta.")
    if "autenticado" not in st.session_state:
        st.title("🔒 Gestor Financeiro Privado")
        login()
        return False
    return True

# --- 2. FUNÇÃO PDF ATUALIZADA ---
def gerar_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio Financeiro Detalhado - ADS", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 8)
    pdf.cell(22, 10, "Data", 1)
    pdf.cell(40, 10, "Categoria", 1)
    pdf.cell(23, 10, "Valor", 1)
    pdf.cell(35, 10, "Origem/Tipo", 1)
    pdf.cell(70, 10, "Finalidade / Obs", 1)
    pdf.ln()

    pdf.set_font("Arial", "", 8)
    for _, row in dataframe.iterrows():
        pdf.cell(22, 10, str(row['data']), 1)
        pdf.cell(40, 10, str(row['categoria'])[:22], 1)
        pdf.cell(23, 10, f"R$ {row['valor']:.2f}", 1)
        pdf.cell(35, 10, str(row['tipo']), 1)
        obs = str(row['observacao']) if row['observacao'] else "-"
        pdf.cell(70, 10, obs[:40], 1)
        pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestor Financeiro ADS", layout="wide")

if verificar_senha():
    inicializar_banco()
    st.title("💰 Gestor Multi-Caixa (Pagamento & Vale)")

    if st.sidebar.button("Sair"):
        del st.session_state["autenticado"]
        st.rerun()

    lista_categorias_base = [
        "açougue", "agua potavel", "areia pet", "barbearia", "condominio",
        "deposito apartamento", "enel", "gastos parcelados", "internet", 
        "lanche gean", "mercado", "pagamento recebido", "vale recebido",
        "taxi/uber", "universidade", "vacina pets", "vivo celular"
    ]
    lista_categorias = sorted([item.title() for item in lista_categorias_base])

    # --- FORMULÁRIO COM SEPARAÇÃO ---
    with st.expander("➕ Novo Lançamento", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data")
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            categoria = st.selectbox("Categoria", lista_categorias)
        with col2:
            # BOTÕES SEPARADOS POR ORIGEM
            st.write("**Selecione a Origem e Tipo:**")
            opcoes_tipo = [
                "Entrada (Pagto)", "Saída (Pagto)", 
                "Entrada (Vale)", "Saída (Vale)", 
                "Baixa de Reserva"
            ]
            tipo = st.radio("Tipo de Movimentação", opcoes_tipo, horizontal=False)

        obs = st.text_input("📝 Finalidade / Observação")

        if st.button("Confirmar Lançamento", use_container_width=True):
            if valor > 0:
                if salvar_dados(data, categoria, valor, tipo, obs):
                    st.success(f"✅ Salvo em {tipo}!")
                    st.rerun()

    st.divider()

    # --- DASHBOARD DE SALDOS SEPARADOS ---
    if engine:
        try:
            df = pd.read_sql("SELECT * FROM lancamentos", engine)
            if not df.empty:
                # Cálculos PAGAMENTO
                ent_p = df[df['tipo'] == 'Entrada (Pagto)']['valor'].sum()
                sai_p = df[df['tipo'].isin(['Saída (Pagto)', 'Baixa de Reserva'])]['valor'].sum()
                saldo_p = ent_p - sai_p

                # Cálculos VALE
                ent_v = df[df['tipo'] == 'Entrada (Vale)']['valor'].sum()
                sai_v = df[df['tipo'] == 'Saída (Vale)']['valor'].sum()
                saldo_v = ent_v - sai_v

                st.subheader("📊 Resumo de Caixas")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.info("🏦 **Saldo Pagamento**")
                    st.metric("Disponível", f"R$ {saldo_p:,.2f}")
                with c2:
                    st.success("💳 **Saldo Vale**")
                    st.metric("Disponível", f"R$ {saldo_v:,.2f}")
                with c3:
                    st.warning("💰 **Total Geral**")
                    st.metric("Soma Total", f"R$ {(saldo_p + saldo_v):,.2f}")

                st.divider()
                
                # Histórico e Gráfico
                col_tab, col_grf = st.columns([1.2, 0.8])
                with col_tab:
                    st.write("**Histórico Recente**")
                    st.dataframe(df.sort_values(by='id', ascending=False), hide_index=True)
                with col_grf:
                    st.write("**Gastos por Categoria (Geral)**")
                    res = df[df['tipo'].str.contains('Saída|Baixa')].groupby("categoria")["valor"].sum()
                    st.bar_chart(res)

                # Exportar
                pdf_out = gerar_pdf(df)
                st.download_button("📥 Baixar Relatório", pdf_out, "financeiro.pdf", "application/pdf")

                # Gerenciamento (Edit/Delete)
                st.subheader("🛠️ Gerenciar")
                dict_op = {f"ID {r['id']} | {r['categoria']} ({r['tipo']})": r for _, r in df.iterrows()}
                sel = st.selectbox("Escolha um item:", options=sorted(list(dict_op.keys()), reverse=True))
                if sel:
                    item = dict_op[sel]
                    with st.expander("📝 Editar Registro"):
                        n_valor = st.number_input("Valor", value=float(item['valor']))
                        n_tipo = st.radio("Novo Tipo", opcoes_tipo, index=opcoes_tipo.index(item['tipo']) if item['tipo'] in opcoes_tipo else 0)
                        n_obs = st.text_input("Observação", value=item['observacao'] if item['observacao'] else "")
                        if st.button("💾 Atualizar"):
                            if atualizar_registro(item['id'], item['data'], item['categoria'], n_valor, n_tipo, n_obs):
                                st.success("Atualizado!"); st.rerun()

        except Exception as e:
            st.error(f"Erro: {e}")