import os
from pdf2image import convert_from_bytes
import re
from sentence_transformers import SentenceTransformer
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
import kdbai_client as kdbai

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
KDBAI_ENDPOINT = os.getenv("KDBAI_ENDPOINT")
KDBAI_API_KEY = os.getenv("KDBAI_API_KEY")

# Configurar o diretório de trabalho
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# Configurar a API do Gemini
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Configurar KDB.AI
kdbai_session = kdbai.Session(endpoint=KDBAI_ENDPOINT, api_key=KDBAI_API_KEY)
kdbai_db = kdbai_session.database('default')

# Criar tabela vetorial no KDB.AI
VECTOR_DIM = 384  # Dimensão do modelo all-MiniLM-L6-v2
TABLE_NAME = "pdf_chunks"

try:
    kdbai_db.table(TABLE_NAME).drop()
except kdbai.KDBAIException:
    pass

schema = [
    {"name": "id", "type": "str"},
    {"name": "text", "type": "str"},
    {"name": "vectors", "type": "float32s"}
]
index = [
    {
        "name": "flat_index",
        "type": "flat",
        "column": "vectors",
        "params": {"dims": VECTOR_DIM, "metric": "L2"}
    }
]
kdbai_table = kdbai_db.create_table(TABLE_NAME, schema=schema, indexes=index)

# Prompt para chunking
CHUNKING_PROMPT = """\
OCR the following page into Markdown. Tables should be formatted as HTML.
Chunk the document into sections of roughly 250 - 1000 words.
Surround each chunk with <chunk> and </chunk> tags.
Preserve as much content as possible, including headings, tables, etc.
"""

# Carregar modelo de embedding
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def process_page(pdf_path, page_num, image):
    """Processa uma página de PDF com OCR e chunking usando Gemini."""
    from io import BytesIO
    import base64
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    payload = [
        {"inline_data": {"data": image_b64, "mime_type": "image/png"}},
        {"text": CHUNKING_PROMPT}
    ]
    try:
        response = gemini_model.generate_content(payload)
        text = response.text
    except Exception as e:
        print(f"Erro na página {page_num} do arquivo {pdf_path}: {e}")
        return []

    chunks = re.findall(r"<chunk>(.*?)</chunk>", text, re.DOTALL)
    if not chunks:
        chunks = text.split("\n\n")  # Fallback se não houver tags
    return [{"id": f"page_{page_num}_chunk_{i}", "text": chunk.strip()} for i, chunk in enumerate(chunks)]

def process_pdfs():
    """Processa todos os PDFs no diretório, armazena chunks no KDB.AI e salva em arquivos de texto."""
    for filename in os.listdir(BASE_DIR):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(BASE_DIR, filename)
            print(f"Processando {filename}...")

            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            pages = convert_from_bytes(pdf_data)

            all_chunks = []
            for i, page in enumerate(pages, start=1):
                page_chunks = process_page(filename, i, page)
                all_chunks.extend(page_chunks)

            # Gerar embeddings e preparar dados para KDB.AI
            chunk_texts = [ch["text"] for ch in all_chunks]
            embeddings = embed_model.encode(chunk_texts).astype("float32")
            row_list = []
            for idx, ch_data in enumerate(all_chunks):
                row_list.append({
                    "id": ch_data["id"],
                    "text": ch_data["text"],
                    "vectors": embeddings[idx].tolist()
                })

            # Inserir no KDB.AI
            df = pd.DataFrame(row_list)
            kdbai_table.insert(df)
            print(f"Chunks inseridos no KDB.AI para '{filename}': {len(df)} chunks.")

            # Salvar chunks em arquivo de texto
            output_filename = f"{os.path.splitext(filename)[0]}_chunks.txt"
            output_path = os.path.join(BASE_DIR, output_filename)
            with open(output_path, "w", encoding="utf-8") as f:
                for chunk in all_chunks:
                    f.write(f"ID: {chunk['id']}\n")
                    f.write(f"{chunk['text']}\n\n")
            print(f"Chunks salvos em {output_filename}")

if __name__ == "__main__":
    process_pdfs()
    print("Processamento concluído!")