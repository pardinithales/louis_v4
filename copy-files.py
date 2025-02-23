import os
import pyperclip
from typing import Optional

def read_file_content(file_path: str) -> Optional[str]:
    """
    Lê o conteúdo de um arquivo, retornando None se não for legível.
    """
    try:
        # Ler como texto, assumindo UTF-8 (com fallback para Latin-1 se necessário)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Limitar o conteúdo a 1.000 caracteres
        if len(content) > 1000:
            content = content[:1000] + "... (conteúdo truncado)"
        return content.strip()
    except Exception as e:
        print(f"Erro ao ler {file_path}: {e}")
        return None

def list_files_to_clipboard(directory: str, exclude_dir: str = None):
    """
    Lista todos os arquivos .py e .env no diretório especificado, excluindo um diretório específico.
    """
    try:
        absolute_dir = os.path.abspath(directory)
        file_list = []
        
        # Extensões permitidas
        allowed_extensions = ('.py', '.env')
        
        # Percorrer diretório e subdiretórios
        for root, dirs, files in os.walk(absolute_dir):
            # Pular o diretório excluído
            if exclude_dir and exclude_dir in root:
                continue
                
            # Filtrar arquivos com extensões permitidas
            for file in files:
                if file.endswith(allowed_extensions):
                    item_path = os.path.join(root, file)
                    file_info = f"Nome: {file}\nLocalização: {item_path}\n"
                    
                    content = read_file_content(item_path)
                    if content is not None:
                        file_info += f"Conteúdo:\n{content}\n{'-'*50}\n"
                    
                    file_list.append(file_info)
        
        clipboard_content = "\n".join(file_list)
        pyperclip.copy(clipboard_content)
        
        print("Lista de arquivos .py e .env copiada para o clipboard com sucesso!")
        print("\nPré-visualização:\n")
        print(clipboard_content[:2000] + "..." if len(clipboard_content) > 2000 else clipboard_content)
        
    except Exception as e:
        print(f"Erro ao listar e copiar arquivos: {e}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    exclude_dir = r"C:\Users\Usuario\Desktop\teste\pykx-env"
    list_files_to_clipboard(current_dir, exclude_dir)