import requests
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_rag_query():
    try:
        url = "http://localhost:8000/query?user_query=What+is+this+text+about%3F"
        response = requests.get(url)
        response.raise_for_status()  # Levanta uma exceção para erros HTTP
        logger.info("Consulta RAG bem-sucedida!")
        logger.info(f"Resposta do servidor: {response.json()}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao realizar consulta RAG: {str(e)}")

if __name__ == "__main__":
    test_rag_query()