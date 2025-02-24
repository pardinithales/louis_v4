import requests
import logging
from pathlib import Path
import json 

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_upload_pdf():      
    try:    
        # Caminho para um arquivo PDF de teste (ajuste o caminho conforme necessário)
        pdf_path = Path("C:/Users/Usuario/Downloads/muscle_channelopathies.14.pdf")
        if not pdf_path.exists():
            logger.error(f"Arquivo PDF '{pdf_path}' não encontrado. Crie um PDF de teste ou ajuste o caminho.")
            return

        # Abrir o arquivo PDF
        with open(pdf_path, "rb") as pdf_file:
            files = {
                "file": (pdf_path.name, pdf_file, "application/pdf")
            }
            url = "http://localhost:8000/upload_pdf"
            response = requests.post(url, files=files)
            response.raise_for_status()

        logger.info("Upload de PDF bem-sucedido!")
        logger.info(f"Resposta do servidor: {response.json()}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erro HTTP ao realizar upload de PDF: {e.response.status_code} - {e.response.text}")
        try:
            error_detail = e.response.json()
            logger.error(f"Detalhes do erro: {error_detail}")
        except json.JSONDecodeError:
            logger.error("Não foi possível decodificar o corpo da resposta como JSON.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao realizar upload de PDF: {str(e)}")

if __name__ == "__main__":
    test_upload_pdf()