import streamlit as st
import pandas as pd
from database import inicializar_banco, salvar_dados, engine, deletar_registro, atualizar_registro
from fpdf import FPDF
import plotly.express as px

# --- 1. FUNÇÃO DE SEGURANÇA E CONTROLE DE ACESSO ---
# Esta função garante que apenas usuários autorizados acessem os dados.
def verificar_senha():
    def login():
        st.markdown("### 🔑 Autenticação de Usuário ADS")
        senha_p = st.text_input("Informe a Senha de Acesso:", type="password")
        
        # Botão de validação de credenciais com novo parâmetro width
        if st.button("Acessar Painel Financeiro", width="stretch"):
            if senha_p == "Ca10Mg43@#$":
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("⚠️ Senha incorreta. Verifique suas credenciais.")

    # Verifica se o estado de autenticação já existe na sessão
    if "autenticado" not in st.session_state:
        st.title("🔒 Gestor Financeiro Privado - Carlos Magno")
        login()
        return False
    return True

# --- 2. FUNÇÃO DE GERAÇÃO DE RELATÓRIO PDF ---
# Gera um documento formatado com os saldos de cada departamento.
def gerar_pdf(dataframe):
    # Cálculos de somatória para o corpo do PDF
    ent_p = dataframe[dataframe['tipo'] == 'Entrada (Pagto)']['valor'].sum()
    sai_p = dataframe[dataframe['tipo'] == 'Saída (Pagto)']['valor'].sum()
    
    # Lógica específica para o Fundo de Reserva
    res_g = dataframe[dataframe['tipo'] == 'Reserva (Entrada)']['valor'].sum()
    res_u = dataframe[dataframe['tipo'] == 'Baixa Reserva (Saída)']['valor'].sum()
    
    # Cálculo dos saldos finais para o relatório
    s_reserva = res_g - res_u
    s_pagamento = ent_p - sai_p 

    # Início da construção do layout do PDF usando FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "RELATÓRIO DE FECHAMENTO FINANCEIRO", ln=True, align="C")
    pdf.ln(10)

    # Seção 1: Conta Principal (Pagamentos)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, " 1. FLUXO DE CAIXA - CONTA PAGAMENTO", 1, ln=True, fill=True)
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(63, 10, f" Total Entradas: R$ {ent_p:.2f}", 1)
    pdf.cell(63, 10, f" Total Saídas: R$ {sai_p:.2f}", 1)
    pdf.cell(64, 10, f" Saldo Atual: R$ {s_pagamento:.2f}", 1, ln=True)
    
    pdf.ln(5)
    
    # Seção 2: Reserva de Emergência (Caixa)
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, " 2. RESERVA E FUNDO DE EMERGÊNCIA", 1, ln=True, fill=True)
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(63, 10, f" Valor Guardado: R$ {res_g:.2f}", 1)
    pdf.cell(63, 10, f" Valor Retirado: R$ {res_u:.2f}", 1)
    pdf.cell(64, 10, f" Saldo Líquido: R$ {s_reserva:.2f}", 1, ln=True)
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. CONFIGURAÇÃO DA INTERFACE E DICIONÁRIOS ---
st.set_page_config(page_title="Gestor Financeiro ADS", layout="wide")

