import requests
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_rag_specific_query():
    try:
        url = "http://localhost:8000/query?user_query=explain+very+basic+for+anyone+what+are+channelopathies+in+ptbr%3F"
        response = requests.get(url)
        response.raise_for_status()

        logger.info("Consulta RAG com pergunta específica bem-sucedida!")
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
    test_rag_specific_query()