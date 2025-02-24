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

def should_skip_directory(dir_path: str, exclude_dir: str = None) -> bool:
    """
    Verifica se um diretório deve ser ignorado.
    """
    dir_name = os.path.basename(dir_path)
    # Ignora __pycache__, diretórios com -env, venv (exceto se for o diretório específico a ser excluído)
    if ('__pycache__' in dir_path or 
        '-env' in dir_name or 
        'venv' in dir_name and dir_path != exclude_dir):
        return True
    # Verifica se é o diretório específico a ser excluído
    if exclude_dir and exclude_dir in dir_path:
        return True
    return False

def should_skip_file(file_name: str) -> bool:
    """
    Verifica se um arquivo deve ser ignorado.
    """
    # Ignora arquivos que começam com 'test'
    return file_name.startswith('test')

def list_files_to_clipboard(directory: str, exclude_dir: str = None):
    """
    Lista apenas arquivos .py, excluindo os que começam com 'test'.
    """
    try:
        absolute_dir = os.path.abspath(directory)
        file_list = []
        
        # Percorrer diretório e subdiretórios
        for root, dirs, files in os.walk(absolute_dir):
            # Filtrar diretórios a serem ignorados
            if should_skip_directory(root, exclude_dir):
                continue
            
            # Remover diretórios indesejados da lista para não percorrê-los
            dirs[:] = [d for d in dirs if not should_skip_directory(os.path.join(root, d), exclude_dir)]
                
            # Filtrar apenas arquivos .py que não começam com 'test'
            for file in files:
                if file.endswith('.py') and not should_skip_file(file):
                    item_path = os.path.join(root, file)
                    file_info = f"Nome: {file}\nLocalização: {item_path}\n"
                    
                    content = read_file_content(item_path)
                    if content is not None:
                        file_info += f"Conteúdo:\n{content}\n{'-'*50}\n"
                    
                    file_list.append(file_info)
        
        clipboard_content = "\n".join(file_list)
        pyperclip.copy(clipboard_content)
        
        print(f"Lista de arquivos .py (exceto os que começam com 'test') copiada para o clipboard com sucesso!")
        print("Diretórios ignorados: __pycache__ e pastas com -env")
        print("\nPré-visualização:\n")
        print(clipboard_content[:2000] + "..." if len(clipboard_content) > 2000 else clipboard_content)
        
    except Exception as e:
        print(f"Erro ao listar e copiar arquivos: {e}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    exclude_dir = r"C:\Users\Usuario\Desktop\teste\pykx-env"
    list_files_to_clipboard(current_dir, exclude_dir)