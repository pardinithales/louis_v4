import requests
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_rag_query():
    try:
        url = "http://localhost:8000/query?user_query=What+is+this+text+about%3F"
        headers = {
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Levanta uma exceção para erros HTTP
        
        # Se a resposta for bem-sucedida, loga o resultado
        logger.info("Consulta RAG bem-sucedida!")
        logger.info(f"Resposta do servidor: {response.json()}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erro HTTP ao realizar consulta RAG: {e.response.status_code} - {e.response.text}")
        try:
            error_detail = e.response.json()
            logger.error(f"Detalhes do erro: {error_detail}")
        except json.JSONDecodeError:
            logger.error("Não foi possível decodificar o corpo da resposta como JSON.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao realizar consulta RAG: {str(e)}")

if __name__ == "__main__":
    test_rag_query()