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
    
    reserva_guardada = dataframe[(dataframe['categoria'] == 'Reserva Caixa') & (dataframe['tipo'] == 'Saída (Pagto)')]['valor'].sum()
    reserva_usada = dataframe[dataframe['tipo'] == 'Baixa de Reserva']['valor'].sum()
    saldo_reserva = reserva_guardada - reserva_usada
    
    saldo_p = ent_p - sai_p 

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "FECHAMENTO FINANCEIRO DETALHADO", ln=True, align="C")
    pdf.ln(5)

    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 8, " 1. CONTA PAGAMENTO", 1, ln=True, fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(63, 8, f" Entradas: R$ {ent_p:.2f}", 1)
    pdf.cell(63, 8, f" Saidas: R$ {sai_p:.2f}", 1)
    pdf.cell(64, 8, f" Sobra Atual: R$ {saldo_p:.2f}", 1, ln=True)
    pdf.ln(4)

    pdf.set_fill_color(200, 220, 255)
    pdf.cell(190, 8, " 2. RESERVA CAIXA (FUNDO)", 1, ln=True, fill=True)
    pdf.cell(63, 8, f" Guardado: R$ {reserva_guardada:.2f}", 1)
    pdf.cell(63, 8, f" Usado: R$ {reserva_usada:.2f}", 1)
    pdf.cell(64, 8, f" Saldo Fundo: R$ {saldo_reserva:.2f}", 1, ln=True)
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. INTERFACE ---
st.set_page_config(page_title="Gestor Financeiro ADS", layout="wide")

