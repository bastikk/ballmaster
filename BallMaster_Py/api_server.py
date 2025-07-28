#!/usr/bin/env python3
"""
Flask API сервер для обработки видеофайлов от пользователей.
"""

import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

from top_results import top_results
from utils import analyze_video

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

app = Flask(__name__)

# Конфигурация
UPLOAD_FOLDER = Path('uploads')
VIDEOS_FOLDER = Path('videos')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Создаем папки
UPLOAD_FOLDER.mkdir(exist_ok=True)
VIDEOS_FOLDER.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


class FileProcessor:
    """Класс для обработки загруженных файлов."""
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Проверяет, разрешен ли тип файла."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    @staticmethod
    def save_uploaded_file(file) -> Optional[Path]:
        """Сохраняет загруженный файл во временную папку."""
        try:
            if file and file.filename:
                logging.info(f"Сохранение файла: {file.filename}")
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"{timestamp}_{filename}"
                
                # Сохраняем во временную папку для обработки
                temp_file_path = UPLOAD_FOLDER / safe_filename
                logging.info(f"Временный путь: {temp_file_path.absolute()}")
                
                file.save(str(temp_file_path))
                logging.info(f"Файл сохранен во временную папку: {temp_file_path}")
                logging.info(f"Размер файла: {temp_file_path.stat().st_size} байт")
                
                return temp_file_path
            else:
                logging.error("Файл или имя файла отсутствует")
        except Exception as e:
            logging.error(f"Ошибка сохранения файла: {e}")
            logging.error(traceback.format_exc())
        return None
    
    @staticmethod
    def save_to_videos_folder(temp_file_path: Path, video_name: str) -> Optional[Path]:
        """Сохраняет файл в папку videos/ если результат попал в топ-30."""
        try:
            videos_file_path = VIDEOS_FOLDER / video_name
            import shutil
            shutil.copy2(str(temp_file_path), str(videos_file_path))
            logging.info(f"Файл сохранен в videos/ (попал в топ-30): {videos_file_path}")
            return videos_file_path
        except Exception as e:
            logging.error(f"Ошибка сохранения файла в videos/: {e}")
            logging.error(traceback.format_exc())
        return None

    @staticmethod
    def cleanup_old_videos():
        """Удаляет видео из папки videos/, которые больше не в топ-30."""
        try:
            # Получаем список файлов в папке videos/
            if not VIDEOS_FOLDER.exists():
                return
            
            # Получаем список видео в топ-30
            top_30_results = top_results.get_top_results()
            top_30_video_names = {r.video_name for r in top_30_results}
            
            # Проверяем каждый файл в папке videos/
            for video_file in VIDEOS_FOLDER.glob('*.mp4'):
                if video_file.name not in top_30_video_names:
                    logging.info(f"Удаляем видео не из топ-30: {video_file.name}")
                    video_file.unlink()
                    logging.info(f"Видео удалено: {video_file.name}")
                    
        except Exception as e:
            logging.error(f"Ошибка очистки старых видео: {e}")
            logging.error(traceback.format_exc())

    @staticmethod
    def cleanup_file(file_path: Path) -> bool:
        """Удаляет файл после обработки."""
        try:
            logging.info(f"Попытка удаления файла: {file_path}")
            if file_path.exists():
                file_path.unlink()
                logging.info(f"Файл успешно удален: {file_path}")
                return True
            else:
                logging.warning(f"Файл не существует для удаления: {file_path}")
        except Exception as e:
            logging.error(f"Ошибка удаления файла {file_path}: {e}")
            logging.error(traceback.format_exc())
        return False


