import os
import re

def find_realexchange_usage():
    """Поиск всех упоминаний RealExchange в проекте"""
    project_dir = "D:\\Documents\\PythonScripts\\trading_system22"
    
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Ищем упоминания RealExchange
                    if 'real_exchange' in content.lower() or 'RealExchange' in content:
                        print(f"🔍 Найдено в: {file_path}")
                        
                        # Показываем контекст
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'real_exchange' in line.lower() or 'RealExchange' in line:
                                print(f"   Строка {i+1}: {line.strip()}")
                        print()
                        
                except Exception as e:
                    print(f"Ошибка чтения {file_path}: {e}")

if __name__ == "__main__":
    find_realexchange_usage()