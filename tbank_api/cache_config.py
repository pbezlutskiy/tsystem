# tbank_api/cache_config.py
"""
Конфигурация системы кэширования данных Tinkoff API
"""

import os
from pathlib import Path
from datetime import timedelta
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class CacheConfig:
    """Настройки кэширования данных"""
    
    # Основные пути
    base_cache_dir: Path = Path("tbank_api/data_cache")
    instruments_cache_dir: Path = base_cache_dir / "instruments"
    candles_cache_dir: Path = base_cache_dir / "candles"
    metadata_dir: Path = base_cache_dir / "metadata"
    
    # Время жизни кэша
    instruments_ttl: timedelta = timedelta(hours=24)  # 24 часа для инструментов
    candles_ttl: timedelta = timedelta(minutes=15)    # 15 минут для свечей
    quotes_ttl: timedelta = timedelta(minutes=2)      # 2 минуты для котировок
    
    # Настройки файлов
    file_extension: str = ".parquet"  # Используем parquet для эффективности
    compression: str = "snappy"
    
    # Лимиты
    max_candle_files_per_instrument: int = 100
    cache_enabled: bool = True
    
    def __post_init__(self):
        """Создание директорий при инициализации"""
        self.instruments_cache_dir.mkdir(parents=True, exist_ok=True)
        self.candles_cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def get_instrument_cache_path(self, instrument_type: str = "all") -> Path:
        """Путь к файлу кэша инструментов"""
        return self.instruments_cache_dir / f"{instrument_type}_instruments{self.file_extension}"
    
    def get_candle_cache_path(self, figi: str, timeframe: str, date_str: str) -> Path:
        """Путь к файлу кэша свечей"""
        safe_figi = figi.replace("/", "_")
        filename = f"{safe_figi}_{timeframe}_{date_str}{self.file_extension}"
        return self.candles_cache_dir / filename
    
    def get_metadata_path(self, key: str) -> Path:
        """Путь к файлу метаданных"""
        return self.metadata_dir / f"{key}.json"