import os

def add_missing_methods():
    """Добавление отсутствующих методов в TBankAPIComplete"""
    
    filepath = "tbank_api/tbank_api_fixed_complete.py"
    
    if not os.path.exists(filepath):
        print(f"❌ Файл {filepath} не найден")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Методы которые нужно добавить
        missing_methods = '''
    def _get_figi_by_ticker(self, ticker: str) -> str:
        """Получение FIGI по тикеру (упрощенная версия)"""
        instruments = self._get_instruments_safe()
        if instruments.empty:
            return f"FIGI_{ticker}"  # Заглушка
        
        match = instruments[instruments['symbol'] == ticker]
        if not match.empty:
            return match.iloc[0]['figi']
        
        return f"FIGI_{ticker}"  # Заглушка

    def get_historical_data(self, symbol: str, start_date: str, end_date: str = None, timeframe: str = '1d') -> pd.DataFrame:
        """
        Получение исторических данных (упрощенная версия - возвращает пустой DataFrame)
        """
        logger.warning(f"⚠️  Tinkoff API временно отключен. Не могу загрузить данные для {symbol}")
        return pd.DataFrame()

    def get_current_quotes(self, symbols: List[str]) -> pd.DataFrame:
        """
        Получение текущих котировок (упрощенная версия)
        """
        logger.warning(f"⚠️  Tinkoff API временно отключен. Не могу загрузить котировки для {symbols}")
        return pd.DataFrame()

    def clear_cache(self):
        """Очистка кэшей"""
        self._figi_cache.clear()
        self._instruments_cache = None
        self._last_instruments_update = None
        logger.info("✅ Кэши Tinkoff API очищены")

    def get_account_info(self) -> Dict:
        """
        Получение информации о счетах
        """
        logger.warning("⚠️  Tinkoff API временно отключен")
        return {}
'''
        
        # Находим место для вставки (после метода is_available)
        if "def is_available(" in content:
            # Вставляем после is_available
            insert_point = content.find("def is_available(")
            # Ищем конец этого метода
            method_end = content.find("\\n\\n", insert_point)
            if method_end == -1:
                method_end = len(content)
            
            # Вставляем новые методы
            new_content = content[:method_end] + missing_methods + content[method_end:]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Отсутствующие методы добавлены в TBankAPIComplete!")
            return True
        else:
            print("❌ Не найдено место для вставки методов")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка добавления методов: {e}")
        return False

if __name__ == "__main__":
    add_missing_methods()