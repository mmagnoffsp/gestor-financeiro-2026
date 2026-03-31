import streamlit as st
import pandas as pd
from database import inicializar_banco, salvar_dados, engine, deletar_registro, atualizar_registro
from fpdf import FPDF
import plotly.express as px
from datetime import datetime

# ==============================================================================
# --- 1. FUNÇÃO DE SEGURANÇA E CONTROLE DE ACESSO (AUTENTICAÇÃO) ---
# Camada de proteção para garantir a integridade dos dados financeiros.
# Desenvolvido por: Carlos Magno - Estudante de ADS (Anhembi Morumbi)
# ==============================================================================
def verificar_senha():
    """
    Gerencia o estado de autenticação da sessão. 
    Utiliza o Streamlit Session State para persistir o login.
    """
    def login():
        st.markdown("---")
        st.markdown("### 🔑 Autenticação de Usuário ADS")
        st.write("Acesso restrito ao ecossistema de gestão privada.")
        
        # Entrada de senha com máscara de caracteres de segurança
        senha_p = st.text_input("Informe a Senha de Segurança:", type="password", key="login_pass")
        
        # Acionamento do motor de validação (Padrão 2026: width='stretch')
        if st.button("Acessar Painel Financeiro", width="stretch"):
            # Validação baseada na regra de negócio do proprietário
            if senha_p == "Ca10Mg43@#$":
                st.session_state["autenticado"] = True
                st.success("Credenciais validadas. Redirecionando...")
                st.rerun()
            else:
                st.error("⚠️ Senha incorreta. Verifique suas credenciais de acesso.")
        
        st.markdown("---")
        st.caption("Desenvolvido para fins acadêmicos e profissionais - ADS 2026")

    # Verificação de persistência da autenticação no navegador
    if "autenticado" not in st.session_state:
        st.title("🔒 Portal de Gestão Privada - Carlos Magno")
        login()
        return False
        
    return True

