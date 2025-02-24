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

def test_function():
    try:
        # Vetor dummy com 768 dimensões (compatível com all-mpnet-base-v2)
        # Usamos o mesmo vetor que foi inserido para garantir um match
        dummy_vector = [0.1] * 768
        # Testa com os parâmetros sugeridos (limit_val, query_vector)
        response = supabase.rpc("search_pdf_chunks", {
            "query_vector": dummy_vector,
            "limit_val": 5
        }).execute()
        
        logger.info("Função 'search_pdf_chunks' funciona!")
        if response.data:
            logger.info(f"Resultados retornados: {response.data}")
        else:
            logger.info("Nenhum resultado retornado (tabela pode estar vazia ou função mal configurada).")
    except Exception as e:
        logger.error(f"Erro ao testar função 'search_pdf_chunks': {str(e)}")

if __name__ == "__main__":
    test_function()