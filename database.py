import os
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1. Só carrega o .env se o arquivo existir (Garante que funcione no VS Code)
if os.path.exists(".env"):
    load_dotenv()

# 2. Pega o link de forma inteligente:
# Tenta primeiro o st.secrets (Streamlit Cloud), depois o ambiente (VS Code)
DB_URL = st.secrets.get("DATABASE_URL") or os.getenv("DATABASE_URL")

# AJUSTE: Compatibilidade para bancos Postgres antigos (opcional, mas seguro)
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

# 3. Criação da Engine
engine = None
if not DB_URL:
    st.error("❌ Erro: DATABASE_URL não encontrada! Configure os Secrets no Streamlit ou o .env local.")
else:
    # pool_pre_ping=True é vital para o Neon não derrubar sua conexão
    engine = create_engine(DB_URL, pool_pre_ping=True)

def inicializar_banco():
    """Cria a tabela no banco de dados se não existir"""
    if not engine: return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS lancamentos (
                    id SERIAL PRIMARY KEY,
                    data DATE,
                    categoria VARCHAR(100),
                    valor NUMERIC(15, 2),
                    tipo VARCHAR(20),
                    observacao TEXT
                )
            """))
            conn.commit()
    except Exception as e:
        print(f"Erro ao conectar ou criar tabela: {e}")

def salvar_dados(data, categoria, valor, tipo, obs):
    """Envia os dados para a nuvem no Neon.tech"""
    if not engine: return False
    query = text("""
        INSERT INTO lancamentos (data, categoria, valor, tipo, observacao) 
        VALUES (:d, :c, :v, :t, :o)
    """)
    try:
        with engine.connect() as conn:
            conn.execute(query, {"d": data, "c": categoria, "v": valor, "t": tipo, "o": obs})
            conn.commit()
            return True
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        return False

def deletar_registro(id_registro):
    """Remove um lançamento específico do Neon pelo ID"""
    if not engine: return False
    query = text("DELETE FROM lancamentos WHERE id = :id")
    try:
        with engine.connect() as conn:
            conn.execute(query, {"id": id_registro})
            conn.commit()
            return True
    except Exception as e:
        print(f"Erro ao deletar: {e}")
        return False

def atualizar_registro(id_reg, data, categoria, valor, tipo, obs):
    """Atualiza um lançamento existente no banco de dados Neon"""
    if not engine: return False
    query = text("""
        UPDATE lancamentos 
        SET data = :d, categoria = :c, valor = :v, tipo = :t, observacao = :o 
        WHERE id = :id
    """)
    try:
        with engine.connect() as conn:
            conn.execute(query, {
                "d": data, 
                "c": categoria, 
                "v": valor, 
                "t": tipo, 
                "o": obs, 
                "id": id_reg
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Erro ao atualizar no banco: {e}")
        return False