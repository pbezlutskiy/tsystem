import os
import re

def find_instrument_service_imports():
    """Поиск всех импортов InstrumentServiceWorking"""
    project_dir = "D:\\Documents\\PythonScripts\\trading_system22"
    
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Ищем упоминания InstrumentServiceWorking
                    if 'InstrumentServiceWorking' in content:
                        print(f"🔍 Найдено в: {file_path}")
                        
                        # Показываем контекст
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'InstrumentServiceWorking' in line:
                                print(f"   Строка {i+1}: {line.strip()}")
                        print()
                        
                except Exception as e:
                    print(f"Ошибка чтения {file_path}: {e}")

if __name__ == "__main__":
    find_instrument_service_imports()