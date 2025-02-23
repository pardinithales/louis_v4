from sentence_transformers import SentenceTransformer
import kdbai_client as kdbai
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
KDBAI_ENDPOINT = os.getenv("KDBAI_ENDPOINT")
KDBAI_API_KEY = os.getenv("KDBAI_API_KEY")

# Configurar KDB.AI
kdbai_session = kdbai.Session(endpoint=KDBAI_ENDPOINT, api_key=KDBAI_API_KEY)
kdbai_db = kdbai_session.database('default')
kdbai_table = kdbai_db.table("pdf_chunks")

# Carregar modelo de embedding (mesmo modelo do processar_pdfs.py)
embed_model = SentenceTransformer("all-mpnet-base-v2")

def perform_rag_query(user_query="What are the molecular mechanisms of DM1 in this paper?"):
    """Realiza uma consulta RAG usando busca vetorial no KDB.AI e geração de resposta com Gemini."""
    # Gerar embedding da consulta
    qvec = embed_model.encode(user_query).astype("float32")

    # Busca vetorial no KDB.AI (top 3 chunks mais relevantes)
    search_results = kdbai_table.search(
        vectors={"vectors": qvec.tolist()},
        n=3
    )

    # Extrair os textos relevantes (ajustado para a coluna 'vectors')
    contexts = [result["text"] for result in search_results[0]]

    # Configurar a API do Gemini
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel(model_name="gemini-2.0-flash")

    # Gerar resposta com o Gemini
    prompt = f"Pergunta: {user_query}\nContexto: {' '.join(contexts)}"
    response = gemini_model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    print(perform_rag_query())