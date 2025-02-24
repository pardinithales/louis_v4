import kdbai_client as kdbai
from dotenv import load_dotenv
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()
KDBAI_ENDPOINT = os.getenv("KDBAI_ENDPOINT")
KDBAI_API_KEY = os.getenv("KDBAI_API_KEY")

# Conectar ao KDB.AI
logger.debug("Conectando ao KDB.AI")
session = kdbai.Session(endpoint=KDBAI_ENDPOINT, api_key=KDBAI_API_KEY)
db = session.database("default")
table = db.table("pdf_chunks")

# Verificar índices
indexes = table.indexes
logger.info(f"Índices disponíveis: {indexes}")

# Verificar esquema da tabela
schema = table.schema
logger.info(f"Esquema da tabela: {schema}")

# Testar uma busca simples
try:
    dummy_vector = [0.0] * 768  # Vetor de teste com 768 dimensões
    result = table.search(
        vectors={"vectors": [dummy_vector]},
        n=1
    )
    logger.info(f"Resultado da busca de teste: {result}")
except Exception as e:
    logger.error(f"Erro na busca de teste: {str(e)}")