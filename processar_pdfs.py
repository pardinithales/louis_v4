import os
from pdf2image import convert_from_bytes
import re
from sentence_transformers import SentenceTransformer
import concurrent.futures
from tqdm import tqdm
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configurar o diretório de trabalho
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# Prompt para chunking
CHUNKING_PROMPT = """\
OCR the following page into Markdown. Tables should be formatted as HTML.
Chunk the document into sections of roughly 250 - 1000 words.
Surround each chunk with <chunk> and </chunk> tags.
Preserve as much content as possible, including headings, tables, etc.
"""

def process_pdf_page(pdf_path, page_num, image, gemini_model):
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
    return [{"id": f"{os.path.basename(pdf_path)}_{page_num}_chunk_{i}", "text": chunk.strip()} for i, chunk in enumerate(chunks)]

def process_pdf(pdf_path, gemini_model):
    """Processa um PDF completo, retornando todos os chunks."""
    try:
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        pages = convert_from_bytes(pdf_data)
        all_chunks = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_page = {executor.submit(process_pdf_page, pdf_path, i + 1, page, gemini_model): i for i, page in enumerate(pages)}
            for future in tqdm(concurrent.futures.as_completed(future_to_page), total=len(pages), desc=f"Processando {os.path.basename(pdf_path)}"):
                page_chunks = future.result()
                all_chunks.extend(page_chunks)
        return all_chunks
    except Exception as e:
        print(f"Erro ao processar {pdf_path}: {e}")
        return []

if __name__ == "__main__":
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv()
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    pdf_files = [f for f in os.listdir(BASE_DIR) if f.endswith(".pdf")]
    for pdf_file in pdf_files:
        chunks = process_pdf(pdf_file, gemini_model)
        print(f"Processed {pdf_file}: {len(chunks)} chunks")