# ==============================================================================
# --- 2. FUNÇÃO DE GERAÇÃO DE RELATÓRIO PDF (AUDITORIA E FECHAMENTO) ---
# Gera um documento PDF técnico com separação explícita de Clientes.
# ==============================================================================
def gerar_pdf(dataframe):
    """
    Converte o DataFrame filtrado em um arquivo binário PDF.
    Implementa lógica de cores para diferenciar Entradas e Saídas.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Configuração de Identidade Visual do Relatório
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "RELATÓRIO DE FECHAMENTO FINANCEIRO DETALHADO", ln=True, align="C")
    
    # Metadados de extração e auditoria
    pdf.set_font("Arial", "I", 8)
    data_emissao = datetime.now().strftime('%d/%m/%Y %H:%M')
    pdf.cell(190, 10, f"Documento extraído em: {data_emissao}", ln=True, align="R")
    pdf.ln(5)

    # Bloco 1: Sumário de Fluxo de Caixa Consolidado
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, " 1. RESUMO CONSOLIDADO DE FLUXO", 1, ln=True, fill=True)
    
    # Filtros de soma para métricas rápidas no topo do PDF
    val_entradas = dataframe[dataframe['tipo'].str.contains('Entrada')]['valor'].sum()
    val_saidas = dataframe[dataframe['tipo'].str.contains('Saída|Baixa')]['valor'].sum()
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, f" Total Acumulado Entradas: R$ {val_entradas:.2f}", 1)
    pdf.cell(95, 8, f" Total Acumulado Saídas: R$ {val_saidas:.2f}", 1, ln=True)
    pdf.ln(5)

    # Bloco 2: Tabela Detalhada de Lançamentos
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(190, 10, " 2. LISTAGEM TÉCNICA DE LANÇAMENTOS POR CLIENTE", 1, ln=True, fill=True)
    
    # Estrutura de colunas ajustada para legibilidade em A4
    # Config: Data, Cliente, Categoria, Departamento, Valor, Observação
    headers_pdf = [
        ("Data", 22), ("Cliente", 35), ("Categoria", 35), 
        ("Departamento", 35), ("Valor", 23), ("Obs", 40)
    ]
    
    # Renderização da linha de cabeçalho da tabela
    for titulo, largura in headers_pdf:
        pdf.cell(largura, 8, titulo, 1, 0, "C", True)
    pdf.ln(8)

    # Preenchimento das linhas com dados do banco
    pdf.set_font("Arial", "", 8)
    df_pdf_lista = dataframe.sort_values(by='id', ascending=False)

    for index, row in df_pdf_lista.iterrows():
        # Lógica de Semântica Visual para Auditoria
        if any(termo in str(row['tipo']) for termo in ["Saída", "Baixa"]):
            pdf.set_text_color(180, 0, 0) # Alerta para Débitos
        else:
            pdf.set_text_color(0, 100, 0) # Confirmação para Créditos
            
        pdf.cell(22, 7, str(row['data']), 1)
        pdf.cell(35, 7, str(row['Cliente'])[:18], 1)
        pdf.cell(35, 7, str(row['categoria'])[:18], 1)
        pdf.cell(35, 7, str(row['tipo'])[:18], 1)
        pdf.cell(23, 7, f"R$ {row['valor']:.2f}", 1, 0, "R")
        
        # Reset de cor para a coluna de observação (Preto padrão)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 7, str(row['Obs_Limpa'])[:22], 1, 1)

    # Codificação para transferência de dados via Streamlit
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# ==============================================================================
# --- 3. CONFIGURAÇÃO DO AMBIENTE STREAMLIT E PARÂMETROS ---
# ==============================================================================
st.set_page_config(
    page_title="Gestor Financeiro ADS", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

if verificar_senha():
    # Sincronização com o motor de banco de dados (SQLAlchemy)
    inicializar_banco()
    
    st.title("💰 Sistema de Gestão Financeira Integrada")
    st.markdown("### Interface de Operação Carlos Magno")

    # Definição dos Domínios de Departamento (Regras Operacionais)
    opcoes_tipo = [
        "Entrada (Pagto)", "Saída (Pagto)", "Entrada (Vale)", "Saída (Vale)", 
        "Reserva (Entrada)", "Baixa Res (Saída)", "Entrada (Férias)", 
        "Saída (Férias)", "Entrada (13º Sal)", "Saída (13º Sal)"
    ]
    
    # Lista de Categorias Expandida e Ordenada
    categorias_brutas = [
        "açougue", "agua potavel", "areia pet", "baixa de reserva", "barbearia", 
        "condominio", "dentista/clinicas/hospital", "deposito apartamento", 
        "despesas emergenciais", "enel", "gastos parcelados", "internet", 
        "lanche gean", "mercado", "pagamento recebido", "reserva caixa", 
        "taxi/uber", "universidade", "vacina pets", "vivo celular"
    ]
    lista_categorias = sorted([c.title() for c in categorias_brutas])
    
    # Controle de estado para injeção de texto via atalhos
    if "input_obs" not in st.session_state:
        st.session_state.input_obs = ""

    # --- SEÇÃO: REGISTRO DE LANÇAMENTOS ---
    with st.expander("➕ Inserir Novo Lançamento Financeiro", expanded=True):
        st.markdown("#### Painel de Atalhos Rápidos")
        
        # Grid de botões com suporte ao padrão width='stretch'
        bt_col1, bt_col2, bt_col3 = st.columns(3)
        
        if bt_col1.button("🌴 Lançar Férias", width="stretch"):
            st.session_state.input_obs = "Recebimento Férias"
            st.rerun()
            
        if bt_col2.button("💰 13º Salário (1ª)", width="stretch"):
            st.session_state.input_obs = "13º Salário 1a Parc"
            st.rerun()
            
        if bt_col3.button("💰 13º Salário (2ª)", width="stretch"):
            st.session_state.input_obs = "13º Salário 2a Parc"

        st.divider()
        
        # Matriz de campos do formulário principal
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            data_reg = st.date_input("Data do Evento")
            valor_reg = st.number_input("Valor Operacional (R$)", min_value=0.0, format="%.2f")
            
        with f_col2:
            cat_reg = st.selectbox("Categoria", lista_categorias)
            tipo_reg = st.selectbox("Departamento", opcoes_tipo)
            
        with f_col3:
            # Lógica de Identificação: Cliente é convertido para MAIÚSCULO por padrão
            cli_nome = st.text_input("👤 Nome do Cliente", placeholder="EX: MERCADO LIVRE").upper()
            obs_input = st.text_input("📝 Descrição", value=st.session_state.input_obs)

        # Mecanismo de persistência (Com validação de segurança)
        if st.button("💾 Confirmar Lançamento no Sistema", width="stretch", type="primary"):
            if valor_reg > 0:
                # Encapsulamento da tag de cliente na observação para manter compatibilidade SQL
                cli_formatado = cli_nome if cli_nome else "GERAL"
                obs_persist = f"[{cli_formatado}] {obs_input}"
                
                # Gravação no banco de dados
                salvar_dados(data_reg, cat_reg, valor_reg, tipo_reg, obs_persist)
                st.success(f"Lançamento vinculado a {cli_formatado} salvo com sucesso!")
                st.rerun()
            else:
                st.warning("Operação abortada: O valor deve ser superior a R$ 0.00")

    st.divider()

    # ==============================================================================
    # --- 4. MOTOR DE PROCESSAMENTO E DASHBOARD ANALÍTICO ---
    # ==============================================================================
    if engine:
        # Extração de dados via motor SQLAlchemy
        df_sql = pd.read_sql("SELECT * FROM lancamentos", engine)
        
        if not df_sql.empty:
            # Lógica de Parsing de Strings (Fundamental para o curso de ADS)
            # Extraímos o cliente da tag [CLIENTE] e limpamos a observação original
            df_sql['Cliente'] = df_sql['observacao'].apply(
                lambda x: x.split(']')[0].replace('[', '') if ']' in str(x) else 'GERAL'
            )
            df_sql['Obs_Limpa'] = df_sql['observacao'].apply(
                lambda x: x.split(']')[1].strip() if ']' in str(x) else x
            )
            
            # Filtro Lateral de Seleção
            st.sidebar.header("🔍 Central de Filtros")
            clientes_db = ["TODOS"] + sorted(df_sql['Cliente'].unique().tolist())
            filtro_sel = st.sidebar.selectbox("Visualizar Cliente:", clientes_db)
            
            # Aplicação dinâmica de filtros no DataFrame
            df_final = df_sql if filtro_sel == "TODOS" else df_sql[df_sql['Cliente'] == filtro_sel]

            # Área de Histórico Operacional
            st.subheader(f"📝 Histórico de Transações: {filtro_sel}")
            
            # Reordenação de colunas para foco no Cliente e Valor
            df_view_final = df_final.copy().sort_values(by='id', ascending=False)
            colunas_grid = ['id', 'data', 'Cliente', 'categoria', 'valor', 'tipo', 'Obs_Limpa']
            
            # Renderização da Tabela (Padrão 2026: width='stretch')
            st.dataframe(df_view_final[colunas_grid], hide_index=True, width="stretch")
            
            # Botão de Exportação de PDF Detalhado
            data_pdf_bin = gerar_pdf(df_final)
            st.download_button(
                label="📥 Baixar Relatório Consolidado (PDF)",
                data=data_pdf_bin,
                file_name=f"relatorio_financeiro_{filtro_sel.lower()}.pdf",
                mime="application/pdf",
                width="stretch"
            )

            st.divider()
            
            # Blocos Visuais de BI (Business Intelligence)
            st.subheader("📊 Distribuição de Despesas por Categoria")
            df_bi_gastos = df_final[df_final['tipo'].str.contains('Saída|Baixa')]
            
            if not df_bi_gastos.empty:
                fig_bi = px.pie(df_bi_gastos, values='valor', names='categoria', hole=0.4)
                st.plotly_chart(fig_bi, width="stretch")
            else:
                st.info("Nenhuma despesa registrada para este filtro.")

            # --- MÓDULO DE MANUTENÇÃO DE DADOS ---
            st.divider()
            st.subheader("🛠️ Ferramentas de Manutenção")
            
            # Mapeamento para interface de edição
            dict_manut = {
                f"ID {r['id']} | {r['data']} | {r['Cliente']}": r 
                for _, r in df_final.iterrows()
            }
            
            sel_manut = st.selectbox(
                "Registro para alteração:",
                options=sorted(list(dict_manut.keys()), reverse=True)
            )
            
            if sel_manut:
                reg_origem = dict_manut[sel_manut]
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    v_novo = st.number_input("Valor", value=float(reg_origem['valor']), key="m_val")
                with col_m2:
                    o_nova = st.text_input("Observação", value=reg_origem['observacao'], key="m_obs")
                
                # Ações de atualização e deleção
                btn_s, btn_e = st.columns(2)
                
                if btn_s.button("💾 Aplicar Alterações", width="stretch"):
                    if atualizar_registro(reg_origem['id'], reg_origem['data'], reg_origem['categoria'], v_novo, reg_origem['tipo'], o_nova):
                        st.rerun()
                
                if btn_e.button("🗑️ Remover permanentemente", type="primary", width="stretch"):
                    if deletar_registro(reg_origem['id']):
                        st.rerun()

# ==============================================================================
# --- DOCUMENTAÇÃO TÉCNICA DO PROJETO ADS ---
# PROJETO: Sistema Integrado de Gestão Financeira (SIGF)
# DESENVOLVEDOR: Carlos Magno Moreira Freitas
# INSTITUIÇÃO: Universidade Anhembi Morumbi
# CURSO: Análise e Desenvolvimento de Sistemas (ADS)
# VERSÃO: 3.5 (Março/2026) - Implementação de PDF e Tags Dinâmicas de Clientes.
# NOTA: Este script utiliza SQLAlchemy para persistência e FPDF para relatórios.
# ==============================================================================