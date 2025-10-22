# find_tbank_config_usage.py
import os
import re

def find_tbank_config_usage(root_dir='.'):
    """Найти все файлы, которые используют tbank_config"""
    
    usage_files = []
    
    for root, dirs, files in os.walk(root_dir):
        # Пропускаем папки, которые не нужно проверять
        if 'venv' in root or '__pycache__' in root or '.git' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Ищем импорты tbank_config
                    patterns = [
                        r'from\s+tbank_config',
                        r'import\s+tbank_config',
                        r'TBankConfig',
                        r'tbank_config\.'
                    ]
                    
                    for pattern in patterns:
                        if re.search(pattern, content):
                            usage_files.append({
                                'file': file_path,
                                'pattern': pattern,
                                'content': content
                            })
                            break  # Чтобы не дублировать файлы
                            
                except Exception as e:
                    print(f"❌ Ошибка чтения {file_path}: {e}")
    
    return usage_files

def analyze_usage(usage_files):
    """Анализировать как используется tbank_config"""
    
    print("📊 АНАЛИЗ ИСПОЛЬЗОВАНИЯ TBANK_CONFIG:")
    print("=" * 50)
    
    for usage in usage_files:
        print(f"\n📁 Файл: {usage['file']}")
        print(f"🔍 Паттерн: {usage['pattern']}")
        
        # Показываем контекст использования
        lines = usage['content'].split('\n')
        for i, line in enumerate(lines, 1):
            if 'tbank_config' in line.lower() or 'TBankConfig' in line:
                print(f"   Строка {i}: {line.strip()}")
        
        print("-" * 30)

if __name__ == "__main__":
    print("🔍 Поиск использований tbank_config...")
    
    usage_files = find_tbank_config_usage()
    
    if usage_files:
        print(f"✅ Найдено {len(usage_files)} файлов с использованием tbank_config:")
        analyze_usage(usage_files)
        
        # Сохраняем результат в файл
        with open('tbank_config_usage_report.txt', 'w', encoding='utf-8') as f:
            f.write("ОТЧЕТ ПО ИСПОЛЬЗОВАНИЮ TBANK_CONFIG\n")
            f.write("=" * 50 + "\n")
            for usage in usage_files:
                f.write(f"\nФайл: {usage['file']}\n")
                f.write(f"Паттерн: {usage['pattern']}\n")
                f.write("-" * 30 + "\n")
                
        print(f"\n📄 Полный отчет сохранен в: tbank_config_usage_report.txt")
    else:
        print("✅ Файлы с tbank_config не найдены!")