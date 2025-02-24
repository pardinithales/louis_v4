from sentence_transformers import SentenceTransformer
import kdbai_client as kdbai
import google.generativeai as genai
from dotenv import load_dotenv
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
KDBAI_ENDPOINT = os.getenv("KDBAI_ENDPOINT")
KDBAI_API_KEY = os.getenv("KDBAI_API_KEY")

# Configurar Gemini
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel(model_name="gemini-2.0-flash")  # Modelo válido

# Configurar KDB.AI
logger.debug("Conectando ao KDB.AI")
kdbai_session = kdbai.Session(endpoint=KDBAI_ENDPOINT, api_key=KDBAI_API_KEY)
kdbai_db = kdbai_session.database('default')
kdbai_table = kdbai_db.table("pdf_chunks")

# Carregar modelo de embedding
logger.debug("Carregando modelo de embedding")
embed_model = SentenceTransformer("all-mpnet-base-v2")

def perform_rag_query(user_query="What are the molecular mechanisms of DM1?"):
    try:
        logger.debug("Verificando índices na tabela pdf_chunks")
        indexes = kdbai_table.indexes  # Atributo, não função
        
        # Log dos índices disponíveis (para depuração)
        logger.debug(f"Índices encontrados: {indexes}")
        
        if not indexes:
            logger.warning("Nenhum índice encontrado. A busca pode falhar.")
        
        # Gerar embedding da consulta do usuário
        query_embedding = embed_model.encode(user_query, show_progress_bar=False)
        
        # Realizar busca nos dados armazenados usando a coluna 'vectors'
        search_result = kdbai_table.search(
            vectors={"vectors": [query_embedding.tolist()]},  # Atualizado para 'vectors'
            n=5  # Número de resultados a retornar
        )
        
        # Extrair os chunks relevantes (assumindo que a coluna de texto é 'text')
        if not search_result or not search_result[0]:
            return "Nenhum resultado encontrado para a consulta."
        
        chunks = search_result[0]["text"]  # Ajuste o nome da coluna se necessário
        
        # Combinar os chunks em um contexto
        context = "\n\n".join(chunks)
        
        # Gerar resposta com Gemini
        prompt = f"Com base no seguinte contexto, responda à pergunta: {user_query}\n\nContexto:\n{context}"
        response = gemini_model.generate_content(prompt)
        
        return response.text
    
    except Exception as e:
        logger.error(f"Erro no perform_rag_query: {str(e)}")
        raise

if __name__ == "__main__":
    # Teste standalone
    result = perform_rag_query("What are the molecular mechanisms of DM1?")
    print(result)