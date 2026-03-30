import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1. Comando que lê o arquivo .env
load_dotenv()

# 2. Pega o link de forma segura
DB_URL = os.getenv("DATABASE_URL")

# AJUSTE: Garantir que a engine seja criada apenas se a URL existir
engine = None
if not DB_URL:
    print("❌ ERRO: O arquivo .env não foi lido ou a variável DATABASE_URL está vazia!")
else:
    # pool_pre_ping=True evita o erro de 'Connection Closed' do Neon
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

# --- NOVA FUNÇÃO DE EDIÇÃO ---
def atualizar_registro(id_reg, data, categoria, valor, tipo, obs):
    """Atualiza um lançamento existente no banco de dados Neon"""
    if not engine:
        return False
    
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