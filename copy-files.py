import os
import pyperclip
from typing import Optional

def read_file_content(file_path: str) -> Optional[str]:
    """
    Lê o conteúdo de um arquivo, retornando None se não for legível (ex.: binários como PDFs).
    """
    try:
        # Verificar se é um arquivo binário (como PDF) ou texto
        with open(file_path, 'rb') as f:
            first_bytes = f.read(1024)  # Ler os primeiros 1KB para verificar
            if b'\x00' in first_bytes or file_path.lower().endswith(('.pdf', '.exe', '.dll')):
                return None  # Arquivo binário, ignorar conteúdo

        # Ler como texto, assumindo UTF-8 (com fallback para Latin-1 se necessário)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Limitar o conteúdo a 1.000 caracteres para evitar sobrecarga (exibir "..." se maior)
        if len(content) > 1000:
            content = content[:1000] + "... (conteúdo truncado)"
        return content.strip()
    except Exception as e:
        print(f"Erro ao ler {file_path}: {e}")
        return None

def list_files_to_clipboard(directory: str):
    """
    Lista todos os arquivos no diretório especificado, incluindo nome, localização e conteúdo (se aplicável),
    e copia para o clipboard.
    """
    try:
        # Obter o caminho absoluto do diretório
        absolute_dir = os.path.abspath(directory)
        
        # Lista para armazenar as informações dos arquivos
        file_list = []
        
        # Iterar sobre todos os arquivos e diretórios no diretório
        for item in os.listdir(absolute_dir):
            item_path = os.path.join(absolute_dir, item)
            # Verificar se é um arquivo (não um diretório)
            if os.path.isfile(item_path):
                # Formatar o nome e localização
                file_info = f"Nome: {item}\nLocalização: {item_path}\n"
                
                # Tentar ler o conteúdo (se for texto)
                content = read_file_content(item_path)
                if content is not None:
                    file_info += f"Conteúdo: {content}\n{'-'*50}\n"
                else:
                    file_info += "Conteúdo: (Arquivo binário, conteúdo não disponível)\n{'-'*50}\n"
                
                file_list.append(file_info)
        
        # Juntar todos os itens em uma única string com quebras de linha
        clipboard_content = "\n".join(file_list)
        
        # Copiar para o clipboard
        pyperclip.copy(clipboard_content)
        
        print("Lista de arquivos com localizações e conteúdos copiada para o clipboard com sucesso!")
        print("\nPré-visualização no terminal (corte se for muito longo):\n")
        print(clipboard_content[:2000] + "..." if len(clipboard_content) > 2000 else clipboard_content)
        
    except Exception as e:
        print(f"Erro ao listar e copiar arquivos: {e}")

if __name__ == "__main__":
    # Diretório atual (C:\Users\Usuario\Desktop\teste)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    list_files_to_clipboard(current_dir)