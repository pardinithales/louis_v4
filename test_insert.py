import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
import uuid  # Para gerar UUIDs

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://hgpjrzouqfzqgkcxrbhv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhncGpyem91cWZ6cWdrY3hyYmh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDAzMjEzMTIsImV4cCI6MjA1NTg5NzMxMn0.UisPCm9a_ARqG4gZnc0WO7zJ5CaWhPBPYYFqTamJv5c")

# Inicializar Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_insert():
    try:
        # Dados de teste com nomes de colunas corrigidos e UUID para 'id'
        test_data = {
            "id": str(uuid.uuid4()),  # Gera um UUID válido
            "content": "Este é um texto de teste para verificar a tabela.",
            "embedding": [0.1] * 768  # Vetor dummy com 768 dimensões (compatível com all-mpnet-base-v2)
            # 'pdf_name' e 'page_num_int' podem ser omitidos se não forem obrigatórios
        }
        response = supabase.table("pdf_chunks").insert(test_data).execute()
        logger.info("Inserção bem-sucedida!")
        logger.info(f"Dados inseridos: {response.data}")
    except Exception as e:
        logger.error(f"Erro ao inserir dados na tabela 'pdf_chunks': {str(e)}")

if __name__ == "__main__":
    test_insert()