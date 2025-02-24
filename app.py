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

# Função para verificar se uma porta está disponível
def is_port_available(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except:
        return False

# Função para encontrar uma porta disponível
def find_available_port(start_port=8000, max_port=8010):
    for port in range(start_port, max_port):
        if is_port_available(port):
            return port
    return None

# Função para verificar se estamos em ambiente de desenvolvimento
def is_development():
    try:
        return not st.runtime.exists()
    except:
        return True

# Encontrar porta disponível para o backend
BACKEND_PORT = find_available_port()
if not BACKEND_PORT:
    st.error("⚠️ Não foi possível encontrar uma porta disponível (8000-8010)")
    st.info("Por favor, verifique se há processos usando essas portas")
    st.stop()

# Configurar URL do backend
BACKEND_URL = st.secrets["general"]["BACKEND_URL"]
logger.info(f"Usando backend em: {BACKEND_URL}")

# Configurar chaves de API
try:
    # Carregar todas as secrets necessárias
    GOOGLE_API_KEY = st.secrets["api_keys"]["GOOGLE_API_KEY"]
    KDBAI_ENDPOINT = st.secrets["api_keys"]["KDBAI_ENDPOINT"]
    KDBAI_API_KEY = st.secrets["api_keys"]["KDBAI_API_KEY"]
    SUPABASE_KEY = st.secrets["api_keys"]["SUPABASE_KEY"]
    
    # Carregar credenciais
    ALLOWED_USERS = {
        st.secrets["credentials"]["username"]: st.secrets["credentials"]["password"]
    }
except Exception as e:
    logger.warning(f"Erro ao carregar secrets: {str(e)}")
    st.error("⚠️ Erro ao carregar configurações. Usando configurações padrão para desenvolvimento.")
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

# Verificar conexão com backend
if not check_backend_connection():
    st.error("⚠️ Backend não está acessível. Por favor, verifique se o servidor está rodando.")
    st.info(f"Tentando conectar em: {BACKEND_URL}")
    st.info("💡 Execute em um terminal separado:")
    st.code("cd C:\\Users\\Usuario\\Desktop\\teste")
    st.code(".\\venv\\Scripts\\Activate")
    st.code(f"uvicorn rag_interface:app --host 0.0.0.0 --port {BACKEND_PORT}")
    st.stop()

# Configurar a página
st.title("RAG Interface para Processamento de PDFs")
st.write("Carregue PDFs (somente com login) ou faça consultas sobre os PDFs processados.")

# Simulação de controle de acesso para upload de PDFs (nome de usuário e senha simples)
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
        if not check_backend_connection():
            st.error("⚠️ Backend não está acessível. Não é possível fazer upload no momento.")
            return None
            
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