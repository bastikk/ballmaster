#!/usr/bin/env python3
"""
Скрипт для просмотра топ-30 результатов жонглирования.
"""

import logging
from top_results import top_results

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

def main():
    """Показывает топ результаты."""
    print("🏆 ТОП-30 РЕЗУЛЬТАТОВ ЖОНГЛИРОВАНИЯ 🏆")
    print("=" * 50)
    
    results = top_results.get_top_results()
    
    if not results:
        print("Пока нет сохраненных результатов")
        return
    
    print(f"Всего сохранено: {len(results)} результатов")
    print()
    
    for i, result in enumerate(results, 1):
        print(f"{i:2d}. {result.video_name}")
        print(f"    Балл: {result.score:.1f} | Набиваний: {result.total_kicks} | "
              f"Серий: {result.total_series} | Лучшая серия: {result.best_series_kicks} набиваний")
        print(f"    Время обработки: {result.processing_time:.1f}с | {result.timestamp}")
        print()

if __name__ == '__main__':
    main() 