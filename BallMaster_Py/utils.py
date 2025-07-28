from pathlib import Path
import logging
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from ultralytics import YOLO
import mediapipe as mp
from scipy.spatial.distance import euclidean
from scipy.signal import find_peaks
import math
import time
from datetime import datetime


@dataclass
class BallKick:
    """Информация об ударе мяча."""
    frame_number: int
    timestamp: float
    ball_position: Tuple[float, float]
    kick_type: str  # "up" - подъем, "ground" - касание земли
    confidence: float


@dataclass
class JugglingSeries:
    """Серия жонглирования от подъема до касания земли."""
    start_frame: int
    end_frame: int
    kicks_count: int
    duration: float


@dataclass
class VideoAnalysis:
    """Результат анализа видео."""
    video_name: str
    total_kicks: int
    total_series: int
    kicks: List[BallKick]
    series: List[JugglingSeries]
    fps: float
    duration: float
    summary: str
    processing_time: float
    timestamp: str


class BallKickAnalyzer:
    """Класс для анализа ударов мяча с помощью YOLOv8 и MediaPipe."""

    def __init__(self):
        # Инициализация YOLOv8 для детекции мяча
        self.ball_model = YOLO('yolov8n.pt')  # Загружаем базовую модель

        # Инициализация MediaPipe для детекции позы
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Параметры для детекции ударов - очень строгие условия для точности
        self.kick_distance_threshold = 400  # пиксели - уменьшен для более точной детекции
        self.velocity_threshold = 8  # пиксели/кадр - увеличен для фильтрации шума
        self.min_kick_interval = 8  # кадров между ударами - увеличен интервал
        self.ground_threshold = 0.85  # доля высоты кадра для определения земли (85% снизу)
        self.trajectory_change_threshold = 25  # градусы - значительно увеличен порог изменения траектории
        self.velocity_history_size = 5  # количество кадров для анализа траектории
        self.min_confidence_threshold = 0.6  # значительно увеличен минимальный порог уверенности

        # История позиций и скоростей мяча
        self.ball_history: List[Tuple[float, float]] = []
        self.velocity_history: List[Tuple[float, float]] = []
        self.kicks: List[BallKick] = []
        self.current_series_kicks = 0
        self.in_juggling_series = False
        
        # Параметры оптимизации производительности
        self.frame_skip = 4  # обрабатываем каждый 2-й кадр для ускорения
        self.last_ball_position = None  # последняя позиция мяча для пропуска кадров
        self.ball_movement_threshold = 10  # минимальное движение мяча для обработки

    def detect_ball(self, frame: np.ndarray) -> Optional[Tuple[float, float, float]]:
        """Детектирует мяч на кадре и возвращает (x, y, confidence)."""
        results = self.ball_model(frame, classes=[32])  # class 32 = sports ball

        if results[0].boxes is not None and len(results[0].boxes) > 0:
            # Берем мяч с наибольшей уверенностью
            boxes = results[0].boxes
            confidences = boxes.conf.cpu().numpy()
            best_idx = np.argmax(confidences)

            if confidences[best_idx] > 0.3:  # Минимальная уверенность
                box = boxes.xyxy[best_idx].cpu().numpy()
                x = (box[0] + box[2]) / 2  # центр по X
                y = (box[1] + box[3]) / 2  # центр по Y
                return (x, y, confidences[best_idx])

        return None

    def detect_feet(self, frame: np.ndarray) -> List[Tuple[float, float]]:
        """Детектирует позиции ног с помощью MediaPipe."""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)

        feet_positions = []
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Левый и правый носок (landmarks 31 и 32)
            left_foot = landmarks[31]
            right_foot = landmarks[32]

            h, w, _ = frame.shape

            if left_foot.visibility > 0.5:
                feet_positions.append((left_foot.x * w, left_foot.y * h))
            if right_foot.visibility > 0.5:
                feet_positions.append((right_foot.x * w, right_foot.y * h))

        return feet_positions

    def calculate_ball_velocity(self) -> Tuple[float, float]:
        """Вычисляет скорость мяча по X и Y на основе истории позиций."""
        if len(self.ball_history) < 2:
            return (0.0, 0.0)

        # Берем последние 2 позиции
        pos1 = self.ball_history[-2]
        pos2 = self.ball_history[-1]

        velocity_x = pos2[0] - pos1[0]
        velocity_y = pos2[1] - pos1[1]  # Положительная = движение вниз

        return (velocity_x, velocity_y)

    def calculate_trajectory_change(self) -> float:
        """Вычисляет изменение траектории мяча в градусах."""
        if len(self.velocity_history) < 3:
            return 0.0

        # Берем последние 3 вектора скорости
        v1 = self.velocity_history[-3]
        v2 = self.velocity_history[-2]
        v3 = self.velocity_history[-1]

        # Вычисляем углы между векторами
        angle1 = math.degrees(math.atan2(v2[1], v2[0]))
        angle2 = math.degrees(math.atan2(v3[1], v3[0]))

        # Вычисляем изменение угла
        angle_change = abs(angle2 - angle1)
        if angle_change > 180:
            angle_change = 360 - angle_change

        return angle_change

    def is_ball_near_ground(self, ball_pos: Tuple[float, float], frame_height: int) -> bool:
        """Проверяет, находится ли мяч близко к земле."""
        ground_y = frame_height * self.ground_threshold
        return ball_pos[1] >= ground_y

    def detect_kick(self, ball_pos: Tuple[float, float], feet_positions: List[Tuple[float, float]],
                    frame_number: int, timestamp: float, frame_height: int) -> Optional[BallKick]:
        """Детектирует удар на основе близости мяча к ногам и направления движения."""

        # Проверяем близость мяча к ногам
        min_distance = float('inf')
        closest_foot = None

        for foot_pos in feet_positions:
            distance = euclidean(ball_pos, foot_pos)
            if distance < min_distance:
                min_distance = distance
                closest_foot = foot_pos

        # Если мяч близко к ноге или есть значительное движение
        if (min_distance < self.kick_distance_threshold and closest_foot) or len(feet_positions) > 0:
            # Проверяем изменение скорости мяча
            velocity_x, velocity_y = self.calculate_ball_velocity()

            # Проверяем, что это не повторный удар
            if self.kicks and frame_number - self.kicks[-1].frame_number < self.min_kick_interval:
                return None

            # Определяем тип удара - более строгие условия
            trajectory_change = self.calculate_trajectory_change()

            # Отладочная информация
            if len(self.velocity_history) >= 3:
                logging.info(f"Кадр {frame_number}: траектория {trajectory_change:.1f}°, "
                             f"скорость Y: {velocity_y:.1f}, расстояние до ног: {min_distance:.1f}, "
                             f"пороги: траектория>{self.trajectory_change_threshold}, "
                             f"скорость>{self.velocity_threshold}, расстояние<{self.kick_distance_threshold}")

            # Проверяем значительное изменение траектории и движение вверх
            # Расстояние до ног используется как дополнительный фактор, но не блокирующий
            if (trajectory_change > self.trajectory_change_threshold and
                    abs(velocity_y) > self.velocity_threshold and
                    velocity_y < 0):  # Мяч должен двигаться вверх (отрицательная скорость Y)

                # Если мяч близко к ногам, увеличиваем уверенность
                distance_bonus = 1.0 if min_distance < self.kick_distance_threshold else 0.7

                # Это набивание - мяч изменил траекторию и был близко к ногам
                if not self.in_juggling_series:
                    self.in_juggling_series = True
                    self.current_series_kicks = 0

                self.current_series_kicks += 1

                # Более точный расчет уверенности
                trajectory_score = min(1.0, trajectory_change / 45.0)  # Нормализуем изменение траектории
                velocity_score = min(1.0, abs(velocity_y) / 20.0)  # Нормализуем скорость
                distance_score = 1.0 if min_distance < self.kick_distance_threshold else 0.5

                confidence = (trajectory_score * 0.4 + velocity_score * 0.4 + distance_score * 0.2) * distance_bonus

                # Возвращаем удар только если уверенность выше порога
                if confidence >= self.min_confidence_threshold:
                    return BallKick(
                        frame_number=frame_number,
                        timestamp=timestamp,
                        ball_position=ball_pos,
                        kick_type="up",
                        confidence=confidence
                    )

                return None

        # Проверяем касание земли
        if self.is_ball_near_ground(ball_pos, frame_height) and self.in_juggling_series:
            self.in_juggling_series = False

            return BallKick(
                frame_number=frame_number,
                timestamp=timestamp,
                ball_position=ball_pos,
                kick_type="ground",
                confidence=0.9
            )

        return None

    def analyze_video(self, video_path: Path) -> VideoAnalysis:
        """Анализирует видео и подсчитывает удары мяча."""
        import time
        start_time = time.time()
        logging.info(f"Начинаю анализ видео: {video_path.name}")

        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0  # значение по умолчанию
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logging.info(f"FPS: {fps}, Длительность: {duration:.2f} сек, Высота: {frame_height}")

        frame_number = 0
        self.ball_history = []
        self.velocity_history = []
        self.kicks = []
        self.current_series_kicks = 0
        self.in_juggling_series = False

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = frame_number / fps
            
            # Оптимизация: пропускаем каждый N-й кадр для ускорения
            if frame_number % self.frame_skip != 0:
                frame_number += 1
                continue

            # Детектируем мяч
            ball_detection = self.detect_ball(frame)
            
            # Оптимизация: если мяч не найден, пропускаем обработку
            if not ball_detection:
                frame_number += 1
                continue
            if ball_detection:
                ball_pos = (ball_detection[0], ball_detection[1])
                
                # Оптимизация: пропускаем кадры с медленным движением мяча
                if self.last_ball_position:
                    movement = ((ball_pos[0] - self.last_ball_position[0])**2 + 
                               (ball_pos[1] - self.last_ball_position[1])**2)**0.5
                    if movement < self.ball_movement_threshold:
                        frame_number += 1
                        continue
                
                self.last_ball_position = ball_pos
                self.ball_history.append(ball_pos)

                # Ограничиваем историю последними 10 позициями
                if len(self.ball_history) > 10:
                    self.ball_history.pop(0)

                # Вычисляем и сохраняем скорость
                velocity = self.calculate_ball_velocity()
                self.velocity_history.append(velocity)

                # Ограничиваем историю скоростей
                if len(self.velocity_history) > self.velocity_history_size:
                    self.velocity_history.pop(0)

                # Детектируем ноги
                feet_positions = self.detect_feet(frame)

                # Проверяем на удар только если есть достаточно истории для анализа траектории
                if len(self.velocity_history) >= 3:
                    kick = self.detect_kick(ball_pos, feet_positions, frame_number, timestamp, frame_height)
                    if kick:
                        self.kicks.append(kick)
                        if kick.kick_type == "up":
                            logging.info(f"Набивание на кадре {frame_number} (время: {timestamp:.2f}с, "
                                         f"уверенность: {kick.confidence:.2f})")
                        else:
                            logging.info(f"Касание земли на кадре {frame_number} (время: {timestamp:.2f}с)")

            frame_number += 1

            # Показываем прогресс
            if frame_number % 30 == 0:
                progress = (frame_number / total_frames) * 100
                logging.info(f"Прогресс: {progress:.1f}%")

        cap.release()

        # Анализируем серии жонглирования
        series = self._analyze_juggling_series()

        # Создаем итоговый анализ
        total_kicks = len([k for k in self.kicks if k.kick_type == "up"])
        summary = f"Обнаружено {total_kicks} набиваний в {len(series)} сериях за {duration:.1f} секунд"
        
        # Измеряем время выполнения
        end_time = time.time()
        processing_time = end_time - start_time
        logging.info(f"Время обработки: {processing_time:.2f} секунд")

        return VideoAnalysis(
            video_name=video_path.name,
            total_kicks=total_kicks,
            total_series=len(series),
            kicks=self.kicks,
            series=series,
            fps=fps,
            duration=duration,
            summary=summary,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )

    def _analyze_juggling_series(self) -> List[JugglingSeries]:
        """Анализирует серии жонглирования."""
        series = []
        current_series_start = None
        current_kicks = 0
        current_series_start_timestamp = None

        for kick in self.kicks:
            if kick.kick_type == "up":
                if current_series_start is None:
                    current_series_start = kick.frame_number
                    current_series_start_timestamp = kick.timestamp
                current_kicks += 1
            elif kick.kick_type == "ground" and current_series_start is not None:
                # Завершаем серию
                duration = kick.timestamp - current_series_start_timestamp
                series.append(JugglingSeries(
                    start_frame=current_series_start,
                    end_frame=kick.frame_number,
                    kicks_count=current_kicks,
                    duration=duration
                ))
                current_series_start = None
                current_kicks = 0
                current_series_start_timestamp = None

        return series