class VideoAnalyzer:
    """Класс для анализа видео."""
    
    @staticmethod
    def analyze_video_file(file_path: Path) -> Dict[str, Any]:
        """Анализирует видеофайл и возвращает результат."""
        try:
            logging.info(f"Начинаю анализ файла: {file_path}")
            logging.info(f"Размер файла: {file_path.stat().st_size} байт")
            logging.info(f"Файл существует: {file_path.exists()}")
            
            # Анализируем видео
            analyze_video(file_path)
            
            # Получаем ВСЕ результаты и находим результат текущего анализа
            all_results = top_results.get_top_results()
            current_result = None
            
            # Ищем результат с именем текущего файла и самым свежим timestamp
            for result in all_results:
                if result.video_name == file_path.name:
                    if current_result is None or result.timestamp > current_result.timestamp:
                        current_result = result
            
            if current_result:
                
                # Проверяем, попал ли результат в топ-30
                is_in_top_30 = any(r.video_name == current_result.video_name for r in all_results)
                
                saved_video_path = None
                message = "Видео успешно обработано"
                
                if is_in_top_30:
                    # Сохраняем файл в videos/ только если попал в топ-30
                    saved_video_path = FileProcessor.save_to_videos_folder(file_path, current_result.video_name)
                    if saved_video_path:
                        message = "Видео успешно обработано и сохранено (попал в топ-30)"
                    else:
                        message = "Видео успешно обработано (попал в топ-30, но ошибка сохранения)"
                    
                    # Очищаем старые видео, которые больше не в топ-30
                    FileProcessor.cleanup_old_videos()
                else:
                    message = "Видео обработано, но не попал в топ-30"
                
                return {
                    "success": True,
                    "data": {
                        "video_name": current_result.video_name,
                        "total_kicks": current_result.total_kicks,
                        "total_series": current_result.total_series,
                        "best_series_kicks": current_result.best_series_kicks,
                        "best_series_duration": current_result.best_series_duration,
                        "processing_time": current_result.processing_time,
                        "score": current_result.score,
                        "timestamp": current_result.timestamp,
                        "saved_video_path": str(saved_video_path) if saved_video_path else None,
                        "in_top_30": is_in_top_30,
                        "message": message
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Результат не был добавлен в топ-30"
                }
                
        except Exception as e:
            logging.error(f"Ошибка анализа видео {file_path}: {e}")
            logging.error(traceback.format_exc())
            return {
                "success": False,
                "error": f"Ошибка обработки видео: {str(e)}"
            }


class ResponseFormatter:
    """Класс для форматирования ответов API."""
    
    @staticmethod
    def success_response(data: Dict[str, Any], message: str = "Success") -> Dict[str, Any]:
        """Форматирует успешный ответ."""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def error_response(error: str, status_code: int = 400) -> tuple:
        """Форматирует ответ с ошибкой."""
        response = {
            "success": False,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        return jsonify(response), status_code


@app.route('/health', methods=['GET'])
def health_check():
    """Проверка состояния сервера."""
    return ResponseFormatter.success_response(
        {"status": "healthy", "uptime": datetime.now().isoformat()},
        "Server is running"
    )


@app.route('/upload', methods=['POST'])
def upload_video():
    """Эндпоинт для загрузки и обработки видео."""
    try:
        # Проверяем наличие файла
        if 'video' not in request.files:
            return ResponseFormatter.error_response("Файл не найден в запросе", 400)
        
        file = request.files['video']
        if file.filename == '':
            return ResponseFormatter.error_response("Файл не выбран", 400)
        
        # Проверяем тип файла
        if not FileProcessor.allowed_file(file.filename):
            return ResponseFormatter.error_response(
                f"Неподдерживаемый тип файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}", 
                400
            )
        
        # Сохраняем файл
        file_path = FileProcessor.save_uploaded_file(file)
        if not file_path:
            return ResponseFormatter.error_response("Ошибка сохранения файла", 500)
        
        try:
            logging.info("=" * 50)
            logging.info("НАЧАЛО ОБРАБОТКИ ЗАГРУЖЕННОГО ВИДЕО")
            logging.info(f"Загруженный файл: {file_path}")
            logging.info(f"Имя файла: {file_path.name}")
            logging.info(f"Файл существует: {file_path.exists()}")
            logging.info(f"Размер файла: {file_path.stat().st_size if file_path.exists() else 'N/A'} байт")
            logging.info("=" * 50)
            
            # Анализируем видео
            analysis_result = VideoAnalyzer.analyze_video_file(file_path)
            
            if analysis_result["success"]:
                return ResponseFormatter.success_response(
                    analysis_result["data"],
                    analysis_result["data"]["message"]
                )
            else:
                return ResponseFormatter.error_response(analysis_result["error"], 500)
                
        finally:
            # Удаляем файл после обработки
            FileProcessor.cleanup_file(file_path)
    
    except Exception as e:
        logging.error(f"Ошибка в upload_video: {e}")
        logging.error(traceback.format_exc())
        return ResponseFormatter.error_response(f"Внутренняя ошибка сервера: {str(e)}", 500)


@app.route('/results', methods=['GET'])
def get_results():
    """Эндпоинт для получения топ результатов."""
    try:
        limit = request.args.get('limit', type=int)
        if limit and (limit < 1 or limit > 30):
            return ResponseFormatter.error_response("Лимит должен быть от 1 до 30", 400)
        
        results = top_results.get_top_results(limit)
        results_data = []
        
        for result in results:
            results_data.append({
                "video_name": result.video_name,
                "total_kicks": result.total_kicks,
                "total_series": result.total_series,
                "best_series_kicks": result.best_series_kicks,
                "best_series_duration": result.best_series_duration,
                "processing_time": result.processing_time,
                "score": result.score,
                "timestamp": result.timestamp
            })
        
        return ResponseFormatter.success_response({
            "total_results": len(results_data),
            "results": results_data
        }, f"Получено {len(results_data)} результатов")
    
    except Exception as e:
        logging.error(f"Ошибка в get_results: {e}")
        return ResponseFormatter.error_response(f"Ошибка получения результатов: {str(e)}", 500)


@app.route('/export', methods=['GET'])
def export_results():
    """Эндпоинт для экспорта всех результатов."""
    try:
        export_data = top_results.get_results_for_export()
        return ResponseFormatter.success_response(export_data, "Результаты экспортированы")
    
    except Exception as e:
        logging.error(f"Ошибка в export_results: {e}")
        return ResponseFormatter.error_response(f"Ошибка экспорта: {str(e)}", 500)


@app.route('/stats', methods=['GET'])
def get_stats():
    """Эндпоинт для получения статистики."""
    try:
        results = top_results.get_top_results()
        
        if not results:
            return ResponseFormatter.success_response({
                "total_results": 0,
                "average_score": 0,
                "max_score": 0,
                "min_score": 0
            }, "Нет сохраненных результатов")
        
        scores = [r.score for r in results]
        kicks = [r.total_kicks for r in results]
        
        stats = {
            "total_results": len(results),
            "average_score": round(sum(scores) / len(scores), 2),
            "max_score": max(scores),
            "min_score": min(scores),
            "average_kicks": round(sum(kicks) / len(kicks), 2),
            "max_kicks": max(kicks),
            "last_update": results[0].timestamp if results else None
        }
        
        return ResponseFormatter.success_response(stats, "Статистика получена")
    
    except Exception as e:
        logging.error(f"Ошибка в get_stats: {e}")
        return ResponseFormatter.error_response(f"Ошибка получения статистики: {str(e)}", 500)


@app.route('/videos', methods=['GET'])
def get_saved_videos():
    """Эндпоинт для получения списка сохраненных видео из топ-30."""
    try:
        video_files = []
        
        if VIDEOS_FOLDER.exists():
            for video_file in VIDEOS_FOLDER.glob('*.mp4'):
                video_files.append({
                    "filename": video_file.name,
                    "size_bytes": video_file.stat().st_size,
                    "size_mb": round(video_file.stat().st_size / (1024 * 1024), 2),
                    "created": datetime.fromtimestamp(video_file.stat().st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(video_file.stat().st_mtime).isoformat()
                })
            
            # Сортируем по дате создания (новые сначала)
            video_files.sort(key=lambda x: x["created"], reverse=True)
        
        return ResponseFormatter.success_response({
            "total_videos": len(video_files),
            "videos": video_files,
            "note": "Показаны только видео из топ-30 результатов"
        }, f"Найдено {len(video_files)} видео из топ-30")
    
    except Exception as e:
        logging.error(f"Ошибка в get_saved_videos: {e}")
        return ResponseFormatter.error_response(f"Ошибка получения списка видео: {str(e)}", 500)


if __name__ == '__main__':
    logging.info("Запуск Flask API сервера...")
    logging.info(f"Папка загрузок: {UPLOAD_FOLDER.absolute()}")
    logging.info(f"Папка сохранения видео: {VIDEOS_FOLDER.absolute()}")
    logging.info(f"Максимальный размер файла: {MAX_FILE_SIZE / (1024*1024):.1f}MB")
    logging.info(f"Разрешенные форматы: {', '.join(ALLOWED_EXTENSIONS)}")
    
    app.run(host='0.0.0.0', port=5000, debug=False) 