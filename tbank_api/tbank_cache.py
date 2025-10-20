# tbank_api/tbank_cache.py
"""
Система кэширования данных Tinkoff API
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging
from .cache_config import CacheConfig

logger = logging.getLogger(__name__)

class TBankCache:
    """Кэширование данных Tinkoff API с поддержкой инкрементального обновления"""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self._memory_cache = {}  # Быстрый кэш в памяти
        
    # ===== КЭШИРОВАНИЕ ИНСТРУМЕНТОВ =====
    
    def save_instruments(self, instruments_df: pd.DataFrame, instrument_type: str = "all") -> bool:
        """Сохранение списка инструментов в кэш"""
        if not self.config.cache_enabled or instruments_df.empty:
            return False
            
        try:
            cache_path = self.config.get_instrument_cache_path(instrument_type)
            
            # Сохраняем в parquet
            instruments_df.to_parquet(
                cache_path,
                engine='pyarrow',
                compression=self.config.compression,
                index=False
            )
            
            # Сохраняем метаданные
            metadata = {
                'cached_at': datetime.now().isoformat(),
                'instrument_type': instrument_type,
                'count': len(instruments_df),
                'columns': list(instruments_df.columns)
            }
            self._save_metadata(f"instruments_{instrument_type}", metadata)
            
            # Сохраняем в memory cache
            cache_key = f"instruments_{instrument_type}"
            self._memory_cache[cache_key] = instruments_df.copy()
            
            logger.info(f"✅ Инструменты типа '{instrument_type}' сохранены в кэш ({len(instruments_df)} записей)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения инструментов в кэш: {e}")
            return False
    
    def load_instruments(self, instrument_type: str = "all", 
                        force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """Загрузка списка инструментов из кэша"""
        if not self.config.cache_enabled:
            return None
            
        # Проверка memory cache
        cache_key = f"instruments_{instrument_type}"
        if not force_refresh and cache_key in self._memory_cache:
            logger.debug(f"Инструменты загружены из memory cache: {instrument_type}")
            return self._memory_cache[cache_key].copy()
        
        cache_path = self.config.get_instrument_cache_path(instrument_type)
        
        if not cache_path.exists():
            return None
            
        # Проверка актуальности кэша
        if not self._is_cache_valid(f"instruments_{instrument_type}", self.config.instruments_ttl):
            if not force_refresh:
                return None
        
        try:
            # Загрузка из файла
            instruments_df = pd.read_parquet(cache_path)
            
            # Сохраняем в memory cache
            self._memory_cache[cache_key] = instruments_df.copy()
            
            logger.info(f"✅ Инструменты загружены из кэша: {instrument_type} ({len(instruments_df)} записей)")
            return instruments_df
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки инструментов из кэша: {e}")
            return None
    
    # ===== КЭШИРОВАНИЕ СВЕЧЕЙ =====
    
    def save_candles(self, figi: str, timeframe: str, 
                    candles_df: pd.DataFrame, date_range: tuple) -> bool:
        """Сохранение свечей в кэш"""
        if not self.config.cache_enabled or candles_df.empty:
            return False
            
        try:
            # Генерируем ключ на основе дат
            start_date, end_date = date_range
            date_str = f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            
            cache_path = self.config.get_candle_cache_path(figi, timeframe, date_str)
            
            # Сохраняем данные
            candles_df.to_parquet(
                cache_path,
                engine='pyarrow',
                compression=self.config.compression,
                index=True  # Индекс - это дата
            )
            
            # Сохраняем метаданные
            metadata = {
                'figi': figi,
                'timeframe': timeframe,
                'cached_at': datetime.now().isoformat(),
                'date_range': [start_date.isoformat(), end_date.isoformat()],
                'count': len(candles_df),
                'date_str': date_str
            }
            self._save_metadata(f"candles_{figi}_{timeframe}_{date_str}", metadata)
            
            logger.info(f"✅ Свечи {figi} ({timeframe}) сохранены в кэш ({len(candles_df)} записей)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения свечей в кэш: {e}")
            return False
    
    def load_candles(self, figi: str, timeframe: str, 
                    start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Загрузка свечей из кэша"""
        if not self.config.cache_enabled:
            return None
            
        date_str = f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        cache_path = self.config.get_candle_cache_path(figi, timeframe, date_str)
        
        if not cache_path.exists():
            return None
            
        # Проверка актуальности кэша
        if not self._is_cache_valid(f"candles_{figi}_{timeframe}_{date_str}", self.config.candles_ttl):
            return None
        
        try:
            candles_df = pd.read_parquet(cache_path)
            logger.info(f"✅ Свечи загружены из кэша: {figi} ({timeframe}) - {len(candles_df)} записей")
            return candles_df
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки свечей из кэша: {e}")
            return None
    
    def find_cached_candle_periods(self, figi: str, timeframe: str) -> List[tuple]:
        """Поиск всех кэшированных периодов для инструмента"""
        pattern = f"{figi.replace('/', '_')}_{timeframe}_*.parquet"
        cache_files = list(self.config.candles_cache_dir.glob(pattern))
        
        periods = []
        for file_path in cache_files:
            try:
                # Извлекаем даты из имени файла
                filename = file_path.stem
                date_part = filename.split('_')[-2:]  # Последние две части - даты
                if len(date_part) == 2:
                    start_date = datetime.strptime(date_part[0], '%Y%m%d')
                    end_date = datetime.strptime(date_part[1], '%Y%m%d')
                    periods.append((start_date, end_date, file_path))
            except Exception as e:
                logger.warning(f"Не удалось обработать файл кэша {file_path}: {e}")
        
        return periods
    
    # ===== ИНКРЕМЕНТАЛЬНОЕ ОБНОВЛЕНИЕ =====
    
    def update_candles_incrementally(self, figi: str, timeframe: str,
                                   new_candles_df: pd.DataFrame) -> pd.DataFrame:
        """Инкрементальное обновление кэша свечей"""
        if new_candles_df.empty:
            return new_candles_df
        
        # Находим существующие кэшированные периоды
        cached_periods = self.find_cached_candle_periods(figi, timeframe)
        
        if not cached_periods:
            # Нет кэша, сохраняем все данные
            start_date = new_candles_df.index.min()
            end_date = new_candles_df.index.max()
            self.save_candles(figi, timeframe, new_candles_df, (start_date, end_date))
            return new_candles_df
        
        # Объединяем с существующими данными
        all_candles = []
        for start, end, cache_path in cached_periods:
            try:
                cached_data = pd.read_parquet(cache_path)
                all_candles.append(cached_data)
            except Exception as e:
                logger.warning(f"Ошибка загрузки кэша {cache_path}: {e}")
        
        if all_candles:
            # Объединяем все кэшированные данные
            combined_cached = pd.concat(all_candles).drop_duplicates().sort_index()
            
            # Объединяем с новыми данными
            combined_all = pd.concat([combined_cached, new_candles_df]).drop_duplicates().sort_index()
            
            # Сохраняем обновленный кэш
            start_date = combined_all.index.min()
            end_date = combined_all.index.max()
            self.save_candles(figi, timeframe, combined_all, (start_date, end_date))
            
            logger.info(f"✅ Кэш свечей обновлен инкрементально: {figi} ({timeframe})")
            return combined_all
        
        return new_candles_df
    
    # ===== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====
    
    def _save_metadata(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Сохранение метаданных кэша"""
        try:
            metadata_path = self.config.get_metadata_path(key)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных {key}: {e}")
            return False
    
    def _load_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Загрузка метаданных кэша"""
        try:
            metadata_path = self.config.get_metadata_path(key)
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки метаданных {key}: {e}")
        return None
    
    def _is_cache_valid(self, cache_key: str, ttl: timedelta) -> bool:
        """Проверка актуальности кэша"""
        metadata = self._load_metadata(cache_key)
        if not metadata or 'cached_at' not in metadata:
            return False
        
        try:
            cached_at = datetime.fromisoformat(metadata['cached_at'])
            return (datetime.now() - cached_at) < ttl
        except Exception:
            return False
    
    def clear_cache(self, cache_type: str = None):
        """Очистка кэша"""
        try:
            if cache_type == "instruments" or cache_type is None:
                # Очистка кэша инструментов
                for file in self.config.instruments_cache_dir.glob("*.parquet"):
                    file.unlink()
                logger.info("✅ Кэш инструментов очищен")
            
            if cache_type == "candles" or cache_type is None:
                # Очистка кэша свечей
                for file in self.config.candles_cache_dir.glob("*.parquet"):
                    file.unlink()
                logger.info("✅ Кэш свечей очищен")
            
            # Очистка memory cache
            self._memory_cache.clear()
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Статистика кэша"""
        stats = {
            'instruments_cache_size': len(list(self.config.instruments_cache_dir.glob("*.parquet"))),
            'candles_cache_size': len(list(self.config.candles_cache_dir.glob("*.parquet"))),
            'memory_cache_entries': len(self._memory_cache),
            'total_cache_size_mb': self._get_total_cache_size()
        }
        return stats
    
    def _get_total_cache_size(self) -> float:
        """Общий размер кэша в мегабайтах"""
        total_size = 0
        for cache_dir in [self.config.instruments_cache_dir, self.config.candles_cache_dir]:
            for file in cache_dir.glob("**/*"):
                if file.is_file():
                    total_size += file.stat().st_size
        return total_size / (1024 * 1024)  # Convert to MB