def analyze_video(video_path: Path) -> None:
    """Анализирует видеофайл и подсчитывает удары мяча."""
    logging.info(f"=== НАЧАЛО АНАЛИЗА ВИДЕО ===")
    logging.info(f"Путь к файлу: {video_path}")
    logging.info(f"Абсолютный путь: {video_path.absolute()}")
    logging.info(f"Файл существует: {video_path.exists()}")
    logging.info(f"Размер файла: {video_path.stat().st_size if video_path.exists() else 'N/A'} байт")
    
    analyzer = BallKickAnalyzer()
    analysis_result = analyzer.analyze_video(video_path)

    logging.info(f"=== Анализ видео: {analysis_result.video_name} ===")
    logging.info(f"FPS: {analysis_result.fps:.2f}")
    logging.info(f"Длительность: {analysis_result.duration:.2f} сек")
    logging.info(f"Всего набиваний: {analysis_result.total_kicks}")
    logging.info(f"Количество серий: {analysis_result.total_series}")
    logging.info(f"Резюме: {analysis_result.summary}")

    if analysis_result.series:
        logging.info("Детали серий жонглирования:")
        for i, series in enumerate(analysis_result.series, 1):
            logging.info(f"  Серия {i}: {series.kicks_count} набиваний за {series.duration:.2f}с "
                         f"(кадры {series.start_frame}-{series.end_frame})")

    if analysis_result.kicks:
        logging.info("Детали ударов:")
        for i, kick in enumerate(analysis_result.kicks, 1):
            kick_type_str = "подъем" if kick.kick_type == "up" else "земля"
            logging.info(f"  {i}. {kick_type_str}: кадр {kick.frame_number}, "
                         f"время {kick.timestamp:.2f}с, уверенность {kick.confidence:.2f}")

    # Добавляем результат в топ-30
    from top_results import top_results
    
    best_series_kicks = max([s.kicks_count for s in analysis_result.series]) if analysis_result.series else 0
    best_series_duration = max([s.duration for s in analysis_result.series]) if analysis_result.series else 0
    
    added = top_results.add_result(
        video_name=analysis_result.video_name,
        total_kicks=analysis_result.total_kicks,
        total_series=analysis_result.total_series,
        best_series_kicks=best_series_kicks,
        best_series_duration=best_series_duration,
        processing_time=analysis_result.processing_time
    )
    
    if added:
        logging.info("Результат добавлен в топ-30")
    else:
        logging.info("Результат не попал в топ-30")



