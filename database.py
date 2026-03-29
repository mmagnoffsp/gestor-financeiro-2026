import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1. Comando que lê o arquivo .env
load_dotenv()

# 2. Pega o link de forma segura (sem mostrar a senha aqui)
DB_URL = os.getenv("DATABASE_URL")

# Verificação de segurança para você saber se o .env funcionou
if not DB_URL:
    print("❌ ERRO: O arquivo .env não foi lido ou a variável DATABASE_URL está vazia!")
else:
    # 3. Criação do motor de conexão usando a variável segura
    engine = create_engine(DB_URL)

def inicializar_banco():
    """Cria a tabela no banco de dados se não existir"""
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