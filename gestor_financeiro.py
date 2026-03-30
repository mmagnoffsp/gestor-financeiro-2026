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

# --- 2. FUNÇÃO PDF ---
def gerar_pdf(dataframe):
    ent_p = dataframe[dataframe['tipo'] == 'Entrada (Pagto)']['valor'].sum()
    sai_p = dataframe[dataframe['tipo'] == 'Saída (Pagto)']['valor'].sum()
    resgate = dataframe[dataframe['tipo'] == 'Baixa de Reserva']['valor'].sum()
    saldo_p = ent_p - sai_p
    ent_v = dataframe[dataframe['tipo'] == 'Entrada (Vale)']['valor'].sum()
    sai_v = dataframe[dataframe['tipo'] == 'Saída (Vale)']['valor'].sum()
    saldo_v = ent_v - sai_v

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "FECHAMENTO FINANCEIRO DETALHADO", ln=True, align="C")
    pdf.ln(5)

    # Quadro Pagamento
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 8, " 1. DEMONSTRATIVO DE PAGAMENTO", 1, ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(63, 8, f" Entradas: R$ {ent_p:.2f}", 1)
    pdf.cell(63, 8, f" Saidas: R$ {sai_p:.2f}", 1)
    pdf.cell(64, 8, f" Saldo: R$ {saldo_p:.2f}", 1, ln=True)
    pdf.ln(4)

    # Quadro Vale
    pdf.set_fill_color(210, 235, 210)
    pdf.cell(190, 8, " 2. DEMONSTRATIVO DE VALE", 1, ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(63, 8, f" Creditado: R$ {ent_v:.2f}", 1)
    pdf.cell(63, 8, f" Utilizado: R$ {sai_v:.2f}", 1)
    pdf.cell(64, 8, f" Saldo Cartao: R$ {saldo_v:.2f}", 1, ln=True)
    pdf.ln(10)

    # Tabela
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(20, 8, "Data", 1, 0, 'C', True)
    pdf.cell(40, 8, "Categoria", 1, 0, 'C', True)
    pdf.cell(25, 8, "Valor", 1, 0, 'C', True)
    pdf.cell(40, 8, "Tipo", 1, 0, 'C', True)
    pdf.cell(65, 8, "Obs", 1, 1, 'C', True)

    pdf.set_font("Arial", "", 7)
    for _, row in dataframe.iterrows():
        pdf.cell(20, 7, str(row['data']), 1)
        pdf.cell(40, 7, str(row['categoria'])[:25], 1)
        pdf.cell(25, 7, f"R$ {row['valor']:.2f}", 1)
        pdf.cell(40, 7, str(row['tipo']), 1)
        obs = str(row['observacao']) if row['observacao'] else "-"
        pdf.cell(65, 7, obs[:45], 1); pdf.ln()
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. INTERFACE ---
st.set_page_config(page_title="Gestor Financeiro ADS", layout="wide")

if verificar_senha():
    inicializar_banco()
    st.title("💰 Gestão Unificada: Pagamento & Vale")

    opcoes_tipo = ["Entrada (Pagto)", "Saída (Pagto)", "Entrada (Vale)", "Saída (Vale)", "Baixa de Reserva"]
    
    # LISTA ATUALIZADA COM DENTISTA/CLINICAS/HOSPITAL
    lista_categorias_base = [
        "açougue", "agua potavel", "areia pet", "barbearia", "condominio", 
        "dentista/clinicas/hospital", "deposito apartamento", "despesas emergenciais", 
        "diferenca reserva caixa", "enel", "gastos parcelados", "internet", 
        "lanche gean", "mercado", "pagamento recebido", "reserva caixa", 
        "vale recebido", "taxi/uber", "universidade", "vacina pets", "vivo celular"
    ]
    lista_categorias = sorted([item.title() for item in lista_categorias_base])

    # --- NOVO LANÇAMENTO ---
    with st.expander("➕ Novo Lançamento", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            data = st.date_input("Data")
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            categoria = st.selectbox("Categoria", lista_categorias)
        with c2:
            tipo = st.radio("Selecione a Origem:", opcoes_tipo)
        obs = st.text_input("📝 Finalidade / Observação")

        if st.button("Confirmar Lançamento", use_container_width=True):
            if valor > 0:
                if salvar_dados(data, categoria, valor, tipo, obs):
                    st.success("✅ Registrado com sucesso!"); st.rerun()

    st.divider()

    if engine:
        df = pd.read_sql("SELECT * FROM lancamentos", engine)
        if not df.empty:
            # DASHBOARD
            ent_p = df[df['tipo'] == 'Entrada (Pagto)']['valor'].sum()
            sai_p = df[df['tipo'] == 'Saída (Pagto)']['valor'].sum()
            saldo_p = ent_p - sai_p
            resgate = df[df['tipo'] == 'Baixa de Reserva']['valor'].sum()
            ent_v = df[df['tipo'] == 'Entrada (Vale)']['valor'].sum()
            sai_v = df[df['tipo'] == 'Saída (Vale)']['valor'].sum()
            saldo_v = ent_v - sai_v

            st.subheader("📊 Resumo de Fluxos")
            col_p, col_v = st.columns(2)
            with col_p:
                st.info("🏦 **CONTA PAGAMENTO**")
                cp1, cp2 = st.columns(2)
                cp1.metric("Saldo do Mês", f"R$ {saldo_p:,.2f}")
                cp2.metric("Uso Reserva", f"R$ {resgate:,.2f}")
            with col_v:
                st.success("💳 **CONTA VALE**")
                cv1, cv2 = st.columns(2)
                cv1.metric("Saldo Cartão", f"R$ {saldo_v:,.2f}")
                cv2.metric("Total Gasto", f"R$ {sai_v:,.2f}")

            st.divider()

            # HISTÓRICO
            st.write("**Histórico Detalhado**")
            st.dataframe(df.sort_values(by='id', ascending=False), hide_index=True)
            
            pdf_bytes = gerar_pdf(df)
            st.download_button("📥 Baixar Relatório", pdf_bytes, "fechamento.pdf", "application/pdf")

            # --- GERENCIAMENTO (EDITAR/DELETAR) ---
            st.subheader("🛠️ Gerenciar Registros")
            dict_itens = {f"ID {r['id']} | {r['data']} | {r['categoria']} - R$ {r['valor']:.2f}": r for _, r in df.iterrows()}
            item_selecionado = st.selectbox("Selecione um registro para Alterar ou Excluir:", options=sorted(list(dict_itens.keys()), reverse=True))
            
            if item_selecionado:
                reg = dict_itens[item_selecionado]
                col_ed1, col_ed2 = st.columns(2)
                
                with col_ed1:
                    try:
                        idx_cat = lista_categorias.index(reg['categoria'])
                    except:
                        idx_cat = 0
                    nova_categoria = st.selectbox("Alterar Categoria", lista_categorias, index=idx_cat, key="cat_edit")
                    novo_valor = st.number_input("Novo Valor", value=float(reg['valor']), key="val_edit")
                
                with col_ed2:
                    try:
                        idx_tipo = opcoes_tipo.index(reg['tipo'])
                    except:
                        idx_tipo = 0
                    novo_tipo = st.selectbox("Novo Tipo", opcoes_tipo, index=idx_tipo, key="tipo_edit")
                    nova_obs = st.text_input("Nova Obs", value=reg['observacao'] if reg['observacao'] else "", key="obs_edit")
                
                btn_at, btn_ex = st.columns(2)
                if btn_at.button("💾 Salvar Alterações", use_container_width=True):
                    if atualizar_registro(reg['id'], reg['data'], nova_categoria, novo_valor, novo_tipo, nova_obs):
                        st.success("✅ Registro atualizado!"); st.rerun()
                
                if btn_ex.button("🗑️ Excluir Registro", use_container_width=True, type="primary"):
                    if deletar_registro(reg['id']):
                        st.warning("⚠️ Registro removido!"); st.rerun()