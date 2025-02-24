import streamlit as st
import requests
import logging
from pathlib import Path
import time
from datetime import datetime
import json
import os
import socket

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Função para verificar se estamos em ambiente de desenvolvimento
def is_development():
    # Usa variável de ambiente para forçar o modo (opcional no deploy)
    env_mode = os.getenv("STREAMLIT_ENV", "development")
    logger.info(f"STREAMLIT_ENV: {env_mode}")
    # Se rodando localmente via 'streamlit run', considera desenvolvimento
    if "streamlit" in os.sys.argv[0] or env_mode == "development":
        logger.info("Detectado como ambiente de desenvolvimento")
        return True
    logger.info("Detectado como ambiente de produção")
    return False

# Configurar URL do backend baseado no ambiente
if is_development():
    BACKEND_URL = "http://localhost:8001"  # Forçado para testes locais
    logger.info("Ambiente de desenvolvimento detectado, usando backend local em porta 8001")
else:
    BACKEND_URL = st.secrets["general"]["BACKEND_URL_PROD"]
    logger.info("Ambiente de produção detectado, usando backend remoto")

logger.info(f"Usando backend em: {BACKEND_URL}")

# Carregar chaves de API e credenciais do secrets.toml
try:
    GOOGLE_API_KEY = st.secrets["api_keys"]["GOOGLE_API_KEY"]
    KDBAI_ENDPOINT = st.secrets["api_keys"]["KDBAI_ENDPOINT"]
    KDBAI_API_KEY = st.secrets["api_keys"]["KDBAI_API_KEY"]
    SUPABASE_KEY = st.secrets["api_keys"]["SUPABASE_KEY"]
    ALLOWED_USERS = {
        st.secrets["credentials"]["username"]: st.secrets["credentials"]["password"]
    }
except Exception as e:
    logger.warning(f"Erro ao carregar secrets: {str(e)}")
    st.error("⚠️ Erro ao carregar configurações. Usando configurações padrão para desenvolvimento.")
    BACKEND_URL = "http://localhost:8001"
    ALLOWED_USERS = {"admin": "password123"}

# Função para verificar conexão com backend
def check_backend_connection():
    try:
        logger.debug(f"Tentando conectar ao backend em: {BACKEND_URL}")
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        logger.debug(f"Resposta do backend: {response.status_code} - {response.text}")
        if response.status_code == 200:
            st.success("✅ Backend conectado com sucesso!")
            return True
        logger.error(f"Backend retornou status code: {response.status_code}")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de conexão com o backend: {str(e)}")
        st.error(f"⚠️ Erro de conexão: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar conexão com backend: {str(e)}")
        return False

# Verificar conexão com backend no início
if not check_backend_connection():
    st.error("⚠️ Backend não está acessível. Por favor, verifique se o servidor está rodando.")
    st.info(f"Tentando conectar em: {BACKEND_URL}")
    if is_development():
        st.info("💡 Execute em um terminal separado:")
        st.code("cd C:\\Users\\Usuario\\Desktop\\teste")
        st.code(".\\pykx-env\\Scripts\\Activate.ps1")
        st.code("python rag_interface.py 8001")
    st.stop()

# Configurar a página
st.title("RAG Interface para Processamento de PDFs")
st.write("Carregue PDFs (somente com login) ou faça consultas sobre os PDFs processados.")

# Controle de acesso via sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# Login para upload de PDFs
if not st.session_state.authenticated:
    st.subheader("Login para Fazer Upload de PDFs (Opcional, Consultas Não Requerem Login)")
    username = st.text_input("Nome de Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if username in ALLOWED_USERS and ALLOWED_USERS[username] == password:
            st.session_state.authenticated = True
            st.session_state.current_user = username
            st.success("Login bem-sucedido! Agora você pode fazer upload de PDFs.")
            st.rerun()
        else:
            st.error("Credenciais inválidas. Tente novamente.")
else:
    st.write(f"Logado como: {st.session_state.current_user}")

    # Estado da sessão para PDFs processados
    if "pdfs_processed" not in st.session_state:
        st.session_state.pdfs_processed = []

    # Função para upload de PDF
    def upload_pdf(pdf_path):
        if not check_backend_connection():
            st.error("⚠️ Backend não está acessível. Não é possível fazer upload no momento.")
            return None
        try:
            with open(pdf_path, "rb") as pdf_file:
                files = {"file": (pdf_path.name, pdf_file, "application/pdf")}
                url = f"{BACKEND_URL}/upload_pdf"
                response = requests.post(url, files=files)
                response.raise_for_status()
                pdf_info = {
                    "filename": pdf_path.name,
                    "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": "Resumo não disponível (faça uma consulta para gerar)"
                }
                st.session_state.pdfs_processed.append(pdf_info)
                return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao fazer upload do PDF: {str(e)}")
            st.error("⚠️ Erro ao fazer upload do PDF. Verifique a conexão com o backend.")
            return None

    # Função para consulta RAG
    def query_rag(user_query):
        if not check_backend_connection():
            st.error("⚠️ Backend não está acessível. Não é possível fazer consultas no momento.")
            return None
        try:
            system_prompt = (
                "Você é um assistente especializado em responder perguntas sobre documentos médicos, "
                "especialmente canalopatias musculares. Forneça respostas claras, concisas e baseadas "
                "estritamente no contexto fornecido, sem adicionar informações externas. Se não souber, "
                "diga 'Não tenho informações suficientes para responder.' "
                "Se a pergunta for caso clínico, responda as 4 síndromes/localização mais prováveis "
                "em ordem de mais provável para menos provável, justificando as artérias envolvidas "
                "ou a artéria culpada e dando uma breve razão para cada síndrome/local."
                "Sempre responda em português brasileiro."
            )
            full_query = f"{system_prompt}\n\nPergunta: {user_query}"
            url = f"{BACKEND_URL}/query?user_query={full_query}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao fazer consulta RAG: {str(e)}")
            st.error("⚠️ Erro ao fazer consulta. Verifique a conexão com o backend.")
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
            if pdf_path.exists():
                pdf_path.unlink()

    # Consulta RAG (disponível para todos)
    st.subheader("Faça uma Consulta (Sem Login Necessário)")
    query = st.text_area("Digite sua pergunta sobre os PDFs processados (e.g., 'Quais medicamentos tratam canalopatias musculares?')")
    if query and st.button("Consultar"):
        result = query_rag(query)
        if result:
            st.write("Resposta:", result["response"])
        else:
            st.error("Falha ao realizar a consulta.")

    # Resumo dos arquivos processados
    st.subheader("Resumo dos PDFs Processados")
    if st.session_state.pdfs_processed:
        for pdf in st.session_state.pdfs_processed:
            st.write(f"**Arquivo:** {pdf['filename']}")
            st.write(f"**Data de Upload:** {pdf['uploaded_at']}")
            st.write(f"**Resumo:** {pdf['summary']}")
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
    st.write("1. Use 'admin' e 'password123' para login e fazer upload de PDFs.")
    st.write("2. Consultas e resumos podem ser feitos sem login.")
    st.write(f"3. Backend atual: {BACKEND_URL}")