"""
Сканирование существующей структуры проекта и сохранение в файл
"""

import os
from pathlib import Path

def scan_project_structure(start_path=".", output_file="project_structure.txt"):
    """
    Сканирует существующую структуру проекта и сохраняет в файл
    """
    start_path = Path(start_path)
    
    print(f"Сканирую структуру проекта в: {start_path.absolute()}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Счетчики
        total_files = 0
        total_dirs = 0
        
        for root, dirs, files in os.walk(start_path):
            # Пропускаем служебные папки
            dirs[:] = [d for d in dirs if d not in {
                '__pycache__', '.git', '.vscode', '.idea', 
                'venv', 'env', 'node_modules', '.pytest_cache'
            } and not d.startswith('.')]
            
            # Уровень вложенности
            level = root.replace(str(start_path), '').count(os.sep)
            indent = '    ' * level
            
            # Относительный путь
            if root == str(start_path):
                f.write(f"{start_path.name}/\n")
                total_dirs += 1
            else:
                dir_name = os.path.basename(root)
                f.write(f"{indent}{dir_name}/\n")
                total_dirs += 1
            
            # Файлы в текущей директории
            sub_indent = '    ' * (level + 1)
            for file in sorted(files):
                # Пропускаем служебные файлы
                if file in {'.DS_Store', 'Thumbs.db', 'desktop.ini'} or file.startswith('.'):
                    continue
                
                f.write(f"{sub_indent}{file}\n")
                total_files += 1
    
    print(f"Структура сохранена в: {output_file}")
    print(f"Найдено: {total_dirs} папок, {total_files} файлов")
    return total_dirs, total_files

if __name__ == "__main__":
    print("Начинаю сканирование проекта...")
    dirs, files = scan_project_structure()
    print("Сканирование завершено!")