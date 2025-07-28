#!/usr/bin/env python3
"""
Тестовый клиент для Flask API сервера.
"""

import requests
import json
from pathlib import Path

API_BASE_URL = "http://localhost:5000"

def test_health():
    """Тестирует эндпоинт проверки состояния."""
    print("🏥 Тестирование /health...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_upload_video(video_path: Path):
    """Тестирует загрузку и обработку видео."""
    print(f"📤 Тестирование /upload с файлом {video_path.name}...")
    
    if not video_path.exists():
        print(f"❌ Файл {video_path} не найден!")
        return
    
    with open(video_path, 'rb') as f:
        files = {'video': (video_path.name, f, 'video/mp4')}
        response = requests.post(f"{API_BASE_URL}/upload", files=files)
    
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_get_results(limit: int = 5):
    """Тестирует получение результатов."""
    print(f"📊 Тестирование /results с лимитом {limit}...")
    response = requests.get(f"{API_BASE_URL}/results?limit={limit}")
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_get_stats():
    """Тестирует получение статистики."""
    print("📈 Тестирование /stats...")
    response = requests.get(f"{API_BASE_URL}/stats")
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_export():
    """Тестирует экспорт результатов."""
    print("📤 Тестирование /export...")
    response = requests.get(f"{API_BASE_URL}/export")
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_get_saved_videos():
    """Тестирует получение списка сохраненных видео."""
    print("📹 Тестирование /videos...")
    response = requests.get(f"{API_BASE_URL}/videos")
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def main():
    """Основная функция тестирования."""
    print("🧪 ТЕСТИРОВАНИЕ FLASK API СЕРВЕРА")
    print("=" * 50)
    
    # Проверяем состояние сервера
    try:
        test_health()
    except requests.exceptions.ConnectionError:
        print("❌ Сервер не запущен! Запустите python api_server.py")
        return
    
    # Тестируем получение результатов
    test_get_results(3)
    
    # Тестируем статистику
    test_get_stats()
    
    # Тестируем список сохраненных видео
    test_get_saved_videos()
    
    # Тестируем экспорт
    test_export()
    
    print("✅ Тестирование завершено!")
    print("📱 Для тестирования загрузки видео используйте Android приложение")

if __name__ == '__main__':
    main() 