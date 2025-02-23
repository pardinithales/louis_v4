import os
from fastapi import FastAPI
from dotenv import load_dotenv
from rag_query import perform_rag_query  # Importa a função de consulta do rag_query.py

# Carregar variáveis de ambiente (local ou do Vercel)
load_dotenv()  # Para desenvolvimento local; no Vercel, variáveis são injetadas diretamente
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "fallback_key_if_not_set")
KDBAI_ENDPOINT = os.getenv("KDBAI_ENDPOINT", "fallback_endpoint_if_not_set")
KDBAI_API_KEY = os.getenv("KDBAI_API_KEY", "fallback_api_key_if_not_set")

# Configurar o diretório de trabalho (ajustado para Vercel)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# Inicializar a aplicação FastAPI
app = FastAPI()

# Endpoint para consulta
@app.get("/query")
async def query(q: str = "What are the molecular mechanisms of DM1 in this paper?"):
    """Endpoint para realizar uma consulta RAG."""
    result = perform_rag_query(user_query=q)
    return {"response": result}

# Para rodar localmente (opcional, ignorado no Vercel)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)