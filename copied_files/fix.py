import kdbai_client as kdbai
from dotenv import load_dotenv
import os
import pkg_resources
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Verificar versão do kdbai-client
kdbai_version = pkg_resources.get_distribution("kdbai-client").version
logger.info(f"Versão do kdbai-client: {kdbai_version}")

# Carregar variáveis de ambiente
load_dotenv()
KDBAI_ENDPOINT = os.getenv("KDBAI_ENDPOINT")
KDBAI_API_KEY = os.getenv("KDBAI_API_KEY")

# Conectar ao KDB.AI
logger.debug("Conectando ao KDB.AI")
session = kdbai.Session(endpoint=KDBAI_ENDPOINT, api_key=KDBAI_API_KEY)
db = session.database("default")
table = db.table("pdf_chunks")

# Verificar índices atuais
indexes = table.indexes
logger.info(f"Índices antes: {indexes}")

# Função para remover índice com fallback
def remove_index(table, index_name):
    if hasattr(table, "drop_index"):
        logger.info(f"Removendo o índice {index_name} usando drop_index...")
        table.drop_index(index_name)
        logger.info(f"Índice {index_name} removido com sucesso.")
    else:
        logger.warning(f"Método drop_index não disponível na versão {kdbai_version}. Tentativa manual não implementada.")
        raise AttributeError("drop_index não suportado. Atualize kdbai-client ou recrie a tabela manualmente.")

# Remover o índice existente (se presente)
for idx in indexes:
    if idx["name"] == "flat_index":
        remove_index(table, "flat_index")

# Criar um novo índice
logger.info("Criando novo índice flat_index...")
table.create_index(
    name="flat_index",
    type="flat",
    column="vectors",
    params={"metric": "L2", "dims": 768}
)
logger.info("Novo índice flat_index criado.")

# Verificar índices após criação
indexes = table.indexes
logger.info(f"Índices depois: {indexes}")

# Testar busca
try:
    dummy_vector = [0.0] * 768
    result = table.search(
        vectors={"vectors": [dummy_vector]},
        n=1
    )
    logger.info(f"Resultado da busca de teste: {result}")
except Exception as e:
    logger.error(f"Erro na busca de teste: {str(e)}")