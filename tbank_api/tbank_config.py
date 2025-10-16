# tbank_api/tbank_config.py
"""
Конфигурация для модуля Т-банка API
"""

import os
import json
from typing import Dict, Any

class TBankConfig:
    """Класс конфигурации для Т-банка API"""
    
    DEFAULT_CONFIG = {
        'api_url': 'https://api.tbank.ru/investments/v1',
        'timeout': 30,
        'max_retries': 3,
        'default_timeframe': '1d',
        'supported_timeframes': ['1m', '5m', '15m', '1h', '4h', '1d', '1w'],
        'cache_duration_minutes': 5
    }
    
    def __init__(self, config_file: str = None):
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = config_file or os.path.join(os.path.dirname(__file__), 'tbank_config.json')
        self.load_config()
    
    def load_config(self):
        """Загрузка конфигурации из файла"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                print(f"✅ Конфигурация загружена из {self.config_file}")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки конфигурации: {e}")
        else:
            print(f"ℹ️ Файл конфигурации не найден: {self.config_file}")
            self.create_default_config()
    
    def create_default_config(self):
        """Создание файла конфигурации по умолчанию"""
        try:
            # Создаем папку если не существует
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            default_config = {
                'api_key': '',  # Пустой ключ по умолчанию
                **self.DEFAULT_CONFIG
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Создан файл конфигурации: {self.config_file}")
            print("ℹ️ Пожалуйста, добавьте ваш API ключ в файл конфигурации")
            
        except Exception as e:
            print(f"❌ Ошибка создания файла конфигурации: {e}")
    
    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ Конфигурация сохранена в {self.config_file}")
        except Exception as e:
            print(f"❌ Ошибка сохранения конфигурации: {e}")
    
    def get(self, key: str, default=None):
        """Получение значения конфигурации"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Установка значения конфигурации"""
        self.config[key] = value
        self.save_config()
    
    def get_api_key(self) -> str:
        """Получение API ключа из конфигурации"""
        return self.config.get('api_key', '')
    
    def set_api_key(self, api_key: str):
        """Установка API ключа"""
        self.set('api_key', api_key)
        print("✅ API ключ сохранен в конфигурации")
    
    def validate_config(self) -> bool:
        """Валидация конфигурации"""
        required_fields = ['api_url']
        return all(field in self.config for field in required_fields)
    
    def is_api_key_set(self) -> bool:
        """Проверка, установлен ли API ключ"""
        api_key = self.get_api_key()
        return bool(api_key and api_key.strip())
    
    def get_config_path(self) -> str:
        """Получение пути к файлу конфигурации"""
        return self.config_file