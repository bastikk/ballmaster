#!/usr/bin/env python3
"""
Скрипт для экспорта топ-30 результатов жонглирования.
"""

import json
from pathlib import Path
from top_results import top_results

def export_results(output_file: str = "exported_results.json") -> None:
    """Экспортирует топ результаты в JSON файл."""
    data = top_results.get_results_for_export()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Результаты экспортированы в {output_file}")
    print(f"📊 Всего результатов: {data['total_saved']}")
    print(f"🕒 Последнее обновление: {data['last_updated']}")

def main():
    """Основная функция."""
    print("📤 ЭКСПОРТ ТОП-30 РЕЗУЛЬТАТОВ")
    print("=" * 40)
    
    export_results()

if __name__ == '__main__':
    main() 