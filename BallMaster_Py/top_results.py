#!/usr/bin/env python3
"""
Модуль для управления топ-30 лучшими результатами жонглирования.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TopResult:
    """Структура для хранения лучшего результата."""
    video_name: str
    total_kicks: int
    total_series: int
    best_series_kicks: int
    best_series_duration: float
    processing_time: float
    timestamp: str
    score: float


class TopResultsManager:
    """Менеджер для управления топ-30 результатами."""
    
    def __init__(self, storage_file: str = "top_results.json", max_results: int = 30):
        self.storage_file = Path(storage_file)
        self.max_results = max_results
        self.results: List[TopResult] = []
        self._load_results()
    
    def _load_results(self):
        """Загружает результаты из файла."""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.results = []
                for result_data in data.get("results", []):
                    # Убираем лишние поля, которых нет в TopResult
                    clean_data = {k: v for k, v in result_data.items() 
                                if k in ['video_name', 'total_kicks', 'total_series', 
                                       'best_series_kicks', 'best_series_duration', 
                                       'processing_time', 'timestamp', 'score']}
                    self.results.append(TopResult(**clean_data))
                
                self._sort_results()
                logging.info(f"Загружено {len(self.results)} результатов")
            else:
                logging.info("Файл результатов не найден, создаем новый")
        except Exception as e:
            logging.error(f"Ошибка загрузки результатов: {e}")
            self.results = []
    
    def _save_results(self):
        """Сохраняет результаты в файл."""
        try:
            data = {
                "max_results": self.max_results,
                "last_updated": datetime.now().isoformat(),
                "results": [asdict(result) for result in self.results]
            }
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Сохранено {len(self.results)} результатов")
        except Exception as e:
            logging.error(f"Ошибка сохранения результатов: {e}")
    
    def _sort_results(self):
        """Сортирует результаты по убыванию очков."""
        self.results.sort(key=lambda x: x.score, reverse=True)
    
    def _calculate_score(self, total_kicks: int, total_series: int, 
                        best_series_kicks: int, best_series_duration: float, 
                        processing_time: float) -> float:
        """Вычисляет оценку результата."""
        base_score = total_kicks * 10
        series_bonus = best_series_kicks * 20 + best_series_duration * 5
        efficiency_bonus = (total_kicks / max(processing_time, 1)) * 50
        time_penalty = processing_time * 0.1
        
        return round(base_score + series_bonus + efficiency_bonus - time_penalty, 2)
    
    def add_result(self, video_name: str, total_kicks: int, total_series: int,
                   best_series_kicks: int, best_series_duration: float, 
                   processing_time: float) -> bool:
        """Добавляет новый результат в топ-30."""
        score = self._calculate_score(total_kicks, total_series, best_series_kicks, 
                                    best_series_duration, processing_time)
        
        new_result = TopResult(
            video_name=video_name,
            total_kicks=total_kicks,
            total_series=total_series,
            best_series_kicks=best_series_kicks,
            best_series_duration=best_series_duration,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            score=score
        )
        
        # Если есть место, добавляем
        if len(self.results) < self.max_results:
            self.results.append(new_result)
            self._sort_results()
            self._save_results()
            return True
        
        # Если результат лучше худшего, заменяем
        if score > self.results[-1].score:
            self.results[-1] = new_result
            self._sort_results()
            self._save_results()
            return True
        
        return False
    
    def get_top_results(self, limit: Optional[int] = None) -> List[TopResult]:
        """Возвращает топ результаты."""
        if limit is None:
            limit = self.max_results
        return self.results[:limit]
    
    def get_results_for_export(self) -> Dict:
        """Возвращает результаты для экспорта/отправки."""
        return {
            "max_results": self.max_results,
            "total_saved": len(self.results),
            "last_updated": datetime.now().isoformat(),
            "results": [asdict(result) for result in self.results]
        }


# Глобальный экземпляр менеджера
top_results = TopResultsManager() 