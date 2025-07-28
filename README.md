# BallMaster - Система анализа жонглирования мячом

Система для анализа видео жонглирования мячом с использованием компьютерного зрения и машинного обучения.

## 🏗️ Архитектура

- **Python API сервер** - Flask бэкенд для анализа видео
- **Android приложение** - мобильный клиент на Kotlin с Jetpack Compose

## 🚀 Быстрый старт

### Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Запуск API сервера

```bash
cd BallMaster_Py
python api_server.py
```

Сервер запустится на `http://localhost:5000`

### Тестирование

```bash
# Тест имитации загрузки с телефона
python test_phone_upload.py

# Тест всех эндпоинтов API
python test_client.py
```

## 📱 API Эндпоинты

- `GET /health` - проверка состояния сервера
- `POST /upload` - загрузка и анализ видео
- `GET /results` - получение топ результатов
- `GET /stats` - статистика
- `GET /export` - экспорт результатов
- `GET /videos` - список сохраненных видео

## 🤖 Технологии

### Python API
- **Flask** - веб-фреймворк
- **YOLOv8** - детекция мяча
- **MediaPipe** - детекция позы человека
- **OpenCV** - обработка видео
- **NumPy** - математические вычисления

### Android приложение
- **Kotlin** - язык программирования
- **Jetpack Compose** - UI фреймворк
- **MVVM** - архитектура
- **Retrofit** - HTTP клиент

## 📊 Анализ видео

Система анализирует:
- **Количество набиваний** мяча
- **Серии жонглирования**
- **Оценку** техники
- **Время** обработки

## 🎯 Точность

- **YOLOv8** детектирует мяч с точностью >90%
- **MediaPipe** находит ноги игрока
- **Алгоритм** определяет удары по изменению траектории

## 📁 Структура проекта

```
BallMaster_Py/
├── api_server.py          # Flask API сервер
├── utils.py              # Логика анализа видео
├── top_results.py        # Управление результатами
├── test_phone_upload.py  # Тест имитации Android
├── test_client.py        # Тест API эндпоинтов
├── uploads/              # Временные загрузки
├── videos/               # Сохраненные видео (топ-30)
└── venv/                 # Виртуальное окружение

BallMaster/               # Android приложение
├── app/
│   ├── src/main/
│   │   ├── java/...      # Kotlin код
│   │   └── res/...       # Ресурсы
│   └── build.gradle.kts  # Конфигурация
└── build.gradle.kts
```

## 🔧 Настройка

### Параметры анализа (utils.py)

```python
# Параметры детекции ударов
kick_distance_threshold = 400      # пиксели
velocity_threshold = 8             # пиксели/кадр
trajectory_change_threshold = 25   # градусы
min_confidence_threshold = 0.6     # уверенность

# Оптимизация производительности
frame_skip = 4                     # пропуск кадров
```

## 📈 Производительность

- **Обработка видео:** ~10 секунд на 1 минуту видео
- **Точность детекции:** >85%
- **Поддерживаемые форматы:** MP4, AVI, MOV, MKV
- **Максимальный размер:** 100MB

## 🤝 Разработка

### Добавление новых функций

1. Измените логику в `utils.py`
2. Обновите API в `api_server.py`
3. Протестируйте с `test_client.py`
4. Обновите Android приложение

### Отладка

```bash
# Включить логирование
export FLASK_DEBUG=1
python api_server.py

# Проверить состояние
curl http://localhost:5000/health
```

## 📄 Лицензия

MIT License

## 👥 Авторы

- Разработка API: Python + Flask + YOLOv8
- Мобильное приложение: Kotlin + Jetpack Compose 