# Fluxo principal do sistema
if verificar_senha():
    inicializar_banco()
    st.title("💰 Gestão Financeira: Departamentos e Clientes")

    # Definição dos tipos de transação aceitos
    opcoes_tipo = [
        "Entrada (Pagto)", "Saída (Pagto)", "Entrada (Vale)", "Saída (Vale)", 
        "Reserva (Entrada)", "Baixa Reserva (Saída)", "Entrada (Férias)", 
        "Saída (Férias)", "Entrada (13º Sal)", "Saída (13º Sal)"
    ]
    
    # Categorias padronizadas para o sistema
    lista_cat_raw = [
        "açougue", "agua potavel", "areia pet", "barbearia", "condominio", 
        "dentista/clinicas/hospital", "deposito apartamento", "despesas emergenciais", 
        "enel", "gastos parcelados", "internet", "lanche gean", "mercado", 
        "pagamento recebido", "reserva caixa", "taxi/uber", "universidade", 
        "vacina pets", "vivo celular"
    ]
    lista_categorias = sorted([item.title() for item in lista_cat_raw])

    # Inicialização de estados para formulários Streamlit
    if "input_cat" not in st.session_state: st.session_state.input_cat = lista_categorias[0]
    if "input_obs" not in st.session_state: st.session_state.input_obs = ""
    if "input_tipo" not in st.session_state: st.session_state.input_tipo = "Entrada (Pagto)"

    # --- SEÇÃO DE LANÇAMENTO E ATALHOS RÁPIDOS ---
    with st.expander("➕ Registrar Novo Lançamento Detalhado", expanded=True):
        st.write("**Atalhos de Entrada Rápida para Folha:**")
        b_f, b_13_1, b_13_2 = st.columns(3)
        
        if b_f.button("🌴 Lançar Férias", width="stretch"):
            st.session_state.input_cat = "Pagamento Recebido"
            st.session_state.input_tipo = "Entrada (Férias)"
            st.session_state.input_obs = "Recebimento Férias"
            
        if b_13_1.button("💰 13º (1ª Parc)", width="stretch"):
            st.session_state.input_cat = "Pagamento Recebido"
            st.session_state.input_tipo = "Entrada (13º Sal)"
            st.session_state.input_obs = "13º Salário 1a Parc"
            
        if b_13_2.button("💰 13º (2ª Parc)", width="stretch"):
            st.session_state.input_cat = "Pagamento Recebido"
            st.session_state.input_tipo = "Entrada (13º Sal)"
            st.session_state.input_obs = "13º Salário 2a Parc"

        st.divider()
        cl1, cl2, cl3 = st.columns(3)
        with cl1:
            data = st.date_input("Data do Registro")
            valor = st.number_input("Valor R$", min_value=0.0, format="%.2f")
        with cl2:
            categoria = st.selectbox("Categoria", lista_categorias)
            tipo = st.selectbox("Departamento", opcoes_tipo)
        with cl3:
            nome_cli = st.text_input("👤 Cliente", placeholder="Ex: Mercado Livre")
            obs_texto = st.text_input("📝 Obs", value=st.session_state.input_obs)

        # Botão de confirmação com lógica de transação dupla para RESERVA
        if st.button("💾 Confirmar Lançamento no Sistema", width="stretch", type="primary"):
            if valor > 0:
                obs_f = f"[{nome_cli.upper() if nome_cli else 'GERAL'}] {obs_texto}"
                # CORREÇÃO: Lógica para conversar entre os caixas automaticamente
                if categoria == "Reserva Caixa" and tipo == "Saída (Pagto)":
                    salvar_dados(data, categoria, valor, "Saída (Pagto)", f"{obs_f} (Transferência)")
                    salvar_dados(data, categoria, valor, "Reserva (Entrada)", f"{obs_f} (Recebido)")
                    st.success("💎 Reserva Alimentada com Sucesso!"); st.rerun()
                else:
                    salvar_dados(data, categoria, valor, tipo, obs_f)
                    st.success("✅ Registro salvo!"); st.rerun()

    st.divider()

    # --- 4. PROCESSAMENTO DE DADOS E VISUALIZAÇÃO ---
    if engine:
        df = pd.read_sql("SELECT * FROM lancamentos", engine)
        if not df.empty:
            df['Cliente_Tag'] = df['observacao'].apply(lambda x: x.split(']')[0].replace('[', '') if x and x.startswith('[') else 'GERAL')
            st.sidebar.header("🔍 Filtros")
            f_cli = st.sidebar.selectbox("Filtrar por Cliente:", ["TODOS"] + sorted(df['Cliente_Tag'].unique().tolist()))
            df_res = df if f_cli == "TODOS" else df[df['Cliente_Tag'] == f_cli]

            def calc_totais(e_t, s_t):
                e = df_res[df_res['tipo'] == e_t]['valor'].sum()
                s = df_res[df_res['tipo'] == s_t]['valor'].sum()
                return e, s, e - s

            e_p, s_p, sal_p = calc_totais('Entrada (Pagto)', 'Saída (Pagto)')
            e_r, s_r, sal_r = calc_totais('Reserva (Entrada)', 'Baixa Reserva (Saída)')
            e_v, s_v, sal_v = calc_totais('Entrada (Vale)', 'Saída (Vale)')
            e_f, s_f, sal_f = calc_totais('Entrada (Férias)', 'Saída (Férias)')
            e_13, s_13, sal_13 = calc_totais('Entrada (13º Sal)', 'Saída (13º Sal)')

            st.subheader(f"📊 Painel Financeiro: {f_cli}")
            m1, m2, m3 = st.columns(3)
            m1.info("🏦 **PAGAMENTO**"); m1.metric("Sobra", f"R$ {sal_p:,.2f}"); m1.caption(f"E: {e_p:.2f} | S: {s_p:.2f}")
            m2.warning("🛡️ **RESERVA**"); m2.metric("Saldo", f"R$ {sal_r:,.2f}"); m2.caption(f"G: {e_r:.2f} | U: {s_r:.2f}")
            m3.success("💳 **CONTA VALE**"); m3.metric("Saldo", f"R$ {sal_v:,.2f}"); m3.caption(f"E: {e_v:.2f} | S: {s_v:.2f}")

            m4, m5 = st.columns(2)
            m4.write("**🌴 SALDO FÉRIAS**"); m4.metric("Disponível", f"R$ {sal_f:,.2f}")
            m5.write("**💰 SALDO 13º SALÁRIO**"); m5.metric("Disponível", f"R$ {sal_13:,.2f}")

            st.divider()
            df_graf = df_res[df_res['tipo'].str.contains('Saída')]
            if not df_graf.empty:
                st.subheader("🍕 Distribuição de Gastos")
                fig = px.pie(df_graf, values='valor', names='categoria', hole=0.4)
                st.plotly_chart(fig, width='stretch')

            st.subheader("📝 Histórico")
            st.dataframe(df_res.sort_values(by='id', ascending=False), hide_index=True, width='stretch')
            st.download_button("📥 Baixar PDF", gerar_pdf(df), "financeiro.pdf", "application/pdf", width='stretch')

            st.divider()
            st.subheader("🛠️ Ferramentas de Edição")
            lista_edit = {f"ID {r['id']} | {r['data']} | {r['observacao']}": r for _, r in df_res.iterrows()}
            item_sel = st.selectbox("Escolha um item:", options=sorted(list(lista_edit.keys()), reverse=True))
            if item_sel:
                reg = lista_edit[item_sel]; ed1, ed2 = st.columns(2)
                with ed1:
                    v_novo = st.number_input("Valor", value=float(reg['valor']), key="edit_v")
                    try: idx_t = opcoes_tipo.index(reg['tipo'])
                    except: idx_t = 0
                    t_novo = st.selectbox("Tipo", opcoes_tipo, index=idx_t)
                with ed2:
                    c_nova = st.selectbox("Categoria", lista_categorias, index=lista_categorias.index(reg['categoria']) if reg['categoria'] in lista_categorias else 0)
                    o_nova = st.text_input("Observação", value=reg['observacao'])
                btn_s, btn_e = st.columns(2)
                if btn_s.button("💾 Salvar", width="stretch"):
                    if atualizar_registro(reg['id'], reg['data'], c_nova, v_novo, t_novo, o_nova): st.rerun()
                if btn_e.button("🗑️ Excluir", type="primary", width="stretch"):
                    if deletar_registro(reg['id']): st.rerun()

# --- LINHA FINAL 210: GESTÃO COMPLETA ADS ---