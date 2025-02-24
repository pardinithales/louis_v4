import streamlit as st
import requests
import logging
from pathlib import Path
import time
from datetime import datetime
import json
import os

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configurar chaves de API
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
KDBAI_ENDPOINT = st.secrets["KDBAI_ENDPOINT"]
KDBAI_API_KEY = st.secrets["KDBAI_API_KEY"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# Configurar URL do backend
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

# Configurar a página
st.title("RAG Interface para Processamento de PDFs")
st.write("Carregue PDFs (somente com login) ou faça consultas sobre os PDFs processados.")

# Simulação de controle de acesso para upload de PDFs (nome de usuário e senha simples)
ALLOWED_USERS = {"admin": "password123"}  # Nome de usuário e senha para teste
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# Login para upload de PDFs (opcional para consultas)
if not st.session_state.authenticated:
    st.subheader("Login para Fazer Upload de PDFs (Opcional, Consultas Não Requerem Login)")
    username = st.text_input("Nome de Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if username in ALLOWED_USERS and ALLOWED_USERS[username] == password:
            st.session_state.authenticated = True
            st.session_state.current_user = username
            st.success("Login bem-sucedido! Agora você pode fazer upload de PDFs.")
            st.rerun()  # Força a recarregar a página para aplicar o estado autenticado
        else:
            st.error("Credenciais inválidas. Tente novamente.")
else:
    st.write(f"Logado como: {st.session_state.current_user}")

    # Estado do sessão para armazenar PDFs processados
    if "pdfs_processed" not in st.session_state:
        st.session_state.pdfs_processed = []

    # Função para upload de PDF (somente para usuários autenticados)
    def upload_pdf(pdf_path):
        try:
            with open(pdf_path, "rb") as pdf_file:
                files = {
                    "file": (pdf_path.name, pdf_file, "application/pdf")
                }
                url = f"{BACKEND_URL}/upload_pdf"
                response = requests.post(url, files=files)
                response.raise_for_status()
                pdf_info = {
                    "filename": pdf_path.name,
                    "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": "Resumo não disponível (faça uma consulta para gerar)"  # Placeholder
                }
                st.session_state.pdfs_processed.append(pdf_info)
                return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao fazer upload do PDF: {str(e)}")
            return None

    # Função para consulta RAG com formato padrão (system prompt), disponível para todos
    def query_rag(user_query):
        try:
            # Formato padrão (system prompt) para garantir consistência
            system_prompt = (
                "Você é um assistente especializado em responder perguntas sobre documentos médicos, "
                "especialmente canalopatias musculares. Forneça respostas claras, concisas e baseadas "
                "estritamente no contexto fornecido, sem adicionar informações externas. Se não souber, "
                "diga 'Não tenho informações suficientes para responder.'"
                "se a pergunta for caso clinico, responda as 4 síndromes/localização mais prováveis"
                "em ordem de mais provável para menos provável"
                "justifique as artérias envolvidas ou a artéria culpada"
                "para cada sindrome/local justifique muito brevemente a razão"
                "sempre em portugues-br"
            )
            full_query = f"{system_prompt}\n\nPergunta: {user_query}"
            url = f"{BACKEND_URL}/query?user_query={full_query}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao fazer consulta RAG: {str(e)}")
            return None

    # Interface para upload de PDF (somente se autenticado)
    if st.session_state.authenticated:
        st.subheader("Upload de PDF")
        uploaded_file = st.file_uploader("Carregue um PDF", type="pdf")
        if uploaded_file is not None:
            pdf_path = Path("temp.pdf")
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            if st.button("Processar PDF"):
                result = upload_pdf(pdf_path)
                if result:
                    st.success(result["message"])
                else:
                    st.error("Falha ao processar o PDF.")
            
            # Limpar o arquivo temporário
            if pdf_path.exists():
                pdf_path.unlink()

    # Consulta RAG (disponível para todos, sem login)
    st.subheader("Faça uma Consulta (Sem Login Necessário)")
    query = st.text_area("Digite sua pergunta sobre os PDFs processados (e.g., 'Quais medicamentos tratam canalopatias musculares?')")
    if query and st.button("Consultar"):
        result = query_rag(query)
        if result:
            st.write("Resposta:", result["response"])
        else:
            st.error("Falha ao realizar a consulta.")

    # Resumo dos arquivos processados (disponível para todos)
    st.subheader("Resumo dos PDFs Processados")
    if st.session_state.pdfs_processed:
        for pdf in st.session_state.pdfs_processed:
            st.write(f"**Arquivo:** {pdf['filename']}")
            st.write(f"**Data de Upload:** {pdf['uploaded_at']}")
            st.write(f"**Resumo:** {pdf['summary']}")
            # Opção para gerar um resumo mais detalhado via consulta RAG
            if st.button(f"Gerar Resumo Detalhado para {pdf['filename']}"):
                summary_query = f"Resuma o conteúdo do PDF {pdf['filename']} em 2-3 frases."
                summary_result = query_rag(summary_query)
                if summary_result:
                    pdf['summary'] = summary_result["response"]
                    st.session_state.pdfs_processed = [p for p in st.session_state.pdfs_processed if p['filename'] != pdf['filename']] + [pdf]
                    st.write("Resumo Detalhado:", summary_result["response"])
    else:
        st.write("Nenhum PDF processado ainda.")

    # Instruções
    st.write("---")
    st.write("1. O upload de PDFs requer login (use 'admin' e 'password123' como credenciais de teste).")
    st.write("2. Consultas e resumos podem ser feitos sem login, baseados nos PDFs já processados.")
    st.write("3. Carregue um PDF, processe-o, e faça perguntas ou gere resumos detalhados.")