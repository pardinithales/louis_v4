import os
import gradio as gr
from pdf2image import convert_from_bytes
import re
from sentence_transformers import SentenceTransformer
import pandas as pd
from dotenv import load_dotenv  # Mantido para desenvolvimento local, mas opcional no Vercel
import google.generativeai as genai
import kdbai_client as kdbai
import concurrent.futures
from tqdm import tqdm

# Carregar variáveis de ambiente (local ou do Vercel)
load_dotenv()  # Para desenvolvimento local; no Vercel, variáveis são injetadas diretamente
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "fallback_key_if_not_set")  # Fallback para testes locais
KDBAI_ENDPOINT = os.getenv("KDBAI_ENDPOINT", "fallback_endpoint_if_not_set")
KDBAI_API_KEY = os.getenv("KDBAI_API_KEY", "fallback_api_key_if_not_set")

# Configurar o diretório de trabalho (ajustado para Vercel, que pode não ter filesystem persistente)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(BASE_DIR):  # Caso o Vercel não tenha o diretório persistente
    os.makedirs(BASE_DIR, exist_ok=True)

# Configurar a API do Gemini
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Configurar KDB.AI
kdbai_session = kdbai.Session(endpoint=KDBAI_ENDPOINT, api_key=KDBAI_API_KEY)
kdbai_db = kdbai_session.database('default')

# Criar tabela vetorial no KDB.AI (768 dimensões para all-mpnet-base-v2)
VECTOR_DIM = 768
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
embed_model = SentenceTransformer("all-mpnet-base-v2")

def process_pdf_page(pdf_path, page_num, image):
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

def process_pdf(pdf_data, filename="uploaded_pdf.pdf"):
    """Processa um PDF completo a partir de bytes, retornando todos os chunks."""
    try:
        pages = convert_from_bytes(pdf_data)
        all_chunks = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_page = {executor.submit(process_pdf_page, filename, i + 1, page): i for i, page in enumerate(pages)}
            for future in tqdm(concurrent.futures.as_completed(future_to_page), total=len(pages), desc="Processando PDF"):
                page_chunks = future.result()
                all_chunks.extend(page_chunks)
        return all_chunks
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return []

def batch_process_pdfs(pdf_files):
    """Processa PDFs em lote, armazena chunks no KDB.AI e salva em arquivos de texto."""
    all_chunks = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(BASE_DIR, pdf_file)
        print(f"Processando {pdf_file}...")
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        chunks = process_pdf(pdf_data, pdf_file)
        all_chunks.extend(chunks)

        # Gerar embeddings e preparar dados para KDB.AI
        chunk_texts = [ch["text"] for ch in chunks]
        embeddings = embed_model.encode(chunk_texts, batch_size=32, show_progress_bar=True).astype("float32")
        row_list = []
        for idx, ch_data in enumerate(chunks):
            row_list.append({
                "id": ch_data["id"],
                "text": ch_data["text"],
                "vectors": embeddings[idx].tolist()
            })

        # Inserir no KDB.AI
        df = pd.DataFrame(row_list)
        kdbai_table.insert(df)
        print(f"Chunks inseridos no KDB.AI para '{pdf_file}': {len(df)} chunks.")

        # Salvar chunks em arquivo de texto (opcional, para debug local)
        output_filename = f"{os.path.splitext(pdf_file)[0]}_chunks.txt"
        output_path = os.path.join(BASE_DIR, output_filename)
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(f"ID: {chunk['id']}\n")
                f.write(f"{chunk['text']}\n\n")
        print(f"Chunks salvos em {output_filename}")

    return "PDFs processados com sucesso!"

def query_rag(query):
    """Realiza uma consulta RAG no KDB.AI e gera resposta com Gemini."""
    qvec = embed_model.encode(query).astype("float32")
    num_chunks = 5  # Recuperar até 5 chunks para contexto rico

    try:
        search_results = kdbai_table.search(vectors={"flat_index": [qvec]}, n=num_chunks)
        retrieved_chunks = search_results[0]["text"].tolist()
        chunk_ids = search_results[0]["id"].tolist()
    except Exception as e:
        return f"Erro na busca vetorial: {e}"

    if not retrieved_chunks:
        return "Nenhum chunk relevante encontrado."

    # Construir contexto com chunks
    chunks_context = "\n".join([f"Chunk {i+1} (ID: {chunk_ids[i]}):\n{chunk_text}" for i, chunk_text in enumerate(retrieved_chunks)])

    # Configurar Gemini para gerar a resposta
    final_prompt = f"""Use o seguinte contexto para responder à pergunta em português do Brasil (pt-BR), de forma contínua, com aproximadamente 10 linhas de texto (sem quebras de linha desnecessárias). Seja breve, preciso, e referencie os IDs dos chunks (ex.: 'Based on chunks page_X_chunk_Y, page_Z_chunk_W, etc.'):
    Contexto:
    {chunks_context}
    Pergunta: {query}
    Resposta (em português do Brasil, contínua, cerca de 10 linhas, referenciando os IDs dos chunks):"""

    try:
        response = gemini_model.generate_content(final_prompt)
        response_text = response.text.strip()
        chunk_refs = ", ".join([f"chunk {chunk_ids[i]}" for i in range(len(chunk_ids))])
        return f"Resposta: {response_text}\nFonte: Based on {chunk_refs}"
    except Exception as e:
        return f"Erro na geração da resposta: {e}"

# Interface Gradio
with gr.Blocks(title="RAG PDF Query Interface") as demo:
    gr.Markdown("# Interface Intuitiva para Upload de PDFs e Consultas RAG")
    
    with gr.Tab("Upload de PDFs"):
        pdf_input = gr.File(file_types=[".pdf"], label="Faça o Upload de um ou Mais PDFs", multiple=True)
        process_button = gr.Button("Processar PDFs")
        process_output = gr.Textbox(label="Resultado do Processamento", lines=5)

        process_button.click(
            fn=batch_process_pdfs,
            inputs=pdf_input,
            outputs=process_output
        )

    with gr.Tab("Consulta RAG"):
        query_input = gr.Textbox(label="Digite sua Pergunta", placeholder="Ex.: Quais são os sintomas do DM1?")
        query_button = gr.Button("Consultar")
        query_output = gr.Textbox(label="Resposta RAG", lines=12)

        query_button.click(
            fn=query_rag,
            inputs=query_input,
            outputs=query_output
        )

# Lançar a interface (localmente ou no Vercel)
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8080)  # Configurar para Vercel (usará porta padrão do Vercel)