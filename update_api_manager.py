import os

def update_api_manager():
    """Обновление ApiManager для использования исправленного TBankAPI"""
    
    filepath = "tbank_api/api_manager.py"
    
    if not os.path.exists(filepath):
        print(f"❌ Файл {filepath} не найден")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем импорт и инициализацию
        old_import = "from .tbank_api import TBankAPI"
        new_import = "from .tbank_api_fixed_complete import TBankAPIComplete as TBankAPI"
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ ApiManager обновлен для использования исправленного TBankAPI!")
            return True
        else:
            print("⚠️  Импорт уже обновлен или не найден")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка обновления ApiManager: {e}")
        return False

if __name__ == "__main__":
    update_api_manager()