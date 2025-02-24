import os
import shutil
from pathlib import Path

def copy_files(source_dir, dest_dir):
    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    
    # Get all files in the source directory
    for item in os.listdir(source_dir):
        source_path = os.path.join(source_dir, item)
        dest_path = os.path.join(dest_dir, item)
        
        # Skip __pycache__ and .devcontainer directories
        if item in ['__pycache__', '.devcontainer']:
            continue
            
        # Copy Python files that don't have 'test' in the name
        if item.endswith('.py') and 'test' not in item.lower():
            shutil.copy2(source_path, dest_path)
            print(f'Copied: {item}')
            
        # Copy specific files
        elif item in ['Dockerfile', '.gitignore', 'secrets.toml']:
            shutil.copy2(source_path, dest_path)
            print(f'Copied: {item}')

if __name__ == '__main__':
    # Get the current directory (root)
    source_dir = os.path.dirname(os.path.abspath(__file__))
    # Create a 'copied_files' directory in the root
    dest_dir = os.path.join(source_dir, 'copied_files')
    
    copy_files(source_dir, dest_dir)
    print(f'\nFiles have been copied to: {dest_dir}')