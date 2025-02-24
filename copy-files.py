import os
import pyperclip
from pathlib import Path

def read_file_content(file_path: str) -> str:
    """Lê o conteúdo de um arquivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()

def should_skip_directory(dir_name: str) -> bool:
    """Verifica se um diretório deve ser ignorado"""
    skip_dirs = ['__pycache__', '.devcontainer', 'venv', '-env']
    return any(skip in dir_name for skip in skip_dirs)

def copy_files_to_clipboard():
    """Copia o conteúdo dos arquivos .py para o clipboard"""
    try:
        # Diretório atual
        current_dir = os.path.dirname(os.path.abspath(__file__))
        all_content = []

        # Percorre todos os arquivos no diretório atual
        for root, dirs, files in os.walk(current_dir):
            # Remove diretórios que devem ser ignorados
            dirs[:] = [d for d in dirs if not should_skip_directory(d)]
            
            for file in files:
                # Pega apenas arquivos .py que não começam com 'test'
                if file.endswith('.py') and not file.startswith('test'):
                    file_path = os.path.join(root, file)
                    try:
                        content = read_file_content(file_path)
                        relative_path = os.path.relpath(file_path, current_dir)
                        
                        file_info = f"""
{'='*50}
Arquivo: {relative_path}
{'='*50}
{content}
"""
                        all_content.append(file_info)
                        print(f"Lido: {relative_path}")
                    except Exception as e:
                        print(f"Erro ao ler {file}: {e}")

        # Junta todo o conteúdo e copia para o clipboard
        final_content = "\n".join(all_content)
        pyperclip.copy(final_content)
        print("\nConteúdo copiado para o clipboard com sucesso!")
        print(f"Total de arquivos copiados: {len(all_content)}")
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    copy_files_to_clipboard()