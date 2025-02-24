import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from PyPDF2 import PdfReader
import uuid     

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()
SUPABASE_URL = "https://hgpjrzouqfzqgkcxrbhv.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Inicializar Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurar Gemini
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Carregar modelo de embedding
logger.debug("Carregando modelo de embedding")
embed_model = SentenceTransformer("all-mpnet-base-v2")

# Configurar o diretório de trabalho
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# Inicializar a aplicação FastAPI
app = FastAPI(title="RAG Interface API", description="API para processamento de PDFs e consultas RAG")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Ler o conteúdo do PDF usando PyPDF2
        pdf_reader = PdfReader(file.file)
        content = ""
        for page in pdf_reader.pages:
            content += page.extract_text() or ""
        chunks = [content[i:i+500] for i in range(0, len(content), 500)]  # Chunking básico
        
        # Gerar embeddings para cada chunk
        embeddings = embed_model.encode(chunks, show_progress_bar=False).tolist()
        
        # Inserir no Supabase com o nome correto da coluna 'content', 'embedding', e UUID para 'id'
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            data = {
                "id": str(uuid.uuid4()),  # Gerar um UUID válido (e.g., "550e8400-e29b-41d4-a716-446655440000")
                "content": chunk,  # Corrigido de "text" para "content"
                "embedding": embedding  # Corrigido de "vectors" para "embedding"
            }
            supabase.table("pdf_chunks").insert(data).execute()
        
        return {"message": f"PDF {file.filename} processado com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao processar PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {str(e)}")
    


@app.get("/query")
async def query_rag(user_query: str):
    try:
        logger.debug(f"Realizando consulta RAG: {user_query}")
        query_embedding = embed_model.encode(user_query, show_progress_bar=False).tolist()
        response = supabase.rpc("search_pdf_chunks", {
            "query_vector": query_embedding,
            "limit_val": 5  # Corrigido de "limit" para "limit_val"
        }).execute()
        
        if not response.data:
            return {"response": "Nenhum resultado encontrado para a consulta."}
        
        # Ajuste para usar 'content' em vez de 'text', pois é o nome da coluna na tabela
        chunks = [row["content"] for row in response.data]  # Corrigido de "text" para "content"
        context = "\n\n".join(chunks)
        prompt = f"Com base no seguinte contexto, responda à pergunta: {user_query}\n\nContexto:\n{context}"
        response = gemini_model.generate_content(prompt)
        return {"response": response.text}
    except Exception as e:
        logger.error(f"Erro na consulta RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na consulta: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)