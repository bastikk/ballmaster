#!/usr/bin/env python3
"""
Тест для имитации загрузки видео с телефона.
"""

import requests
import json
from pathlib import Path

# Конфигурация
API_BASE_URL = "http://localhost:5000"

def test_phone_video_upload():
    """Имитирует загрузку видео с телефона."""
    print("📱 ИМИТАЦИЯ ЗАГРУЗКИ ВИДЕО С ТЕЛЕФОНА")
    print("=" * 50)
    
    # Используем файл juggling2 для тестирования
    video_file_path = Path("videos/juggling2.mp4")
    
    if not video_file_path.exists():
        print(f"❌ Файл не найден: {video_file_path}")
        return
    
    print(f"📹 Используем файл: {video_file_path.name}")
    print(f"📊 Размер файла: {video_file_path.stat().st_size / (1024*1024):.2f} MB")
    
    try:
        # Имитируем загрузку файла как с телефона
        with open(video_file_path, 'rb') as video_file:
            files = {
                'video': (video_file_path.name, video_file, 'video/mp4')
            }
            
            print("🚀 Отправляем POST запрос на /upload...")
            response = requests.post(f"{API_BASE_URL}/upload", files=files)
            
            print(f"📡 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Успешная загрузка!")
                print(f"📊 Результат анализа:")
                print(f"   🥾 Набиваний: {result['data']['total_kicks']}")
                print(f"   ⏱️ Время обработки: {result['data']['processing_time']:.2f} сек")
                print(f"   🏆 Оценка: {result['data']['score']:.2f}")
                print(f"   💾 Сохранено в videos/: {result['data']['in_top_30']}")
                print(f"   📁 Путь к файлу: {result['data']['saved_video_path']}")
                print(f"   💬 Сообщение: {result['data']['message']}")
            else:
                print(f"❌ Ошибка: {response.status_code}")
                print(f"📄 Ответ: {response.text}")
                
    except Exception as e:
        print(f"❌ Ошибка при загрузке: {e}")

def test_phone_video_upload_with_metadata():
    """Имитирует загрузку видео с дополнительными метаданными."""
    print("\n📱 ИМИТАЦИЯ ЗАГРУЗКИ С МЕТАДАННЫМИ")
    print("=" * 50)
    
    video_file_path = Path("videos/juggling2.mp4")
    
    if not video_file_path.exists():
        print(f"❌ Файл не найден: {video_file_path}")
        return
    
    try:
        with open(video_file_path, 'rb') as video_file:
            # Имитируем данные с телефона
            data = {
                'device_id': 'android_phone_123',
                'user_id': 'test_user',
                'video_duration': '15.5',
                'video_quality': 'HD',
                'timestamp': '2025-07-27T17:50:00'
            }
            
            files = {
                'video': (video_file_path.name, video_file, 'video/mp4')
            }
            
            print("🚀 Отправляем POST запрос с метаданными...")
            response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data)
            
            print(f"📡 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Успешная загрузка с метаданными!")
                print(f"📊 Результат анализа:")
                print(f"   🥾 Набиваний: {result['data']['total_kicks']}")
                print(f"   📱 Устройство: {data.get('device_id', 'N/A')}")
                print(f"   👤 Пользователь: {data.get('user_id', 'N/A')}")
                print(f"   ⏱️ Время обработки: {result['data']['processing_time']:.2f} сек")
                print(f"   🏆 Оценка: {result['data']['score']:.2f}")
            else:
                print(f"❌ Ошибка: {response.status_code}")
                print(f"📄 Ответ: {response.text}")
                
    except Exception as e:
        print(f"❌ Ошибка при загрузке: {e}")

def main():
    """Основная функция тестирования."""
    print("🧪 ТЕСТИРОВАНИЕ ЗАГРУЗКИ ВИДЕО С ТЕЛЕФОНА")
    print("=" * 60)
    
    # Проверяем, что API сервер работает
    try:
        health_response = requests.get(f"{API_BASE_URL}/health")
        if health_response.status_code == 200:
            print("✅ API сервер работает")
        else:
            print("❌ API сервер не отвечает")
            return
    except Exception as e:
        print(f"❌ Не удается подключиться к API: {e}")
        print("💡 Убедитесь, что API сервер запущен: python api_server.py")
        return
    
    # Тестируем обычную загрузку
    test_phone_video_upload()
    
    # Тестируем загрузку с метаданными
    test_phone_video_upload_with_metadata()
    
    print("\n✅ Тестирование завершено!")
    print("📱 Теперь можно тестировать с реальным Android приложением")

if __name__ == "__main__":
    main() 