if verificar_senha():
    inicializar_banco()
    st.title("💰 Gestão Unificada: Pagamento & Vale")

    opcoes_tipo = ["Entrada (Pagto)", "Saída (Pagto)", "Entrada (Vale)", "Saída (Vale)", "Baixa de Reserva"]
    
    lista_categorias_base = [
        "açougue", "agua potavel", "areia pet", "barbearia", "condominio", 
        "dentista/clinicas/hospital", "deposito apartamento", "despesas emergenciais", 
        "diferenca reserva caixa", "enel", "gastos parcelados", "internet", 
        "lanche gean", "mercado", "pagamento recebido", "reserva caixa", 
        "vale recebido", "taxi/uber", "universidade", "vacina pets", "vivo celular"
    ]
    lista_categorias = sorted([item.title() for item in lista_categorias_base])

    # Inicialização de estados para os botões de atalho
    if "input_cat" not in st.session_state: st.session_state.input_cat = lista_categorias[0]
    if "input_obs" not in st.session_state: st.session_state.input_obs = ""
    if "input_tipo" not in st.session_state: st.session_state.input_tipo = "Entrada (Pagto)"

    with st.expander("➕ Novo Lançamento", expanded=True):
        st.write("**Atalhos de Entrada Rápida:**")
        bt1, bt2, bt3 = st.columns(3)
        
        if bt1.button("🌴 Férias", use_container_width=True):
            st.session_state.input_cat = "Pagamento Recebido"
            st.session_state.input_tipo = "Entrada (Pagto)"
            st.session_state.input_obs = "Recebimento de Férias"
            
        if bt2.button("💰 13º Salário (1ª Parc)", use_container_width=True):
            st.session_state.input_cat = "Pagamento Recebido"
            st.session_state.input_tipo = "Entrada (Pagto)"
            st.session_state.input_obs = "13º Salário - 1ª Parcela"
            
        if bt3.button("💰 13º Salário (2ª Parc)", use_container_width=True):
            st.session_state.input_cat = "Pagamento Recebido"
            st.session_state.input_tipo = "Entrada (Pagto)"
            st.session_state.input_obs = "13º Salário - 2ª Parcela"

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            data = st.date_input("Data")
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            
            # Ajusta o index conforme o atalho clicado
            try:
                idx_cat = lista_categorias.index(st.session_state.input_cat)
            except:
                idx_cat = 0
            categoria = st.selectbox("Categoria", lista_categorias, index=idx_cat)
            
        with c2:
            try:
                idx_tipo = opcoes_tipo.index(st.session_state.input_tipo)
            except:
                idx_tipo = 0
            tipo = st.radio("Selecione a Origem:", opcoes_tipo, index=idx_tipo)
            
        obs = st.text_input("📝 Finalidade / Observação", value=st.session_state.input_obs)

        if st.button("Confirmar Lançamento", use_container_width=True, type="primary"):
            if valor > 0:
                if salvar_dados(data, categoria, valor, tipo, obs):
                    st.success("✅ Registrado com sucesso!")
                    # Limpa os campos após salvar
                    st.session_state.input_cat = lista_categorias[0]
                    st.session_state.input_obs = ""
                    st.rerun()

    st.divider()

    if engine:
        df = pd.read_sql("SELECT * FROM lancamentos", engine)
        if not df.empty:
            ent_p = df[df['tipo'] == 'Entrada (Pagto)']['valor'].sum()
            sai_p = df[df['tipo'] == 'Saída (Pagto)']['valor'].sum()
            saldo_p = ent_p - sai_p 
            
            reserva_guardada = df[(df['categoria'] == 'Reserva Caixa') & (df['tipo'] == 'Saída (Pagto)')]['valor'].sum()
            reserva_usada = df[df['tipo'] == 'Baixa de Reserva']['valor'].sum()
            saldo_reserva = reserva_guardada - reserva_usada

            ent_v = df[df['tipo'] == 'Entrada (Vale)']['valor'].sum()
            sai_v = df[df['tipo'] == 'Saída (Vale)']['valor'].sum()
            saldo_v = ent_v - sai_v

            st.subheader("📊 Resumo de Fluxos")
            col_p, col_r, col_v = st.columns(3)
            
            with col_p:
                st.info("🏦 **CONTA PAGAMENTO**")
                st.metric("Sobra do Montante", f"R$ {saldo_p:,.2f}")
                st.caption(f"Entradas: R$ {ent_p:.2f} | Saídas: R$ {sai_p:.2f}")

            with col_r:
                st.warning("🛡️ **RESERVA CAIXA**")
                st.metric("Saldo no Fundo", f"R$ {saldo_reserva:,.2f}")
                st.write(f"📥 Guardado: R$ {reserva_guardada:.2f}")
                st.write(f"📤 Usado: R$ {reserva_usada:.2f}")

            with col_v:
                st.success("💳 **CONTA VALE**")
                st.metric("Saldo Cartão", f"R$ {saldo_v:,.2f}")
                st.caption(f"Gasto: R$ {sai_v:.2f}")

            st.divider()
            
            st.write("**Histórico Detalhado**")
            st.dataframe(df.sort_values(by='id', ascending=False), hide_index=True)
            
            pdf_bytes = gerar_pdf(df)
            st.download_button("📥 Baixar Relatório", pdf_bytes, "fechamento.pdf", "application/pdf")

            st.subheader("🛠️ Gerenciar Registros")
            dict_itens = {f"ID {r['id']} | {r['data']} | {r['categoria']} - R$ {r['valor']:.2f}": r for _, r in df.iterrows()}
            item_selecionado = st.selectbox("Selecione um registro para editar:", options=sorted(list(dict_itens.keys()), reverse=True))
            
            if item_selecionado:
                reg = dict_itens[item_selecionado]
                col_ed1, col_ed2 = st.columns(2)
                with col_ed1:
                    nova_cat = st.selectbox("Alterar Categoria", lista_categorias, index=lista_categorias.index(reg['categoria']) if reg['categoria'] in lista_categorias else 0, key="edit_cat")
                    novo_val = st.number_input("Novo Valor", value=float(reg['valor']), key="edit_val")
                with col_ed2:
                    novo_t = st.selectbox("Novo Tipo", opcoes_tipo, index=opcoes_tipo.index(reg['tipo']) if reg['tipo'] in opcoes_tipo else 0, key="edit_tipo")
                    nova_o = st.text_input("Nova Obs", value=reg['observacao'] or "", key="edit_obs")
                
                b1, b2 = st.columns(2)
                if b1.button("💾 Salvar Alterações", use_container_width=True):
                    if atualizar_registro(reg['id'], reg['data'], nova_cat, novo_val, novo_t, nova_o):
                        st.rerun()
                if b2.button("🗑️ Excluir Registro", type="primary", use_container_width=True):
                    if deletar_registro(reg['id']):
                        st.rerun()