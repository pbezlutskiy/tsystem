# check_structure.py
"""
Проверка структуры проекта
"""

import os

def check_tbank_api_structure():
    """Проверяем структуру папки tbank_api"""
    
    print("🔍 ПРОВЕРКА СТРУКТУРЫ TBANK_API")
    print("=" * 40)
    
    tbank_path = "tbank_api"
    
    if not os.path.exists(tbank_path):
        print(f"❌ Папка {tbank_path} не существует")
        return False
    
    print(f"✅ Папка {tbank_path} существует")
    
    # Проверяем необходимые файлы
    required_files = [
        '__init__.py',
        'tbank_api.py', 
        'tbank_config.py',
        'tbank_config.json',
        'api_manager.py'
    ]
    
    for file in required_files:
        file_path = os.path.join(tbank_path, file)
        if os.path.exists(file_path):
            print(f"✅ {file} - существует")
        else:
            print(f"❌ {file} - отсутствует")
    
    # Показываем содержимое папки
    print(f"\n📁 Содержимое папки {tbank_path}:")
    for item in os.listdir(tbank_path):
        item_path = os.path.join(tbank_path, item)
        if os.path.isfile(item_path):
            print(f"   📄 {item}")
        else:
            print(f"   📁 {item}/")

if __name__ == "__main__":
    check_tbank_api_structure()