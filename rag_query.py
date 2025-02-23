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

# Carregar modelo de embedding
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def perform_rag_query(user_query="What are the molecular mechanisms of DM1 in this paper?"):
    """Realiza uma consulta RAG usando busca vetorial no KDB.AI e geração de resposta com Gemini."""
    # Gerar embedding da consulta
    qvec = embed_model.encode(user_query).astype("float32")

    # Busca vetorial no KDB.AI (top 3 chunks mais relevantes)
    search_results = kdbai_table.search(vectors={"flat_index": [qvec]}, n=3)
    retrieved_chunks = search_results[0]["text"].tolist()
    context_for_llm = "\n\n".join(retrieved_chunks)
    print("Chunks recuperados:\n", context_for_llm)

    # Configurar Gemini para gerar a resposta
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel(model_name="gemini-2.0-flash")

    # Prompt para RAG
    final_prompt = f"""Use the following context to answer the question:
    Context:
    {context_for_llm}
    Question: {user_query}
    Answer:
    """
    response = gemini_model.generate_content(final_prompt)
    print("\n=== Resposta final do Gemini ===")
    print(response.text)

if __name__ == "__main__":
    perform_rag_query()