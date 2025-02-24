import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://hgpjrzouqfzqgkcxrbhv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhncGpyem91cWZ6cWdrY3hyYmh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDAzMjEzMTIsImV4cCI6MjA1NTg5NzMxMn0.UisPCm9a_ARqG4gZnc0WO7zJ5CaWhPBPYYFqTamJv5c")

# Inicializar Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_table():
    try:
        # Tenta selecionar até 5 linhas da tabela
        response = supabase.table("pdf_chunks").select("*").limit(5).execute()
        logger.info("Tabela 'pdf_chunks' encontrada!")
        
        # Verifica colunas
        if response.data:
            columns = list(response.data[0].keys())
            logger.info(f"Colunas da tabela: {columns}")
            logger.info(f"Dados de exemplo (primeira linha): {response.data[0]}")
        else:
            logger.info("Tabela existe, mas está vazia.")
            # Usa uma consulta vazia para pegar metadados
            schema_response = supabase.table("pdf_chunks").select("*").limit(0).execute()
            columns = schema_response.model_fields
            logger.info(f"Colunas esperadas: {columns}")
    except Exception as e:
        logger.error(f"Erro ao verificar tabela 'pdf_chunks': {str(e)}")

if __name__ == "__main__":
    test_table()