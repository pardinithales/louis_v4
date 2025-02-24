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
logger.info(f"Tipo de indexes: {type(indexes)}")
logger.info(f"Número de índices: {len(indexes)}")

if indexes:
    for idx in indexes:
        logger.info(f"Detalhes do índice: {idx}")
else:
    logger.warning("Nenhum índice encontrado na tabela pdf_chunks")